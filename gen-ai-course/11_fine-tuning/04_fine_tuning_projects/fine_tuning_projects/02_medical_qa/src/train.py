"""
Medical Q&A - LoRA Fine-Tuning Training Script

Architecture:
  Base model  : microsoft/BioGPT-Large (or any CausalLM)
  PEFT method : LoRA (Low-Rank Adaptation) via `peft`
  Trainer     : Hugging Face `transformers.Trainer` + `accelerate`
  Precision   : fp16 on CUDA, fp32 on CPU (auto-detected)

Usage:
  python src/train.py                         # use defaults from config
  python src/train.py --config configs/training_config.yaml
"""

from __future__ import annotations

import argparse
import logging
import os
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import torch
import yaml
from datasets import DatasetDict, load_from_disk
from peft import LoraConfig, TaskType, get_peft_model, prepare_model_for_kbit_training
from transformers import (
    AutoModelForCausalLM,
    AutoTokenizer,
    DataCollatorForSeq2Seq,
    EarlyStoppingCallback,
    Trainer,
    TrainingArguments,
    set_seed,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


# ── Configuration ─────────────────────────────────────────────────────────────

@dataclass
class TrainConfig:
    # Model
    base_model: str = "microsoft/BioGPT-Large"
    trust_remote_code: bool = True

    # LoRA
    lora_r: int = 16
    lora_alpha: int = 32
    lora_target_modules: list = field(default_factory=lambda: ["q_proj", "v_proj"])
    lora_dropout: float = 0.05

    # Data
    processed_dir: str = "data/processed"
    output_dir: str = "models/medical_qa_lora"

    # Training hyper-parameters
    num_train_epochs: int = 3
    per_device_train_batch_size: int = 2
    per_device_eval_batch_size: int = 2
    gradient_accumulation_steps: int = 8
    learning_rate: float = 2e-4
    lr_scheduler_type: str = "cosine"
    warmup_ratio: float = 0.05
    weight_decay: float = 0.01
    max_grad_norm: float = 1.0
    gradient_checkpointing: bool = True
    fp16: bool = False
    bf16: bool = False
    logging_steps: int = 50
    save_total_limit: int = 2
    seed: int = 42
    dataloader_num_workers: int = 0


def load_config_from_yaml(path: str) -> TrainConfig:
    """Override TrainConfig defaults from a YAML file."""
    with open(path) as f:
        raw = yaml.safe_load(f)

    cfg = TrainConfig()

    model_cfg = raw.get("model", {})
    cfg.base_model = model_cfg.get("base_model", cfg.base_model)
    cfg.trust_remote_code = model_cfg.get("trust_remote_code", cfg.trust_remote_code)

    lora_cfg = raw.get("lora", {})
    cfg.lora_r = lora_cfg.get("r", cfg.lora_r)
    cfg.lora_alpha = lora_cfg.get("lora_alpha", cfg.lora_alpha)
    cfg.lora_target_modules = lora_cfg.get("target_modules", cfg.lora_target_modules)
    cfg.lora_dropout = lora_cfg.get("lora_dropout", cfg.lora_dropout)

    ds_cfg = raw.get("dataset", {})
    cfg.processed_dir = ds_cfg.get("processed_dir", cfg.processed_dir)

    tr_cfg = raw.get("training", {})
    cfg.output_dir = tr_cfg.get("output_dir", cfg.output_dir)
    cfg.num_train_epochs = tr_cfg.get("num_train_epochs", cfg.num_train_epochs)
    cfg.per_device_train_batch_size = tr_cfg.get("per_device_train_batch_size", cfg.per_device_train_batch_size)
    cfg.per_device_eval_batch_size = tr_cfg.get("per_device_eval_batch_size", cfg.per_device_eval_batch_size)
    cfg.gradient_accumulation_steps = tr_cfg.get("gradient_accumulation_steps", cfg.gradient_accumulation_steps)
    cfg.learning_rate = tr_cfg.get("learning_rate", cfg.learning_rate)
    cfg.lr_scheduler_type = tr_cfg.get("lr_scheduler_type", cfg.lr_scheduler_type)
    cfg.warmup_ratio = tr_cfg.get("warmup_ratio", cfg.warmup_ratio)
    cfg.weight_decay = tr_cfg.get("weight_decay", cfg.weight_decay)
    cfg.max_grad_norm = tr_cfg.get("max_grad_norm", cfg.max_grad_norm)
    cfg.gradient_checkpointing = tr_cfg.get("gradient_checkpointing", cfg.gradient_checkpointing)
    cfg.fp16 = tr_cfg.get("fp16", cfg.fp16)
    cfg.bf16 = tr_cfg.get("bf16", cfg.bf16)
    cfg.logging_steps = tr_cfg.get("logging_steps", cfg.logging_steps)
    cfg.save_total_limit = tr_cfg.get("save_total_limit", cfg.save_total_limit)
    cfg.dataloader_num_workers = tr_cfg.get("dataloader_num_workers", cfg.dataloader_num_workers)
    return cfg


# ── Model builder ─────────────────────────────────────────────────────────────

def build_model_and_tokenizer(cfg: TrainConfig):
    """Load base model, apply LoRA, return (model, tokenizer)."""
    logger.info(f"Loading base model: {cfg.base_model}")

    device_map = "auto" if torch.cuda.is_available() else None
    torch_dtype = torch.float16 if (cfg.fp16 and torch.cuda.is_available()) else torch.float32

    model = AutoModelForCausalLM.from_pretrained(
        cfg.base_model,
        torch_dtype=torch_dtype,
        device_map=device_map,
        trust_remote_code=cfg.trust_remote_code,
    )

    tokenizer = AutoTokenizer.from_pretrained(
        cfg.base_model,
        trust_remote_code=cfg.trust_remote_code,
    )
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
        model.config.pad_token_id = tokenizer.eos_token_id

    if cfg.gradient_checkpointing:
        model = prepare_model_for_kbit_training(model)

    lora_config = LoraConfig(
        r=cfg.lora_r,
        lora_alpha=cfg.lora_alpha,
        target_modules=cfg.lora_target_modules,
        lora_dropout=cfg.lora_dropout,
        bias="none",
        task_type=TaskType.CAUSAL_LM,
    )
    model = get_peft_model(model, lora_config)
    model.print_trainable_parameters()

    return model, tokenizer


# ── Dataset loader ────────────────────────────────────────────────────────────

def load_datasets(cfg: TrainConfig) -> DatasetDict:
    processed_path = Path(cfg.processed_dir)
    if not processed_path.exists():
        raise FileNotFoundError(
            f"Processed data not found at '{processed_path}'. "
            "Run `python src/preprocess.py` first."
        )
    logger.info(f"Loading tokenised dataset from: {processed_path}")
    ds = load_from_disk(str(processed_path))
    logger.info(
        f"  train: {len(ds['train'])}, val: {len(ds['validation'])}, test: {len(ds['test'])}"
    )
    return ds


# ── Trainer builder ───────────────────────────────────────────────────────────

def build_trainer(cfg: TrainConfig, model, tokenizer, datasets: DatasetDict) -> Trainer:
    training_args = TrainingArguments(
        output_dir=cfg.output_dir,
        num_train_epochs=cfg.num_train_epochs,
        per_device_train_batch_size=cfg.per_device_train_batch_size,
        per_device_eval_batch_size=cfg.per_device_eval_batch_size,
        gradient_accumulation_steps=cfg.gradient_accumulation_steps,
        learning_rate=cfg.learning_rate,
        lr_scheduler_type=cfg.lr_scheduler_type,
        warmup_ratio=cfg.warmup_ratio,
        weight_decay=cfg.weight_decay,
        max_grad_norm=cfg.max_grad_norm,
        fp16=cfg.fp16,
        bf16=cfg.bf16,
        gradient_checkpointing=cfg.gradient_checkpointing,
        logging_dir=f"{cfg.output_dir}/logs",
        logging_steps=cfg.logging_steps,
        evaluation_strategy="epoch",
        save_strategy="epoch",
        load_best_model_at_end=True,
        metric_for_best_model="eval_loss",
        greater_is_better=False,
        save_total_limit=cfg.save_total_limit,
        report_to="none",
        dataloader_num_workers=cfg.dataloader_num_workers,
        remove_unused_columns=False,
    )

    data_collator = DataCollatorForSeq2Seq(
        tokenizer=tokenizer,
        model=model,
        label_pad_token_id=-100,
        pad_to_multiple_of=8,
    )

    return Trainer(
        model=model,
        args=training_args,
        train_dataset=datasets["train"],
        eval_dataset=datasets["validation"],
        tokenizer=tokenizer,
        data_collator=data_collator,
        callbacks=[EarlyStoppingCallback(early_stopping_patience=2)],
    )


# ── Checkpoint helpers ────────────────────────────────────────────────────────

def find_latest_checkpoint(output_dir: str) -> Optional[str]:
    out = Path(output_dir)
    checkpoints = sorted(out.glob("checkpoint-*"), key=lambda p: int(p.name.split("-")[1]))
    return str(checkpoints[-1]) if checkpoints else None


def save_final_model(trainer: Trainer, cfg: TrainConfig) -> None:
    final_path = Path(cfg.output_dir) / "final"
    trainer.save_model(str(final_path))
    trainer.tokenizer.save_pretrained(str(final_path))
    logger.info(f"Final model saved → {final_path}")


# ── Main ──────────────────────────────────────────────────────────────────────

def train(cfg: TrainConfig) -> None:
    set_seed(cfg.seed)
    logger.info("=== Medical Q&A Fine-Tuning ===")
    logger.info(f"  Base model : {cfg.base_model}")
    logger.info(f"  LoRA r     : {cfg.lora_r}")
    logger.info(f"  Epochs     : {cfg.num_train_epochs}")
    logger.info(f"  Device     : {'GPU' if torch.cuda.is_available() else 'CPU'}")

    model, tokenizer = build_model_and_tokenizer(cfg)
    datasets = load_datasets(cfg)
    trainer = build_trainer(cfg, model, tokenizer, datasets)

    resume_from = find_latest_checkpoint(cfg.output_dir)
    if resume_from:
        logger.info(f"Resuming from checkpoint: {resume_from}")

    try:
        trainer.train(resume_from_checkpoint=resume_from)
    except KeyboardInterrupt:
        logger.warning("Training interrupted — saving current state …")
        trainer.save_model(f"{cfg.output_dir}/interrupted")
        sys.exit(0)
    except Exception as exc:
        logger.error(f"Training failed: {exc}")
        trainer.save_model(f"{cfg.output_dir}/error_checkpoint")
        raise

    save_final_model(trainer, cfg)
    metrics = trainer.evaluate(datasets["test"])
    logger.info(f"Test metrics: {metrics}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Medical Q&A LoRA fine-tuning")
    parser.add_argument("--config", type=str, default=None,
                        help="Path to YAML config (configs/training_config.yaml)")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    cfg = load_config_from_yaml(args.config) if args.config else TrainConfig()
    train(cfg)


if __name__ == "__main__":
    main()

