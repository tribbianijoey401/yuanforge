"""Content-addressed Yuan Core authority pointer and writer guard."""

from __future__ import annotations

import json
import pathlib
from typing import Any

from yuan_runtime_state import (
    AuthorityError,
    IMMUTABLE_RUNTIME_AREAS,
    RUNTIME_ROOT,
    SHA256,
    atomic_write,
    canonical,
    file_sha256,
    inside,
    rebuild_runtime_memory,
    seal_runtime,
    sha256,
    verify_runtime,
    write_immutable,
)


AUTHORITY_ROOT = pathlib.PurePosixPath(".yuan/authority")
CURRENT_PATH = AUTHORITY_ROOT / "current"
RECORDS_PATH = AUTHORITY_ROOT / "records"
LEGACY_ROOT = pathlib.PurePosixPath("docs")


def _approved(approval_path: pathlib.Path, expected_m7_sha256: str) -> dict[str, Any]:
    if not SHA256.fullmatch(expected_m7_sha256):
        raise AuthorityError("M7 expected hash is invalid")
    try:
        approval = json.loads(
            pathlib.Path(approval_path).read_text(encoding="utf-8")
        )
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise AuthorityError("M7 approval is missing or invalid") from error
    if (
        approval.get("verdict") != "PASS"
        or approval.get("approved_semantic_registry_sha256")
        != expected_m7_sha256
        or not approval.get("m8_requirements", {}).get(
            "authority_receipt_must_bind_semantic_registry_sha256"
        )
    ):
        raise AuthorityError("M7 approval/hash requirement is not satisfied")
    return approval


def _record_path(repo: pathlib.Path, record_sha256: str) -> pathlib.Path:
    if not SHA256.fullmatch(record_sha256):
        raise AuthorityError("authority record SHA-256 is invalid")
    return repo / RECORDS_PATH / f"{record_sha256}.json"


def load_current(repo_root: pathlib.Path) -> dict[str, Any]:
    repo = pathlib.Path(repo_root).resolve()
    pointer_path = repo / CURRENT_PATH
    try:
        pointer_bytes = pointer_path.read_bytes()
        pointer = json.loads(pointer_bytes.decode("utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise AuthorityError("authority current pointer missing or invalid") from error
    if (
        set(pointer) != {"schema_version", "record_sha256"}
        or pointer["schema_version"] != "yuan.authority-current/v1"
    ):
        raise AuthorityError("authority current pointer fields are invalid")
    record_path = _record_path(repo, pointer["record_sha256"])
    try:
        record_bytes = record_path.read_bytes()
        record = json.loads(record_bytes.decode("utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise AuthorityError("authority record missing or invalid") from error
    if sha256(record_bytes) != pointer["record_sha256"]:
        raise AuthorityError("authority record content address mismatch")
    return {
        "pointer": pointer,
        "pointer_path": pointer_path,
        "pointer_sha256": sha256(pointer_bytes),
        "record": record,
        "record_path": record_path,
        "record_sha256": pointer["record_sha256"],
    }


def _new_record(
    *,
    revision: int,
    target: str,
    previous_authority: str | None,
    previous_record_sha256: str | None,
    legacy_snapshot_sha256: str,
    runtime_snapshot_sha256: str,
    runtime_root: str = RUNTIME_ROOT.as_posix(),
    runtime_pointer_sha256: str | None = None,
    protocol_activation: dict[str, Any] | None = None,
    m7_sha256: str,
    pointer_before_sha256: str | None,
) -> dict[str, Any]:
    record = {
        "schema_version": "yuan.authority-record/v1",
        "revision": revision,
        "authority": target,
        "legacy_root": LEGACY_ROOT.as_posix(),
        "runtime_root": runtime_root,
        "previous_record_sha256": previous_record_sha256,
        "legacy_snapshot_sha256": legacy_snapshot_sha256,
        "runtime_snapshot_sha256": runtime_snapshot_sha256,
        "m7_semantic_registry_sha256": m7_sha256,
        "receipt": {
            "schema_version": "yuan.authority-switch-receipt/v1",
            "from": previous_authority,
            "to": target,
            "pointer_before_sha256": pointer_before_sha256,
            "semantic_registry_sha256": m7_sha256,
            "single_writable_authority": True,
            "dual_write": False,
        },
    }
    if runtime_pointer_sha256 is not None:
        record["runtime_pointer_sha256"] = runtime_pointer_sha256
    if protocol_activation is not None:
        record["protocol_activation"] = protocol_activation
    return record


def _commit_record(
    repo: pathlib.Path,
    record: dict[str, Any],
    expected_pointer_sha256: str | None,
) -> dict[str, Any]:
    record_bytes = canonical(record)
    record_sha = sha256(record_bytes)
    write_immutable(_record_path(repo, record_sha), record_bytes)
    pointer = {
        "schema_version": "yuan.authority-current/v1",
        "record_sha256": record_sha,
    }
    pointer_path = repo / CURRENT_PATH
    atomic_write(pointer_path, canonical(pointer), expected_pointer_sha256)
    return {
        **record["receipt"],
        "revision": record["revision"],
        "record_sha256": record_sha,
        "pointer_after_sha256": file_sha256(pointer_path),
        "m7_semantic_registry_sha256": record["m7_semantic_registry_sha256"],
    }


def initialize_authority(
    repo_root: pathlib.Path,
    *,
    legacy_snapshot_sha256: str,
    m7_approval: pathlib.Path,
    expected_m7_sha256: str,
) -> str:
    repo = pathlib.Path(repo_root).resolve()
    if (repo / CURRENT_PATH).exists():
        raise AuthorityError("authority is already initialized")
    _approved(m7_approval, expected_m7_sha256)
    runtime_manifest = verify_runtime(repo)
    if runtime_manifest["legacy_snapshot_sha256"] != legacy_snapshot_sha256:
        raise AuthorityError("legacy/runtime snapshot mismatch")
    record = _new_record(
        revision=1,
        target="legacy",
        previous_authority=None,
        previous_record_sha256=None,
        legacy_snapshot_sha256=legacy_snapshot_sha256,
        runtime_snapshot_sha256=file_sha256(
            repo / runtime_manifest["runtime_root"] / "runtime-manifest.json"
        ),
        m7_sha256=expected_m7_sha256,
        pointer_before_sha256=None,
    )
    return _commit_record(repo, record, None)["pointer_after_sha256"]


def verify_authority(repo_root: pathlib.Path) -> dict[str, Any]:
    repo = pathlib.Path(repo_root).resolve()
    current = load_current(repo)
    runtime = verify_runtime(repo)
    record = current["record"]
    runtime_manifest_path = repo / runtime["runtime_root"] / "runtime-manifest.json"
    if (
        record.get("runtime_snapshot_sha256") != file_sha256(runtime_manifest_path)
        or record.get("runtime_root") != runtime["runtime_root"]
        or (
            "runtime_pointer_sha256" in record
            and record["runtime_pointer_sha256"]
            != runtime["active_run_pointer_sha256"]
        )
    ):
        raise AuthorityError("authority/runtime snapshot binding mismatch")
    if record.get("authority") == "core" and runtime["active_run_pointer"] is not None:
        from yuan_activation import verify_activation_descriptor

        if record.get("protocol_activation") != verify_activation_descriptor(repo):
            raise AuthorityError("authority/Core activation binding mismatch")
    seen: set[str] = set()
    expected_revision = record.get("revision")
    record_sha = current["record_sha256"]
    while True:
        if record_sha in seen:
            raise AuthorityError("authority record history cycle")
        seen.add(record_sha)
        if (
            record.get("schema_version") != "yuan.authority-record/v1"
            or record.get("revision") != expected_revision
            or record.get("m7_semantic_registry_sha256")
            != current["record"]["m7_semantic_registry_sha256"]
        ):
            raise AuthorityError("authority record history mismatch")
        previous = record.get("previous_record_sha256")
        if previous is None:
            break
        path = _record_path(repo, previous)
        try:
            payload = path.read_bytes()
            record = json.loads(payload.decode("utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as error:
            raise AuthorityError("authority record history missing") from error
        if sha256(payload) != previous:
            raise AuthorityError("authority record history content mismatch")
        record_sha = previous
        expected_revision -= 1
    if expected_revision != 1:
        raise AuthorityError("authority history does not reach revision 1")
    return {
        "status": "PASS",
        "authority": current["record"]["authority"],
        "revision": current["record"]["revision"],
        "history_length": len(seen),
        "runtime_immutable_files": len(runtime["immutable_files"]),
        "m7_semantic_registry_sha256": current["record"][
            "m7_semantic_registry_sha256"
        ],
    }


def switch_authority(
    repo_root: pathlib.Path,
    *,
    target: str,
    expected_pointer_sha256: str,
    m7_approval: pathlib.Path,
    expected_m7_sha256: str,
) -> dict[str, Any]:
    if target not in {"legacy", "core"}:
        raise AuthorityError("authority target must be legacy or core")
    repo = pathlib.Path(repo_root).resolve()
    _approved(m7_approval, expected_m7_sha256)
    verified = verify_authority(repo)
    current = load_current(repo)
    if current["pointer_sha256"] != expected_pointer_sha256:
        raise AuthorityError("authority pointer CAS mismatch")
    if verified["authority"] == target:
        raise AuthorityError("authority target is already active")
    runtime = verify_runtime(repo)
    record = _new_record(
        revision=current["record"]["revision"] + 1,
        target=target,
        previous_authority=current["record"]["authority"],
        previous_record_sha256=current["record_sha256"],
        legacy_snapshot_sha256=runtime["legacy_snapshot_sha256"],
        runtime_snapshot_sha256=file_sha256(
            repo / runtime["runtime_root"] / "runtime-manifest.json"
        ),
        runtime_root=runtime["runtime_root"],
        runtime_pointer_sha256=runtime["active_run_pointer_sha256"],
        protocol_activation=current["record"].get("protocol_activation"),
        m7_sha256=expected_m7_sha256,
        pointer_before_sha256=expected_pointer_sha256,
    )
    return _commit_record(repo, record, expected_pointer_sha256)


def advance_core_runtime(
    repo_root: pathlib.Path,
    *,
    expected_pointer_sha256: str,
    protocol_activation: dict[str, Any] | None = None,
) -> dict[str, Any]:
    repo = pathlib.Path(repo_root).resolve()
    current = load_current(repo)
    if current["pointer_sha256"] != expected_pointer_sha256:
        raise AuthorityError("authority pointer CAS mismatch")
    if current["record"].get("authority") != "core":
        raise AuthorityError("Core runtime cannot advance while inactive")
    runtime = verify_runtime(repo)
    activation = protocol_activation or current["record"].get("protocol_activation")
    if not isinstance(activation, dict):
        raise AuthorityError("Core runtime activation binding is missing")
    record = _new_record(
        revision=current["record"]["revision"] + 1,
        target="core",
        previous_authority="core",
        previous_record_sha256=current["record_sha256"],
        legacy_snapshot_sha256=current["record"]["legacy_snapshot_sha256"],
        runtime_snapshot_sha256=file_sha256(
            repo / runtime["runtime_root"] / "runtime-manifest.json"
        ),
        runtime_root=runtime["runtime_root"],
        runtime_pointer_sha256=runtime["active_run_pointer_sha256"],
        protocol_activation=activation,
        m7_sha256=current["record"]["m7_semantic_registry_sha256"],
        pointer_before_sha256=expected_pointer_sha256,
    )
    return _commit_record(repo, record, expected_pointer_sha256)


def assert_write_allowed(
    repo_root: pathlib.Path,
    writer_lane: str,
    target: str | pathlib.Path,
    expected_before_sha256: str | None,
) -> pathlib.Path:
    repo_input = pathlib.Path(repo_root).absolute()
    repo = repo_input.resolve()
    current = load_current(repo)["record"]
    if current["authority"] != writer_lane:
        raise AuthorityError(f"{writer_lane} writer is inactive")
    relative_target = pathlib.Path(target)
    target_path = (repo / relative_target).resolve()
    root = (repo / (RUNTIME_ROOT if writer_lane == "core" else LEGACY_ROOT)).resolve()
    if not inside(target_path, root):
        raise AuthorityError("writer target escapes active authority root")
    if writer_lane == "core":
        relative = target_path.relative_to(root)
        if relative.as_posix() in {"runtime-manifest.json", "active-run.json"}:
            if not target_path.is_file() or expected_before_sha256 is None:
                raise AuthorityError("runtime control write requires CAS")
            if file_sha256(target_path) != expected_before_sha256:
                raise AuthorityError("runtime control CAS mismatch")
        elif relative.parts and relative.parts[0] == "runs":
            raise AuthorityError("active-run records require an atomic transaction")
        elif relative.parts and relative.parts[0] in IMMUTABLE_RUNTIME_AREAS:
            if target_path.exists():
                raise AuthorityError("immutable runtime record cannot be overwritten")
        elif relative.as_posix() == "run-memory.json":
            if not target_path.is_file() or expected_before_sha256 is None:
                raise AuthorityError("run-memory write requires CAS")
            if file_sha256(target_path) != expected_before_sha256:
                raise AuthorityError("run-memory CAS mismatch")
        else:
            raise AuthorityError("core writer target is not a declared runtime path")
    elif target_path.exists():
        if expected_before_sha256 is None or file_sha256(target_path) != expected_before_sha256:
            raise AuthorityError("legacy writer CAS mismatch")
    elif expected_before_sha256 is not None:
        raise AuthorityError("legacy writer CAS target missing")
    return repo_input / relative_target
