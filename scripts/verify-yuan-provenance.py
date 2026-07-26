#!/usr/bin/env python3
"""CLI for the independent M7 provenance verifier."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from yuan_provenance_verify import ProvenanceFailure, verify

ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, default=ROOT)
    parser.add_argument(
        "--provenance-dir",
        type=Path,
        default=ROOT / ".yuan/extensions/provenance",
    )
    args = parser.parse_args()
    try:
        result = verify(args.repo.resolve(), args.provenance_dir.resolve())
    except (OSError, KeyError, ValueError, UnicodeError, json.JSONDecodeError, ProvenanceFailure) as exc:
        print(f"FAIL {exc}", file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
