"""Legacy entrypoint for preprocessing."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT / "src"))

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
    tokenized = pipeline.tokenize_splits(tokenizer, force_rebuild=cfg.data.force_rebuild)

    print(
        f"Prepared dataset | train={len(raw['train'])} validation={len(raw['validation'])} "
        f"test={len(raw['test'])} tokenized_train={len(tokenized['train'])}"
    )


if __name__ == "__main__":
    main()
