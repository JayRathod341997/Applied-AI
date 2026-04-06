"""
Legal/Finance Model Trainer

Two-stage training pipeline:
1. Domain-specific pretraining with masked language modeling
2. Task-specific fine-tuning for summarization and Q&A

Environment: PyTorch 2.4, Transformers 4.46, Accelerate 0.30
"""

import os
import sys
import json
import logging
import argparse
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime

import torch
import numpy as np
from datasets import DatasetDict, load_from_disk
from transformers import (
    AutoModelForCausalLM,
    AutoModelForMaskedLM,
    AutoTokenizer,
    TrainingArguments,
    Trainer,
    DataCollatorForLanguageModeling,
    DataCollatorForSeq2Seq,
    EarlyStoppingCallback,
    set_seed,
    GenerationConfig,
)
from peft import (
    LoraConfig,
    get_peft_model,
    TaskType,
    PeftType,
)
from accelerate import Accelerator
import evaluate

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("logs/training.log"),
        logging.StreamHandler(),
    ],
)
logger = logging.getLogger(__name__)


@dataclass
class TrainingConfig:
    """Configuration for 2-stage training."""

    # Model
    base_model: str = "microsoft/finbert-tone"
    model_type: str = "causal_lm"  # or "masked_lm"
    output_dir: str = "experiments"

    # Data
    pretrain_data_path: str = "data/processed/pretrain_dataset"
    sft_data_path: str = "data/processed/sft_dataset"

    # Stage 1: Domain pretraining
    pretrain_epochs: int = 5
    pretrain_batch_size: int = 8
    pretrain_learning_rate: float = 3e-5
    pretrain_max_length: int = 512
    mlm_probability: float = 0.15

    # Stage 2: Task fine-tuning
    sft_epochs: int = 12
    sft_batch_size: int = 8
    sft_learning_rate: float = 3e-5
    sft_max_length: int = 512

    # LoRA configuration
    use_lora: bool = True
    lora_r: int = 16
    lora_alpha: int = 32
    lora_dropout: float = 0.05
    target_modules: List[str] = field(
        default_factory=lambda: ["q_proj", "v_proj", "k_proj", "o_proj"]
    )

    # Optimization
    gradient_checkpointing: bool = True
    use_flash_attention: bool = True
    bf16: bool = True
    tf32: bool = True
    warmup_ratio: float = 0.03
    weight_decay: float = 0.01
    max_grad_norm: float = 1.0

    # Generation (for inference)
    max_new_tokens: int = 150
    num_beams: int = 4
    length_penalty: float = 1.2

    # Evaluation
    eval_steps: int = 100
    save_steps: int = 200
    logging_steps: int = 50

    # System
    seed: int = 42
    dataloader_num_workers: int = 4


class LegalFinanceTrainer:
    """Two-stage trainer for legal-finance domain adaptation."""

    def __init__(self, config: TrainingConfig):
        self.config = config
        self.tokenizer: Optional[AutoTokenizer] = None
        self.model = None
        self.trainer: Optional[Trainer] = None
        self.accelerator: Optional[Accelerator] = None

    def setup_logging(self):
        """Setup logging to file."""
        log_dir = Path("logs")
        log_dir.mkdir(parents=True, exist_ok=True)

        file_handler = logging.FileHandler(
            log_dir / f"training_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        )
        file_handler.setFormatter(
            logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
        )
        logger.addHandler(file_handler)

    def set_seed(self):
        """Set random seed."""
        set_seed(self.config.seed)
        torch.manual_seed(self.config.seed)
        np.random.seed(self.config.seed)

    def load_tokenizer(self):
        """Load and configure tokenizer."""
        logger.info(f"Loading tokenizer: {self.config.base_model}")

        self.tokenizer = AutoTokenizer.from_pretrained(
            self.config.base_model,
            trust_remote_code=True,
        )

        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token

        self.tokenizer.padding_side = "right"

        logger.info("Tokenizer loaded successfully")

    def load_base_model(self, for_pretraining: bool = False):
        """Load base model."""
        logger.info(f"Loading base model: {self.config.base_model}")

        torch_dtype = torch.bfloat16 if self.config.bf16 else torch.float32

        if for_pretraining:
            # Masked LM for pretraining
            self.model = AutoModelForMaskedLM.from_pretrained(
                self.config.base_model,
                torch_dtype=torch_dtype,
                trust_remote_code=True,
                device_map="auto",
            )
        else:
            # Causal LM for fine-tuning
            self.model = AutoModelForCausalLM.from_pretrained(
                self.config.base_model,
                torch_dtype=torch_dtype,
                trust_remote_code=True,
                device_map="auto",
                attn_implementation="flash_attention_2"
                if self.config.use_flash_attention
                else "eager",
            )

        self.model.config.use_cache = not self.config.gradient_checkpointing

        if self.config.gradient_checkpointing:
            self.model.gradient_checkpointing_enable()

        logger.info("Model loaded successfully")

    def apply_lora(self):
        """Apply LoRA adapters."""
        if not self.config.use_lora:
            logger.info("LoRA disabled, using full fine-tuning")
            return

        logger.info("Applying LoRA adapters...")

        lora_config = LoraConfig(
            task_type=TaskType.CAUSAL_LM,
            r=self.config.lora_r,
            lora_alpha=self.config.lora_alpha,
            lora_dropout=self.config.lora_dropout,
            target_modules=self.config.target_modules,
            bias="none",
            inference_mode=False,
        )

        self.model = get_peft_model(self.model, lora_config)
        self.model.print_trainable_parameters()

        logger.info("LoRA adapters applied successfully")

    def load_dataset(self, data_path: str) -> DatasetDict:
        """Load preprocessed dataset."""
        logger.info(f"Loading dataset from: {data_path}")

        dataset = load_from_disk(data_path)

        if "train" not in dataset:
            raise ValueError(f"Invalid dataset format: {dataset}")

        logger.info(f"Dataset loaded: {len(dataset['train'])} train samples")

        return dataset

    def pretrain_tokenize(self, examples: Dict[str, Any]) -> Dict[str, List]:
        """Tokenize for MLM pretraining."""
        result = self.tokenizer(
            examples["text"],
            truncation=True,
            max_length=self.config.pretrain_max_length,
            padding="max_length",
            return_special_tokens_mask=True,
        )

        return result

    def sft_tokenize(self, examples: Dict[str, Any]) -> Dict[str, List]:
        """Tokenize for SFT (with label masking for prompt)."""
        full_texts = examples["text"]

        result = self.tokenizer(
            full_texts,
            truncation=True,
            max_length=self.config.sft_max_length,
            padding="max_length",
            return_tensors=None,
        )

        # Create labels with prompt masked
        prompt_end_indicators = ["### Response:"]

        labels = []
        for text, input_ids in zip(full_texts, result["input_ids"]):
            labels.append(list(input_ids))

            for indicator in prompt_end_indicators:
                prompt_end = text.find(indicator)
                if prompt_end != -1:
                    prompt_tokens = self.tokenizer(
                        text[: prompt_end + len(indicator)],
                        add_special_tokens=False,
                    )["input_ids"]

                    for i in range(min(len(prompt_tokens), len(labels[-1]))):
                        labels[-1][i] = -100
                    break

        # Mask padding tokens
        for i, input_ids in enumerate(result["input_ids"]):
            for j, token_id in enumerate(input_ids):
                if token_id == self.tokenizer.pad_token_id:
                    labels[i][j] = -100

        result["labels"] = labels
        return result

    def compute_metrics(self, eval_pred):
        """Compute evaluation metrics."""
        predictions, labels = eval_pred
        predictions = np.argmax(predictions, axis=-1)

        # Filter out -100 labels
        mask = labels != -100
        correct = np.sum(predictions[mask] == labels[mask])
        total = np.sum(mask)

        accuracy = correct / total if total > 0 else 0

        return {"accuracy": accuracy}

    def setup_trainer(
        self,
        dataset: DatasetDict,
        training_type: str = "sft",
    ) -> Trainer:
        """Setup Trainer with configuration."""

        if training_type == "pretrain":
            training_args = TrainingArguments(
                output_dir=str(Path(self.config.output_dir) / "pretrain"),
                num_train_epochs=self.config.pretrain_epochs,
                per_device_train_batch_size=self.config.pretrain_batch_size,
                per_device_eval_batch_size=self.config.pretrain_batch_size,
                learning_rate=self.config.pretrain_learning_rate,
                weight_decay=self.config.weight_decay,
                warmup_ratio=self.config.warmup_ratio,
                max_grad_norm=self.config.max_grad_norm,
                evaluation_strategy="steps",
                eval_steps=self.config.eval_steps,
                save_strategy="steps",
                save_steps=self.config.save_steps,
                save_total_limit=2,
                logging_dir=str(Path("logs") / "pretrain"),
                logging_steps=self.config.logging_steps,
                logging_first_step=True,
                load_best_model_at_end=True,
                metric_for_best_model="eval_loss",
                greater_is_better=False,
                bf16=self.config.bf16,
                fp16=not self.config.bf16,
                gradient_checkpointing=self.config.gradient_checkpointing,
                dataloader_num_workers=self.config.dataloader_num_workers,
                remove_unused_columns=False,
                report_to=["tensorboard"],
                optim="adamw_torch",
                lr_scheduler_type="cosine",
                seed=self.config.seed,
            )

            data_collator = DataCollatorForLanguageModeling(
                tokenizer=self.tokenizer,
                mlm=True,
                mlm_probability=self.config.mlm_probability,
            )

        else:  # sft
            training_args = TrainingArguments(
                output_dir=str(Path(self.config.output_dir) / "sft"),
                num_train_epochs=self.config.sft_epochs,
                per_device_train_batch_size=self.config.sft_batch_size,
                per_device_eval_batch_size=self.config.sft_batch_size,
                learning_rate=self.config.sft_learning_rate,
                weight_decay=self.config.weight_decay,
                warmup_ratio=self.config.warmup_ratio,
                max_grad_norm=self.config.max_grad_norm,
                evaluation_strategy="steps",
                eval_steps=self.config.eval_steps,
                save_strategy="steps",
                save_steps=self.config.save_steps,
                save_total_limit=2,
                logging_dir=str(Path("logs") / "sft"),
                logging_steps=self.config.logging_steps,
                logging_first_step=True,
                load_best_model_at_end=True,
                metric_for_best_model="eval_loss",
                greater_is_better=False,
                bf16=self.config.bf16,
                fp16=not self.config.bf16,
                gradient_checkpointing=self.config.gradient_checkpointing,
                dataloader_num_workers=self.config.dataloader_num_workers,
                remove_unused_columns=False,
                report_to=["tensorboard"],
                optim="adamw_torch",
                lr_scheduler_type="cosine",
                seed=self.config.seed,
                predict_with_generate=True,
            )

            data_collator = DataCollatorForSeq2Seq(
                tokenizer=self.tokenizer,
                model=self.model,
                padding=True,
                return_tensors="pt",
            )

        trainer = Trainer(
            model=self.model,
            args=training_args,
            train_dataset=dataset["train"],
            eval_dataset=dataset.get("validation", dataset["train"].select(range(100))),
            data_collator=data_collator,
            tokenizer=self.tokenizer,
            callbacks=[EarlyStoppingCallback(early_stopping_patience=3)],
        )

        logger.info(f"Trainer setup complete for {training_type}")

        return trainer

    def stage_1_pretrain(self) -> Dict[str, Any]:
        """Stage 1: Domain-specific pretraining with MLM."""
        logger.info("=" * 60)
        logger.info("STAGE 1: Domain-Specific Pretraining")
        logger.info("=" * 60)

        self.load_tokenizer()
        self.load_base_model(for_pretraining=True)

        dataset = self.load_dataset(self.config.pretrain_data_path)

        logger.info("Tokenizing pretrain dataset...")
        dataset = dataset.map(
            self.pretrain_tokenize,
            batched=True,
            remove_columns=dataset["train"].column_names,
            desc="Tokenizing pretrain data",
        )

        self.trainer = self.setup_trainer(dataset, "pretrain")

        logger.info("Starting domain pretraining...")
        train_result = self.trainer.train()

        logger.info("Saving pretrain checkpoint...")
        self.trainer.save_model(str(Path(self.config.output_dir) / "stage1_pretrain"))

        metrics = train_result.metrics
        self.trainer.log_metrics("pretrain", metrics)
        self.trainer.save_metrics("pretrain", metrics)

        logger.info("Stage 1 complete!")
        return metrics

    def stage_2_finetune(self) -> Dict[str, Any]:
        """Stage 2: Task-specific fine-tuning."""
        logger.info("=" * 60)
        logger.info("STAGE 2: Task-Specific Fine-Tuning")
        logger.info("=" * 60)

        # Load fresh model for fine-tuning
        self.load_tokenizer()
        self.load_base_model(for_pretraining=False)
        self.apply_lora()

        dataset = self.load_dataset(self.config.sft_data_path)

        logger.info("Tokenizing SFT dataset...")
        dataset = dataset.map(
            self.sft_tokenize,
            batched=True,
            remove_columns=dataset["train"].column_names,
            desc="Tokenizing SFT data",
        )

        self.trainer = self.setup_trainer(dataset, "sft")

        logger.info("Starting task fine-tuning...")
        train_result = self.trainer.train()

        logger.info("Saving fine-tuned model...")
        self.trainer.save_model(str(Path(self.config.output_dir) / "fine_tuned_model"))

        metrics = train_result.metrics
        self.trainer.log_metrics("sft", metrics)
        self.trainer.save_metrics("sft", metrics)

        logger.info("Stage 2 complete!")
        return metrics

    def train_full(self) -> Dict[str, Any]:
        """Run complete 2-stage training."""
        logger.info("=" * 60)
        logger.info("Starting 2-Stage Legal/Finance Training")
        logger.info("=" * 60)

        self.setup_logging()
        self.set_seed()

        # Stage 1: Domain pretraining
        pretrain_metrics = self.stage_1_pretrain()

        # Stage 2: Task fine-tuning
        finetune_metrics = self.stage_2_finetune()

        logger.info("=" * 60)
        logger.info("Training Complete!")
        logger.info("=" * 60)

        return {
            "pretrain": pretrain_metrics,
            "finetune": finetune_metrics,
        }


def create_parser() -> argparse.ArgumentParser:
    """Create argument parser."""
    parser = argparse.ArgumentParser(description="Legal/Finance Model Trainer")

    parser.add_argument(
        "--config",
        type=str,
        default="configs/legal_finance.yaml",
        help="Path to config file",
    )
    parser.add_argument(
        "--output_dir",
        type=str,
        default="experiments/2026_04_06",
        help="Output directory",
    )
    parser.add_argument(
        "--epochs", type=int, default=12, help="Number of epochs for fine-tuning"
    )
    parser.add_argument("--batch_size", type=int, default=8, help="Batch size")
    parser.add_argument("--lr", type=float, default=3e-5, help="Learning rate")
    parser.add_argument(
        "--stage",
        type=str,
        choices=["pretrain", "finetune", "both"],
        default="both",
        help="Training stage",
    )

    return parser


def main():
    """Main entry point."""
    parser = create_parser()
    args = parser.parse_args()

    # Load config from file if exists
    config = TrainingConfig(
        output_dir=args.output_dir,
        sft_epochs=args.epochs,
        sft_batch_size=args.batch_size,
        sft_learning_rate=args.lr,
    )

    trainer = LegalFinanceTrainer(config)

    if args.stage == "pretrain":
        trainer.stage_1_pretrain()
    elif args.stage == "finetune":
        trainer.stage_2_finetune()
    else:
        trainer.train_full()


if __name__ == "__main__":
    main()
