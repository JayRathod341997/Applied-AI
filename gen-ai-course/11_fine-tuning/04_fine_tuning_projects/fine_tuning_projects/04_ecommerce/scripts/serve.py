"""Run the FastAPI inference server with uvicorn."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

import uvicorn

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=str, default="configs/train_config.yaml")
    parser.add_argument("--adapter_dir", type=str, default="")
    parser.add_argument("--host", type=str, default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--reload", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    os.environ["ECOM_CONFIG_PATH"] = str((PROJECT_ROOT / args.config).resolve())
    if args.adapter_dir:
        os.environ["ECOM_ADAPTER_DIR"] = str((PROJECT_ROOT / args.adapter_dir).resolve())

    uvicorn.run("deploy.app:app", host=args.host, port=args.port, reload=args.reload)


if __name__ == "__main__":
    main()

