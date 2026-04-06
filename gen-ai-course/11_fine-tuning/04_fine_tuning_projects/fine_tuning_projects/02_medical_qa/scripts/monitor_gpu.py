"""
GPU / System Monitor

Logs GPU utilisation, VRAM usage, CPU, and RAM every N seconds.
Works with or without a GPU (CPU-only mode).

Usage:
  python scripts/monitor_gpu.py                     # poll every 5 s, print to stdout
  python scripts/monitor_gpu.py --interval 10 --log logs/gpu_monitor.csv
  python scripts/monitor_gpu.py --duration 3600     # run for 1 hour then exit
"""

from __future__ import annotations

import argparse
import csv
import datetime
import logging
import sys
import time
from pathlib import Path
from typing import Dict, Optional

import psutil

# Optional GPU monitoring
try:
    import pynvml
    pynvml.nvmlInit()
    _NVML_AVAILABLE = True
except Exception:
    _NVML_AVAILABLE = False

logging.basicConfig(level=logging.INFO,
                    format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


def _gpu_stats(device_idx: int = 0) -> Dict:
    if not _NVML_AVAILABLE:
        return {"gpu_util_%": "N/A", "vram_used_mb": "N/A",
                "vram_total_mb": "N/A", "gpu_temp_c": "N/A"}
    try:
        handle = pynvml.nvmlDeviceGetHandleByIndex(device_idx)
        util = pynvml.nvmlDeviceGetUtilizationRates(handle)
        mem = pynvml.nvmlDeviceGetMemoryInfo(handle)
        temp = pynvml.nvmlDeviceGetTemperature(handle, pynvml.NVML_TEMPERATURE_GPU)
        return {
            "gpu_util_%": util.gpu,
            "vram_used_mb": round(mem.used / 1024 ** 2, 1),
            "vram_total_mb": round(mem.total / 1024 ** 2, 1),
            "gpu_temp_c": temp,
        }
    except Exception as e:
        return {"gpu_error": str(e)}


def _cpu_stats() -> Dict:
    mem = psutil.virtual_memory()
    return {
        "cpu_util_%": psutil.cpu_percent(interval=None),
        "ram_used_gb": round(mem.used / 1024 ** 3, 2),
        "ram_total_gb": round(mem.total / 1024 ** 3, 2),
        "ram_util_%": mem.percent,
    }


def collect_snapshot(device_idx: int = 0) -> Dict:
    ts = datetime.datetime.now().isoformat(timespec="seconds")
    return {"timestamp": ts, **_cpu_stats(), **_gpu_stats(device_idx)}


def monitor(interval: float = 5.0, log_file: Optional[str] = None,
            duration: Optional[float] = None) -> None:
    logger.info(f"Starting monitor | interval={interval}s | GPU={'yes' if _NVML_AVAILABLE else 'no'}")

    writer = None
    fh = None
    if log_file:
        Path(log_file).parent.mkdir(parents=True, exist_ok=True)
        fh = open(log_file, "w", newline="")
        fieldnames = ["timestamp", "cpu_util_%", "ram_used_gb", "ram_total_gb", "ram_util_%",
                      "gpu_util_%", "vram_used_mb", "vram_total_mb", "gpu_temp_c"]
        writer = csv.DictWriter(fh, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        logger.info(f"Logging to: {log_file}")

    start = time.time()
    try:
        while True:
            snap = collect_snapshot()
            msg = ("  ".join(f"{k}={v}" for k, v in snap.items() if k != "timestamp"))
            logger.info(f"[{snap['timestamp']}]  {msg}")
            if writer:
                writer.writerow(snap)
                fh.flush()
            if duration and (time.time() - start) >= duration:
                break
            time.sleep(interval)
    except KeyboardInterrupt:
        logger.info("Monitor stopped by user.")
    finally:
        if fh:
            fh.close()
        if _NVML_AVAILABLE:
            pynvml.nvmlShutdown()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="GPU / System resource monitor")
    parser.add_argument("--interval", type=float, default=5.0, help="Poll interval in seconds")
    parser.add_argument("--log", type=str, default=None, help="CSV output file")
    parser.add_argument("--duration", type=float, default=None, help="Stop after N seconds")
    parser.add_argument("--device", type=int, default=0, help="GPU device index")
    args = parser.parse_args()
    monitor(interval=args.interval, log_file=args.log, duration=args.duration)
