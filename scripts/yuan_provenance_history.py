"""Verify frozen M7 provenance plus the independently activated Core deltas."""

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
R1_PATHS = (
    ".yuan/core/0.1/candidate-manifest.json",
    ".yuan/core/0.1/runtime_replay.py",
    ".yuan/core/0.1/tests/test_replay_pending.py",
)
R2_BASELINE = "0cc910d"
R2_PATHS = (
    ".yuan/core/0.1/candidate-manifest.json",
    ".yuan/core/0.1/completion_semantics.py",
    ".yuan/core/0.1/runtime_replay.py",
    ".yuan/core/0.1/tests/test_replay_pending.py",
)
R1_INDEX_PATH = pathlib.PurePosixPath(
    ".yuan/authority/core-history/m7-to-m8/index.json"
)
R2_INDEX_PATH = pathlib.PurePosixPath(
    ".yuan/authority/core-history/m8-r1-to-r2/index.json"
)
M9_BASELINE = "aed1595"
M9_PATHS = (
    ".yuan/core/0.1/candidate-manifest.json",
    ".yuan/core/0.1/protocol.md",
)
M9_INDEX_PATH = pathlib.PurePosixPath(
    ".yuan/authority/core-history/r2-to-m9/index.json"
)
R1_DESCRIPTOR_SHA256 = (
    "b590944715e515b6533371e461bfb4afdd87d6d89ba4a75e196336d4d1cb36dd"
)
R1_DESCRIPTOR_BLOB = pathlib.PurePosixPath(
    ".yuan/authority/activation/history/"
    f"{R1_DESCRIPTOR_SHA256}.blob"
)
R2_DESCRIPTOR_SHA256 = (
    "6f08c7e10bcd433e2341471bef463e0d37fe6b6c7356f400988868a1b129afe8"
)
R2_DESCRIPTOR_BLOB = pathlib.PurePosixPath(
    ".yuan/authority/activation/history/"
    f"{R2_DESCRIPTOR_SHA256}.blob"
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
    commit = _git(repo, "rev-parse", M9_BASELINE).decode("ascii").strip()
    tree = _git(repo, "rev-parse", f"{commit}^{{tree}}").decode("ascii").strip()
    root = repo / M9_INDEX_PATH.parent
    entries = []
    for relative in M9_PATHS:
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
        "previous_delta_index": R2_INDEX_PATH.as_posix(),
        "previous_delta_index_sha256": file_sha256(repo / R2_INDEX_PATH),
        "previous_activation_descriptor": R2_DESCRIPTOR_BLOB.as_posix(),
        "previous_activation_descriptor_sha256": R2_DESCRIPTOR_SHA256,
        "activation_descriptor": ".yuan/authority/activation/yuan-core-0.1.json",
        "activation_descriptor_sha256": file_sha256(
            repo / ".yuan/authority/activation/yuan-core-0.1.json"
        ),
        "entries": entries,
    }
    write_immutable(repo / M9_INDEX_PATH, canonical(index))
    return index


def _load_index(repo: pathlib.Path, path: pathlib.PurePosixPath) -> dict[str, Any]:
    try:
        value = json.loads((repo / path).read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise ProvenanceHistoryError("Core provenance delta is missing") from error
    if not isinstance(value, dict):
        raise ProvenanceHistoryError("Core provenance delta is not an object")
    return value


def _verify_index_shape(
    index: dict[str, Any],
    *,
    paths: tuple[str, ...],
) -> list[dict[str, Any]]:
    entries = index.get("entries")
    if (
        index.get("schema_version") != "yuan.core-provenance-delta/v1"
        or index.get("frozen_registry_sha256") != M7_SHA256
        or not isinstance(entries, list)
        or not all(isinstance(item, dict) for item in entries)
        or len(entries) != len(paths)
        or {item.get("path") for item in entries} != set(paths)
    ):
        raise ProvenanceHistoryError("Core provenance delta shape mismatch")
    return entries


def verify_history_delta(repo_root: pathlib.Path) -> dict[str, Any]:
    repo = pathlib.Path(repo_root).resolve()
    r1 = _load_index(repo, R1_INDEX_PATH)
    r2 = _load_index(repo, R2_INDEX_PATH)
    m9 = _load_index(repo, M9_INDEX_PATH)
    r1_entries = _verify_index_shape(r1, paths=R1_PATHS)
    r2_entries = _verify_index_shape(r2, paths=R2_PATHS)
    m9_entries = _verify_index_shape(m9, paths=M9_PATHS)
    if (
        r2.get("previous_delta_index") != R1_INDEX_PATH.as_posix()
        or r2.get("previous_delta_index_sha256")
        != file_sha256(repo / R1_INDEX_PATH)
        or r2.get("previous_activation_descriptor")
        != R1_DESCRIPTOR_BLOB.as_posix()
        or r2.get("previous_activation_descriptor_sha256")
        != R1_DESCRIPTOR_SHA256
        or r1.get("activation_descriptor_sha256") != R1_DESCRIPTOR_SHA256
    ):
        raise ProvenanceHistoryError("Core provenance chain binding mismatch")
    previous_descriptor = repo / R1_DESCRIPTOR_BLOB
    if (
        not previous_descriptor.is_file()
        or file_sha256(previous_descriptor) != R1_DESCRIPTOR_SHA256
    ):
        raise ProvenanceHistoryError("previous activation descriptor is unavailable")
    if (
        m9.get("previous_delta_index") != R2_INDEX_PATH.as_posix()
        or m9.get("previous_delta_index_sha256")
        != file_sha256(repo / R2_INDEX_PATH)
        or m9.get("previous_activation_descriptor")
        != R2_DESCRIPTOR_BLOB.as_posix()
        or m9.get("previous_activation_descriptor_sha256")
        != R2_DESCRIPTOR_SHA256
        or r2.get("activation_descriptor_sha256") != R2_DESCRIPTOR_SHA256
        or not (repo / R2_DESCRIPTOR_BLOB).is_file()
        or file_sha256(repo / R2_DESCRIPTOR_BLOB) != R2_DESCRIPTOR_SHA256
    ):
        raise ProvenanceHistoryError("M9 provenance chain binding mismatch")
    descriptor = repo / m9.get("activation_descriptor", "")
    if (
        not descriptor.is_file()
        or file_sha256(descriptor) != m9.get("activation_descriptor_sha256")
    ):
        raise ProvenanceHistoryError("Core delta activation binding mismatch")
    for item in (*r1_entries, *r2_entries, *m9_entries):
        blob = repo / item["retained_blob"]
        if (
            not blob.is_file()
            or file_sha256(blob) != item.get("old_sha256")
        ):
            raise ProvenanceHistoryError("Core delta byte binding mismatch")
    r1_new = {item["path"]: item["new_sha256"] for item in r1_entries}
    r2_old = {item["path"]: item["old_sha256"] for item in r2_entries}
    for path in R1_PATHS:
        if r1_new[path] != r2_old[path]:
            raise ProvenanceHistoryError("Core provenance delta chain is discontinuous")
    r2_new = {item["path"]: item["new_sha256"] for item in r2_entries}
    m9_old = {item["path"]: item["old_sha256"] for item in m9_entries}
    if r2_new[".yuan/core/0.1/candidate-manifest.json"] != m9_old[
        ".yuan/core/0.1/candidate-manifest.json"
    ]:
        raise ProvenanceHistoryError("M9 candidate provenance is discontinuous")
    for item in m9_entries:
        current = repo / item["path"]
        if (
            not current.is_file()
            or file_sha256(current) != item.get("new_sha256")
        ):
            raise ProvenanceHistoryError("current Core delta byte binding mismatch")
    return {"r1": r1, "r2": r2, "m9": m9}


def verify_frozen_and_delta(repo_root: pathlib.Path) -> dict[str, Any]:
    repo = pathlib.Path(repo_root).resolve()
    chain = verify_history_delta(repo)
    r1 = chain["r1"]
    r2 = chain["r2"]
    m9 = chain["m9"]
    commit = r1["baseline_commit"]
    if (
        _git(repo, "rev-parse", commit).decode("ascii").strip() != commit
        or _git(repo, "rev-parse", f"{commit}^{{tree}}").decode("ascii").strip()
        != r1["baseline_tree"]
    ):
        raise ProvenanceHistoryError("frozen provenance baseline object mismatch")
    r2_commit = r2["baseline_commit"]
    if (
        _git(repo, "rev-parse", r2_commit).decode("ascii").strip() != r2_commit
        or _git(repo, "rev-parse", f"{r2_commit}^{{tree}}").decode("ascii").strip()
        != r2["baseline_tree"]
    ):
        raise ProvenanceHistoryError("r2 provenance baseline object mismatch")
    for item in r2["entries"]:
        if sha256(_git(repo, "show", f"{r2_commit}:{item['path']}")) != item["old_sha256"]:
            raise ProvenanceHistoryError("r2 retained bytes differ from baseline")
    m9_commit = m9["baseline_commit"]
    if (
        _git(repo, "rev-parse", m9_commit).decode("ascii").strip() != m9_commit
        or _git(repo, "rev-parse", f"{m9_commit}^{{tree}}").decode("ascii").strip()
        != m9["baseline_tree"]
    ):
        raise ProvenanceHistoryError("M9 provenance baseline object mismatch")
    for item in m9["entries"]:
        if sha256(_git(repo, "show", f"{m9_commit}:{item['path']}")) != item["old_sha256"]:
            raise ProvenanceHistoryError("M9 retained bytes differ from baseline")
    with tempfile.TemporaryDirectory(prefix="yuan-m7-history-") as temp_name:
        historical = pathlib.Path(temp_name) / "checkout"
        _git(repo, "worktree", "add", "--detach", str(historical), commit)
        try:
            for item in r1["entries"]:
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
            "delta_assertions": len(r1["entries"]) * 3,
            "r2_delta_assertions": len(r2["entries"]) * 3 + len(R1_PATHS) + 3,
            "baseline_commit": commit,
            "baseline_tree": r1["baseline_tree"],
            "delta_index_sha256": file_sha256(repo / R1_INDEX_PATH),
            "r2_baseline_commit": r2_commit,
            "r2_baseline_tree": r2["baseline_tree"],
            "r2_delta_index_sha256": file_sha256(repo / R2_INDEX_PATH),
            "m9_baseline_commit": m9_commit,
            "m9_baseline_tree": m9["baseline_tree"],
            "m9_delta_assertions": len(m9["entries"]) * 3 + 4,
            "m9_delta_index_sha256": file_sha256(repo / M9_INDEX_PATH),
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
