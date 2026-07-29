"""Verify frozen M7 provenance plus an independently activated Core delta."""

from __future__ import annotations

import argparse
import json
import pathlib
import subprocess
import sys
import tempfile
from typing import Any

from yuan_runtime_state import canonical, file_sha256, sha256, write_immutable


M7_SHA256 = "4e8d974409bf0ad2bd66df17039c8dee12b6fca03a0e2860ed5ac865615823d4"
BASELINE = "a888fdd"
CHANGED_CORE_PATHS = (
    ".yuan/core/0.1/candidate-manifest.json",
    ".yuan/core/0.1/runtime_replay.py",
    ".yuan/core/0.1/tests/test_replay_pending.py",
)
INDEX_PATH = pathlib.PurePosixPath(
    ".yuan/authority/core-history/m7-to-m8/index.json"
)


class ProvenanceHistoryError(RuntimeError):
    """A historical registry or current delta failed closed."""


def _git(repo: pathlib.Path, *args: str) -> bytes:
    process = subprocess.run(
        ["git", *args],
        cwd=repo,
        capture_output=True,
        check=False,
    )
    if process.returncode != 0:
        raise ProvenanceHistoryError("required immutable Git object is unavailable")
    return process.stdout


def create_history_delta(repo_root: pathlib.Path) -> dict[str, Any]:
    repo = pathlib.Path(repo_root).resolve()
    commit = _git(repo, "rev-parse", BASELINE).decode("ascii").strip()
    tree = _git(repo, "rev-parse", f"{commit}^{{tree}}").decode("ascii").strip()
    root = repo / INDEX_PATH.parent
    entries = []
    for relative in CHANGED_CORE_PATHS:
        old_bytes = _git(repo, "show", f"{commit}:{relative}")
        old_sha = sha256(old_bytes)
        blob = root / "blobs" / f"{old_sha}.blob"
        write_immutable(blob, old_bytes)
        entries.append(
            {
                "path": relative,
                "old_sha256": old_sha,
                "new_sha256": file_sha256(repo / relative),
                "retained_blob": blob.relative_to(repo).as_posix(),
            }
        )
    index = {
        "schema_version": "yuan.core-provenance-delta/v1",
        "baseline_commit": commit,
        "baseline_tree": tree,
        "frozen_registry_sha256": M7_SHA256,
        "activation_descriptor": ".yuan/authority/activation/yuan-core-0.1.json",
        "activation_descriptor_sha256": file_sha256(
            repo / ".yuan/authority/activation/yuan-core-0.1.json"
        ),
        "entries": entries,
    }
    write_immutable(repo / INDEX_PATH, canonical(index))
    return index


def verify_history_delta(repo_root: pathlib.Path) -> dict[str, Any]:
    repo = pathlib.Path(repo_root).resolve()
    try:
        index = json.loads((repo / INDEX_PATH).read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise ProvenanceHistoryError("Core provenance delta is missing") from error
    entries = index.get("entries")
    if (
        index.get("schema_version") != "yuan.core-provenance-delta/v1"
        or index.get("frozen_registry_sha256") != M7_SHA256
        or not isinstance(entries, list)
        or len(entries) != len(CHANGED_CORE_PATHS)
        or {item.get("path") for item in entries} != set(CHANGED_CORE_PATHS)
    ):
        raise ProvenanceHistoryError("Core provenance delta shape mismatch")
    descriptor = repo / index.get("activation_descriptor", "")
    if (
        not descriptor.is_file()
        or file_sha256(descriptor) != index.get("activation_descriptor_sha256")
    ):
        raise ProvenanceHistoryError("Core delta activation binding mismatch")
    for item in entries:
        blob = repo / item["retained_blob"]
        current = repo / item["path"]
        if (
            not blob.is_file()
            or file_sha256(blob) != item.get("old_sha256")
            or not current.is_file()
            or file_sha256(current) != item.get("new_sha256")
        ):
            raise ProvenanceHistoryError("Core delta byte binding mismatch")
    return index


def verify_frozen_and_delta(repo_root: pathlib.Path) -> dict[str, Any]:
    repo = pathlib.Path(repo_root).resolve()
    index = verify_history_delta(repo)
    commit = index["baseline_commit"]
    if (
        _git(repo, "rev-parse", commit).decode("ascii").strip() != commit
        or _git(repo, "rev-parse", f"{commit}^{{tree}}").decode("ascii").strip()
        != index["baseline_tree"]
    ):
        raise ProvenanceHistoryError("frozen provenance baseline object mismatch")
    with tempfile.TemporaryDirectory(prefix="yuan-m7-history-") as temp_name:
        historical = pathlib.Path(temp_name) / "checkout"
        _git(repo, "worktree", "add", "--detach", str(historical), commit)
        try:
            for item in index["entries"]:
                if file_sha256(historical / item["path"]) != item["old_sha256"]:
                    raise ProvenanceHistoryError("retained bytes differ from baseline")
            process = subprocess.run(
                [
                    sys.executable,
                    "-B",
                    str(historical / "scripts/verify-yuan-provenance.py"),
                    "--repo",
                    str(historical),
                    "--semantic-registry-sha256",
                    M7_SHA256,
                ],
                cwd=historical,
                text=True,
                encoding="utf-8",
                errors="replace",
                capture_output=True,
                check=False,
            )
        finally:
            subprocess.run(
                ["git", "worktree", "remove", "--force", str(historical)],
                cwd=repo,
                capture_output=True,
                check=False,
            )
    if process.returncode != 0:
        detail = process.stdout.strip() or process.stderr.strip()
        raise ProvenanceHistoryError(
            f"frozen M7 provenance replay failed: {detail[:2000]}"
        )
    try:
        receipt = json.loads(process.stdout)
    except json.JSONDecodeError as error:
        raise ProvenanceHistoryError("frozen provenance receipt is invalid") from error
    receipt.update(
        {
            "assertions": receipt.get("semantic_records", 0),
            "delta_assertions": len(index["entries"]) * 3,
            "baseline_commit": commit,
            "baseline_tree": index["baseline_tree"],
            "delta_index_sha256": file_sha256(repo / INDEX_PATH),
        }
    )
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=pathlib.Path, default=pathlib.Path.cwd())
    parser.add_argument("--create", action="store_true")
    args = parser.parse_args()
    try:
        result = (
            create_history_delta(args.repo)
            if args.create
            else verify_frozen_and_delta(args.repo)
        )
    except (ProvenanceHistoryError, OSError, UnicodeError, json.JSONDecodeError) as error:
        print(f"FAIL {error}", file=sys.stderr)
        return 1
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
