"""Configuration models and loaders for the e-commerce project."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

import yaml


@dataclass(slots=True)
class ModelConfig:
    base_model_name: str = "EleutherAI/gpt-neo-125M"
    max_seq_length: int = 512
    load_in_4bit: bool = False
    torch_dtype: str = "float16"
    lora_r: int = 16
    lora_alpha: int = 32
    lora_dropout: float = 0.05
    target_modules: list[str] = field(default_factory=lambda: ["q_proj", "v_proj"])


@dataclass(slots=True)
class DataConfig:
    bitext_dataset_candidates: list[str] = field(
        default_factory=lambda: ["bitext/Bitext-customer-support-llm-chatbot-training-dataset"]
    )
    amazon_qa_dataset_candidates: list[str] = field(
        default_factory=lambda: ["mteb/amazon_qa", "donfu/oa-amazon-qa"]
    )
    cache_dir: str = "data/cache"
    processed_dir: str = "data/processed"
    bitext_scan_examples: int = 120000
    amazon_scan_examples: int = 200000
    train_split: float = 0.9
    val_split: float = 0.05
    test_split: float = 0.05
    max_samples_total: int = 14000
    max_samples_per_dataset: dict[str, int] = field(
        default_factory=lambda: {
            "bitext_customer_support": 7000,
            "amazon_qa": 7000,
        }
    )
    min_prompt_chars: int = 8
    min_response_chars: int = 8
    force_rebuild: bool = False


@dataclass(slots=True)
class TrainingConfig:
    output_dir: str = "models/ecommerce_support"
    per_device_train_batch_size: int = 4
    per_device_eval_batch_size: int = 4
    gradient_accumulation_steps: int = 8
    num_train_epochs: int = 1
    learning_rate: float = 2e-4
    weight_decay: float = 0.01
    warmup_ratio: float = 0.03
    logging_steps: int = 10
    save_strategy: str = "epoch"
    evaluation_strategy: str = "epoch"
    gradient_checkpointing: bool = True
    fp16: bool = True
    max_grad_norm: float = 0.3
    save_total_limit: int = 2


@dataclass(slots=True)
class GenerationConfig:
    max_new_tokens: int = 180
    temperature: float = 0.7
    top_p: float = 0.9
    repetition_penalty: float = 1.05


@dataclass(slots=True)
class AppConfig:
    project_name: str = "ecommerce_customer_support_bot"
    seed: int = 42
    model: ModelConfig = field(default_factory=ModelConfig)
    data: DataConfig = field(default_factory=DataConfig)
    training: TrainingConfig = field(default_factory=TrainingConfig)
    generation: GenerationConfig = field(default_factory=GenerationConfig)

    def validate(self) -> None:
        total_split = self.data.train_split + self.data.val_split + self.data.test_split
        if abs(total_split - 1.0) > 1e-6:
            raise ValueError(
                f"Data split must sum to 1.0, received {total_split:.6f}. "
                "Check train_split/val_split/test_split."
            )
        if self.data.max_samples_total <= 0:
            raise ValueError("max_samples_total must be > 0.")
        if self.model.max_seq_length < 64:
            raise ValueError("max_seq_length should be >= 64.")


def _merge_dicts(defaults: dict[str, Any], incoming: dict[str, Any]) -> dict[str, Any]:
    merged = defaults.copy()
    for key, value in incoming.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _merge_dicts(merged[key], value)
        else:
            merged[key] = value
    return merged


def load_config(config_path: str | Path) -> AppConfig:
    path = Path(config_path).resolve()
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")

    with path.open("r", encoding="utf-8") as file:
        raw_cfg = yaml.safe_load(file) or {}

    default_cfg = {
        "project_name": AppConfig().project_name,
        "seed": AppConfig().seed,
        "model": asdict(ModelConfig()),
        "data": asdict(DataConfig()),
        "training": asdict(TrainingConfig()),
        "generation": asdict(GenerationConfig()),
    }
    cfg = _merge_dicts(default_cfg, raw_cfg)

    app_cfg = AppConfig(
        project_name=cfg["project_name"],
        seed=int(cfg["seed"]),
        model=ModelConfig(**cfg["model"]),
        data=DataConfig(**cfg["data"]),
        training=TrainingConfig(**cfg["training"]),
        generation=GenerationConfig(**cfg["generation"]),
    )
    app_cfg.validate()
    return app_cfg


def resolve_project_paths(config: AppConfig, project_root: str | Path) -> AppConfig:
    root = Path(project_root).resolve()
    config.data.cache_dir = str((root / config.data.cache_dir).resolve())
    config.data.processed_dir = str((root / config.data.processed_dir).resolve())
    config.training.output_dir = str((root / config.training.output_dir).resolve())
    return config

