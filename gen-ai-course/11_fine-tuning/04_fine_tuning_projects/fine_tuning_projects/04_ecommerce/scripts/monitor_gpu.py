"""Simple GPU monitor for training runs."""

from __future__ import annotations

import argparse
import csv
import subprocess
import time
from datetime import datetime
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--interval", type=int, default=5, help="Polling interval in seconds.")
    parser.add_argument("--iterations", type=int, default=0, help="0 means run forever.")
    parser.add_argument("--output", type=str, default="models/gpu_usage_log.csv")
    return parser.parse_args()


def read_gpu_line() -> str:
    command = [
        "nvidia-smi",
        "--query-gpu=name,utilization.gpu,memory.used,memory.total,temperature.gpu",
        "--format=csv,noheader,nounits",
    ]
    output = subprocess.check_output(command, text=True)
    return output.strip().splitlines()[0]


def main() -> None:
    args = parse_args()
    output_path = Path(args.output).resolve()
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("a", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        if output_path.stat().st_size == 0:
            writer.writerow(
                ["timestamp", "gpu_name", "gpu_util_pct", "memory_used_mb", "memory_total_mb", "temp_c"]
            )

        count = 0
        while True:
            line = read_gpu_line()
            parts = [part.strip() for part in line.split(",")]
            writer.writerow([datetime.utcnow().isoformat(), *parts])
            file.flush()
            count += 1

            if args.iterations > 0 and count >= args.iterations:
                break
            time.sleep(args.interval)


if __name__ == "__main__":
    main()

