"""Training entrypoints."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from accelerate import Accelerator
from transformers import Trainer, TrainingArguments, set_seed

from .config import AppConfig, load_config, resolve_project_paths
from .data import ChatbotDatasetPipeline, SupervisedDataCollator
from .modeling import load_model_for_training, load_tokenizer

LOGGER = logging.getLogger(__name__)


def _to_serializable(metrics: dict[str, Any]) -> dict[str, Any]:
    serializable: dict[str, Any] = {}
    for key, value in metrics.items():
        if hasattr(value, "item"):
            serializable[key] = value.item()
        else:
            serializable[key] = value
    return serializable


def run_training(config: AppConfig) -> dict[str, Any]:
    accelerator = Accelerator()
    accelerator.print("Initializing training pipeline...")

    set_seed(config.seed)

    tokenizer = load_tokenizer(config)
    pipeline = ChatbotDatasetPipeline(config)
    tokenized = pipeline.tokenize_splits(tokenizer, force_rebuild=config.data.force_rebuild)

    model = load_model_for_training(config)

    collator = SupervisedDataCollator(tokenizer=tokenizer)
    output_dir = Path(config.training.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    train_args = TrainingArguments(
        output_dir=str(output_dir),
        per_device_train_batch_size=config.training.per_device_train_batch_size,
        per_device_eval_batch_size=config.training.per_device_eval_batch_size,
        gradient_accumulation_steps=config.training.gradient_accumulation_steps,
        learning_rate=config.training.learning_rate,
        num_train_epochs=config.training.num_train_epochs,
        weight_decay=config.training.weight_decay,
        warmup_ratio=config.training.warmup_ratio,
        logging_steps=config.training.logging_steps,
        save_strategy=config.training.save_strategy,
        evaluation_strategy=config.training.evaluation_strategy,
        max_grad_norm=config.training.max_grad_norm,
        fp16=config.training.fp16,
        bf16=False,
        gradient_checkpointing=config.training.gradient_checkpointing,
        save_total_limit=config.training.save_total_limit,
        load_best_model_at_end=True,
        metric_for_best_model="eval_loss",
        greater_is_better=False,
        report_to="none",
        optim="adamw_torch",
    )

    trainer = Trainer(
        model=model,
        args=train_args,
        train_dataset=tokenized["train"],
        eval_dataset=tokenized["validation"],
        data_collator=collator,
        tokenizer=tokenizer,
    )

    train_result = trainer.train()
    eval_metrics = trainer.evaluate(tokenized["validation"])
    test_metrics = trainer.evaluate(tokenized["test"], metric_key_prefix="test")

    adapter_dir = output_dir / "adapter"
    adapter_dir.mkdir(parents=True, exist_ok=True)
    trainer.model.save_pretrained(str(adapter_dir))
    tokenizer.save_pretrained(str(adapter_dir))

    metrics: dict[str, Any] = {}
    metrics.update(_to_serializable(train_result.metrics))
    metrics.update(_to_serializable(eval_metrics))
    metrics.update(_to_serializable(test_metrics))

    metrics_path = output_dir / "training_metrics.json"
    metrics_path.write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    LOGGER.info("Saved metrics to %s", metrics_path)
    return metrics


def run_training_from_path(config_path: str | Path, project_root: str | Path) -> dict[str, Any]:
    cfg = load_config(config_path)
    cfg = resolve_project_paths(cfg, project_root=project_root)
    return run_training(cfg)
