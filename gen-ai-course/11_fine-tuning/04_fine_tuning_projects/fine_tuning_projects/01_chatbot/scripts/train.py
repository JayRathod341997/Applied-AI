"""Train a custom chatbot model with LoRA."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from chatbot_ft.training import run_training_from_path
from chatbot_ft.utils.logging_utils import setup_logging


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=str, default="configs/train_config.yaml")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    setup_logging()
    metrics = run_training_from_path(
        config_path=PROJECT_ROOT / args.config,
        project_root=PROJECT_ROOT,
    )
    print("Training complete.")
    for key, value in metrics.items():
        print(f"{key}: {value}")


if __name__ == "__main__":
    main()

