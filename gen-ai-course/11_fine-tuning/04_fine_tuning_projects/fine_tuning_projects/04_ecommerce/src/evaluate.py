"""Legacy entrypoint for evaluation."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT / "src"))

from ecommerce_ft.evaluation import evaluate_model_from_path
from ecommerce_ft.utils.logging_utils import setup_logging


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=str, default="configs/train_config.yaml")
    parser.add_argument("--split", type=str, default="test", choices=["validation", "test"])
    parser.add_argument("--max_eval_samples", type=int, default=300)
    parser.add_argument("--adapter_dir", type=str, default=None)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    setup_logging()
    metrics = evaluate_model_from_path(
        config_path=PROJECT_ROOT / args.config,
        project_root=PROJECT_ROOT,
        split=args.split,
        max_eval_samples=args.max_eval_samples,
        adapter_dir=args.adapter_dir,
    )
    print("Evaluation complete.")
    for key, value in metrics.items():
        print(f"{key}: {value:.6f}")


if __name__ == "__main__":
    main()
