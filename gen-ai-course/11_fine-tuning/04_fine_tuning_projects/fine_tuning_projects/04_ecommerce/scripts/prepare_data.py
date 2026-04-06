"""Prepare and cache e-commerce datasets for training."""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from ecommerce_ft.config import load_config, resolve_project_paths
from ecommerce_ft.data import EcommerceDatasetPipeline
from ecommerce_ft.modeling import load_tokenizer
from ecommerce_ft.utils.logging_utils import setup_logging


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=str, default="configs/train_config.yaml")
    parser.add_argument("--force-rebuild", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    setup_logging()

    cfg = load_config(PROJECT_ROOT / args.config)
    cfg = resolve_project_paths(cfg, project_root=PROJECT_ROOT)
    if args.force_rebuild:
        cfg.data.force_rebuild = True

    pipeline = EcommerceDatasetPipeline(cfg)
    raw = pipeline.build_raw_splits(force_rebuild=cfg.data.force_rebuild)
    tokenizer = load_tokenizer(cfg)
    tokenized = pipeline.tokenize_splits(tokenizer=tokenizer, force_rebuild=cfg.data.force_rebuild)

    logging.info(
        "Dataset prepared. train=%d validation=%d test=%d tokenized_train=%d",
        len(raw["train"]),
        len(raw["validation"]),
        len(raw["test"]),
        len(tokenized["train"]),
    )


if __name__ == "__main__":
    main()

