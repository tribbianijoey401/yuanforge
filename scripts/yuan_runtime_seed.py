#!/usr/bin/env python3
"""Seed immutable .yuan-run state from one verified M4 projection."""

from __future__ import annotations

import argparse
import json
import os
import pathlib
import shutil
import sys
from typing import Any

try:
    from scripts.yuan_shadow_support import verify_shadow_projection
except ModuleNotFoundError:
    from yuan_shadow_support import verify_shadow_projection

from yuan_runtime_state import (
    AuthorityError,
    RUNTIME_ROOT,
    atomic_write,
    canonical,
    rebuild_runtime_memory,
    seal_runtime,
    verify_runtime,
)


class SeedError(RuntimeError):
    """Projection cannot safely become the active Core runtime."""


def _json(path: pathlib.Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise SeedError(f"invalid JSON: {path}") from error
    if not isinstance(value, dict):
        raise SeedError(f"JSON object required: {path}")
    return value


def _copy_json(source: pathlib.Path, destination: pathlib.Path) -> None:
    _json(source)
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, destination)


def seed_verified_projection(
    repo_root: pathlib.Path,
    shadow_root: pathlib.Path,
) -> dict[str, Any]:
    repo = pathlib.Path(repo_root).resolve()
    shadow = pathlib.Path(shadow_root).resolve()
    runtime = repo / RUNTIME_ROOT
    if runtime.exists():
        raise SeedError(".yuan-run already exists")
    verification = verify_shadow_projection(repo, shadow)
    if verification.get("status") != "PASS":
        raise SeedError("shadow projection verification did not PASS")
    report = _json(shadow / "report.json")
    for field in ("legacy_snapshot_sha256", "projection_digest"):
        if report.get(field) != verification.get(field):
            raise SeedError(f"verified projection/report mismatch: {field}")
    workspace_id = report.get("active_workspace_id")
    if not isinstance(workspace_id, str) or not workspace_id:
        raise SeedError("active workspace is not declared")
    source = shadow / "workspaces" / workspace_id
    if not source.is_dir():
        raise SeedError("active workspace projection is missing")
    pending = repo / f".yuan-run.pending.{os.getpid()}"
    if pending.exists():
        raise SeedError("runtime pending directory already exists")
    (pending / "contracts").mkdir(parents=True)
    _copy_json(
        source / "work-contract.json",
        pending / "contracts" / f"{workspace_id}.json",
    )
    for area in ("attempts", "evidence"):
        inputs = sorted((source / area).glob("*.json"))
        if not inputs:
            raise SeedError(f"active projection has no {area}")
        for item in inputs:
            _copy_json(item, pending / area / item.name)
    pending.rename(runtime)
    atomic_write(
        runtime / "run-memory.json",
        canonical(rebuild_runtime_memory(repo)),
        None,
    )
    manifest = seal_runtime(
        repo,
        runtime,
        legacy_snapshot_sha256=verification["legacy_snapshot_sha256"],
        source_projection_sha256=verification["projection_digest"],
    )
    verify_runtime(repo)
    return {
        "status": "PASS",
        "active_workspace_id": workspace_id,
        "legacy_snapshot_sha256": verification["legacy_snapshot_sha256"],
        "projection_digest": verification["projection_digest"],
        "immutable_files": len(manifest["immutable_files"]),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=pathlib.Path, required=True)
    parser.add_argument("--shadow-root", type=pathlib.Path, required=True)
    args = parser.parse_args(argv)
    try:
        receipt = seed_verified_projection(args.repo, args.shadow_root)
    except (SeedError, AuthorityError, OSError, UnicodeError) as error:
        print(f"BLOCKED {error}", file=sys.stderr)
        return 2
    print(json.dumps(receipt, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
