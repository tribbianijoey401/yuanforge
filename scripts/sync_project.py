#!/usr/bin/env python3
"""Yuan Source Repository 外部 Project 同步入口。"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


SOURCE_ROOT = Path(__file__).resolve().parent.parent
INSTALLER = SOURCE_ROOT / "bin" / "yuanforge-init"


def main() -> int:
    parser = argparse.ArgumentParser(description="Yuan Project Sync")
    parser.add_argument("command", choices=("init", "update", "check"))
    parser.add_argument("project_root")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    command = [sys.executable, "-B", str(INSTALLER), args.project_root, "--force"]
    if args.command == "init":
        command.extend(("--mode", "existing"))
    elif args.command == "update":
        command.append("--update")
    else:
        command.append("--check")
    if args.dry_run:
        command.append("--dry-run")

    completed = subprocess.run(command, cwd=SOURCE_ROOT)
    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())
