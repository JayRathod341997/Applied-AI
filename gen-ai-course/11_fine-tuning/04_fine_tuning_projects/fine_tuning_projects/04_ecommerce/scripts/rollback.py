"""Backup and rollback helper for model artifacts."""

from __future__ import annotations

import argparse
import shutil
from datetime import datetime
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    backup = subparsers.add_parser("backup", help="Create backup from current model directory.")
    backup.add_argument("--source", type=str, default="models/ecommerce_support")
    backup.add_argument("--backup_root", type=str, default="models/backups")

    rollback = subparsers.add_parser("rollback", help="Rollback model directory from latest backup.")
    rollback.add_argument("--target", type=str, default="models/ecommerce_support")
    rollback.add_argument("--backup_root", type=str, default="models/backups")

    listing = subparsers.add_parser("list", help="List existing backups.")
    listing.add_argument("--backup_root", type=str, default="models/backups")

    return parser.parse_args()


def create_backup(source: Path, backup_root: Path) -> Path:
    if not source.exists():
        raise FileNotFoundError(f"Source directory not found: {source}")
    backup_root.mkdir(parents=True, exist_ok=True)
    stamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    destination = backup_root / f"backup_{stamp}"
    shutil.copytree(source, destination)
    return destination


def rollback_latest(target: Path, backup_root: Path) -> tuple[Path, Path]:
    backups = sorted([path for path in backup_root.glob("backup_*") if path.is_dir()], reverse=True)
    if not backups:
        raise RuntimeError(f"No backup directories found in {backup_root}")

    latest = backups[0]
    stamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    archived_current = backup_root / f"failed_current_{stamp}"

    if target.exists():
        shutil.move(str(target), str(archived_current))
    shutil.copytree(latest, target)
    return latest, archived_current


def main() -> None:
    args = parse_args()

    if args.command == "backup":
        source = Path(args.source).resolve()
        backup_root = Path(args.backup_root).resolve()
        destination = create_backup(source=source, backup_root=backup_root)
        print(f"Backup created: {destination}")
        return

    if args.command == "rollback":
        target = Path(args.target).resolve()
        backup_root = Path(args.backup_root).resolve()
        latest, archived_current = rollback_latest(target=target, backup_root=backup_root)
        print(f"Rolled back target from backup: {latest}")
        if archived_current.exists():
            print(f"Previous target archived at: {archived_current}")
        return

    if args.command == "list":
        backup_root = Path(args.backup_root).resolve()
        backups = sorted([path for path in backup_root.glob("backup_*") if path.is_dir()], reverse=True)
        if not backups:
            print("No backups found.")
            return
        for backup in backups:
            print(str(backup))


if __name__ == "__main__":
    main()

