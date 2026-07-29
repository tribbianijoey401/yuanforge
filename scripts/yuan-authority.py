#!/usr/bin/env python3
"""CLI for Yuan Core runtime authority records."""

from __future__ import annotations

import argparse
import json
import pathlib
import sys

from yuan_authority import (
    AuthorityError,
    initialize_authority,
    switch_authority,
    verify_authority,
)


ROOT = pathlib.Path(__file__).resolve().parents[1]
M7_APPROVAL = (
    ROOT
    / "docs/20260726-yuan-core-01-upgrade/evidence/m7-review/M7-APPROVAL.json"
)
M7_SHA256 = "4e8d974409bf0ad2bd66df17039c8dee12b6fca03a0e2860ed5ac865615823d4"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=pathlib.Path, default=ROOT)
    commands = parser.add_subparsers(dest="command", required=True)
    initialize = commands.add_parser("initialize")
    initialize.add_argument("--legacy-snapshot-sha256", required=True)
    switch = commands.add_parser("switch")
    switch.add_argument("--to", choices=("legacy", "core"), required=True)
    switch.add_argument("--expected-pointer-sha256", required=True)
    commands.add_parser("verify")
    args = parser.parse_args(argv)
    repo = args.repo.resolve()
    approval = repo / M7_APPROVAL.relative_to(ROOT)
    try:
        if args.command == "initialize":
            result = {
                "status": "PASS",
                "pointer_sha256": initialize_authority(
                    repo,
                    legacy_snapshot_sha256=args.legacy_snapshot_sha256,
                    m7_approval=approval,
                    expected_m7_sha256=M7_SHA256,
                ),
            }
        elif args.command == "switch":
            result = switch_authority(
                repo,
                target=args.to,
                expected_pointer_sha256=args.expected_pointer_sha256,
                m7_approval=approval,
                expected_m7_sha256=M7_SHA256,
            )
        else:
            result = verify_authority(repo)
    except (AuthorityError, OSError, UnicodeError, json.JSONDecodeError) as error:
        print(f"BLOCKED {error}", file=sys.stderr)
        return 2
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
