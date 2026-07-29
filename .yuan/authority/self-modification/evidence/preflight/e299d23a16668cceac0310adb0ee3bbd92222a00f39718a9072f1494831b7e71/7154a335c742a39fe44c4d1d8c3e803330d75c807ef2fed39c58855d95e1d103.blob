#!/usr/bin/env python3
"""Independently rebind the frozen M3 bridge to the M6 Core manifest.

The bridge and held-out validator remain byte-for-byte frozen.  This wrapper
only supplies the newly observed content address, then lets the unchanged M1
bootstrap verifier execute the isolated suite.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import pathlib
import sys


ROOT = pathlib.Path(__file__).resolve().parents[2]
FROZEN_BRIDGE = ROOT / "tests" / "core_01" / "run_m3_bootstrap.py"
FROZEN_HELD_OUT = ROOT / "tests" / "core_01" / "held_out_validator.py"
FROZEN_BRIDGE_SHA256 = (
    "a262ad8f57ad8581b1303980a51d91e580159fd0fa906703402b9c7dc58b4db6"
)
FROZEN_HELD_OUT_SHA256 = (
    "104bfdef44b77012ab69c83cd414a18269b924fefec647e816951771f97cc4a6"
)


def _sha256(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidate-manifest-sha256", required=True)
    parser.add_argument("--receipt", required=True, type=pathlib.Path)
    parser.add_argument("--manifest-snapshot", required=True, type=pathlib.Path)
    args = parser.parse_args()
    if len(args.candidate_manifest_sha256) != 64 or any(
        token not in "0123456789abcdef"
        for token in args.candidate_manifest_sha256
    ):
        raise SystemExit("candidate manifest SHA-256 must be lowercase hex")
    if _sha256(FROZEN_BRIDGE) != FROZEN_BRIDGE_SHA256:
        raise SystemExit("frozen M3 bridge drift")
    if _sha256(FROZEN_HELD_OUT) != FROZEN_HELD_OUT_SHA256:
        raise SystemExit("frozen M3 held-out validator drift")

    spec = importlib.util.spec_from_file_location("frozen_m3_bridge", FROZEN_BRIDGE)
    if spec is None or spec.loader is None:
        raise SystemExit("cannot load frozen M3 bridge")
    bridge = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(bridge)
    bridge.CORE_MANIFEST_SHA256 = args.candidate_manifest_sha256
    original_argv = sys.argv
    try:
        sys.argv = [
            str(FROZEN_BRIDGE),
            "--receipt",
            str(args.receipt),
            "--manifest-snapshot",
            str(args.manifest_snapshot),
        ]
        return int(bridge.main())
    finally:
        sys.argv = original_argv


if __name__ == "__main__":
    raise SystemExit(main())
