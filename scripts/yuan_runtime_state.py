"""Sealed Yuan Core runtime storage primitives."""

from __future__ import annotations

import hashlib
import json
import os
import pathlib
import re
import sys
import tempfile
from datetime import datetime, timezone
from typing import Any


RUNTIME_ROOT = pathlib.PurePosixPath(".yuan-run")
ACTIVE_RUN_PATH = RUNTIME_ROOT / "active-run.json"
RUNS_ROOT = RUNTIME_ROOT / "runs"
IMMUTABLE_RUNTIME_AREAS = ("contracts", "attempts", "evidence")
SHA256 = re.compile(r"^[0-9a-f]{64}$")


class AuthorityError(RuntimeError):
    """Fail-closed authority, CAS, or immutable-history error."""


def canonical(value: Any) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def file_sha256(path: pathlib.Path) -> str:
    return sha256(path.read_bytes())


def inside(path: pathlib.Path, root: pathlib.Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except ValueError:
        return False


def atomic_write(
    path: pathlib.Path,
    payload: bytes,
    expected_sha256: str | None,
) -> None:
    if path.exists():
        if not path.is_file():
            raise AuthorityError(f"CAS target is not a file: {path}")
        actual = file_sha256(path)
        if expected_sha256 is None or actual != expected_sha256:
            raise AuthorityError(f"CAS mismatch: {path}")
    elif expected_sha256 is not None:
        raise AuthorityError(f"CAS target missing: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.", dir=path.parent
    )
    temporary = pathlib.Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


def write_immutable(path: pathlib.Path, payload: bytes) -> None:
    if path.exists():
        if not path.is_file() or path.read_bytes() != payload:
            raise AuthorityError(f"immutable record collision: {path}")
        return
    atomic_write(path, payload, None)


def immutable_runtime_files(runtime_root: pathlib.Path) -> dict[str, str]:
    result: dict[str, str] = {}
    for area in IMMUTABLE_RUNTIME_AREAS:
        root = runtime_root / area
        if not root.is_dir():
            raise AuthorityError(f"runtime immutable area missing: {area}")
        for path in sorted(root.rglob("*")):
            if not path.is_file():
                continue
            try:
                json.loads(path.read_text(encoding="utf-8"))
            except (OSError, UnicodeError, json.JSONDecodeError) as error:
                raise AuthorityError(
                    f"runtime immutable JSON invalid: {path}"
                ) from error
            result[path.relative_to(runtime_root).as_posix()] = file_sha256(path)
    if not result:
        raise AuthorityError("runtime has no immutable Work/Attempt/Evidence")
    return result


def resolve_runtime_root(
    repo_root: pathlib.Path,
) -> tuple[pathlib.Path, dict[str, Any] | None, str | None]:
    repo = pathlib.Path(repo_root).resolve()
    pointer_path = repo / ACTIVE_RUN_PATH
    if not pointer_path.exists():
        return repo / RUNTIME_ROOT, None, None
    try:
        pointer_bytes = pointer_path.read_bytes()
        pointer = json.loads(pointer_bytes.decode("utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise AuthorityError("active-run pointer is missing or invalid") from error
    if (
        pointer.get("schema_version") != "yuan.active-run/v1"
        or not isinstance(pointer.get("run_id"), str)
        or pointer.get("runtime_root")
        != f"{RUNS_ROOT.as_posix()}/{pointer.get('run_id')}"
        or not SHA256.fullmatch(pointer.get("manifest_sha256", ""))
    ):
        raise AuthorityError("active-run pointer fields are invalid")
    runtime = (repo / pointer["runtime_root"]).resolve()
    if not inside(runtime, (repo / RUNS_ROOT).resolve()):
        raise AuthorityError("active-run pointer escapes runs root")
    manifest = runtime / "runtime-manifest.json"
    if not manifest.is_file() or file_sha256(manifest) != pointer["manifest_sha256"]:
        raise AuthorityError("active-run manifest binding mismatch")
    return runtime, pointer, sha256(pointer_bytes)


def runtime_documents(
    repo_root: pathlib.Path,
    runtime_root: pathlib.Path | None = None,
) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]]]:
    repo = pathlib.Path(repo_root).resolve()
    runtime = (
        pathlib.Path(runtime_root).resolve()
        if runtime_root is not None
        else resolve_runtime_root(repo)[0]
    )
    contracts = sorted((runtime / "contracts").glob("*.json"))
    if len(contracts) != 1:
        raise AuthorityError("runtime must contain exactly one active Work")

    def load_all(paths: list[pathlib.Path]) -> list[dict[str, Any]]:
        values = []
        for path in paths:
            try:
                value = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, UnicodeError, json.JSONDecodeError) as error:
                raise AuthorityError(f"runtime JSON invalid: {path}") from error
            if not isinstance(value, dict):
                raise AuthorityError(f"runtime JSON object required: {path}")
            values.append(value)
        return values

    work = load_all(contracts)[0]
    attempts = load_all(sorted((runtime / "attempts").glob("*.json")))
    evidence = load_all(sorted((runtime / "evidence").glob("*.json")))
    if not attempts or not evidence:
        raise AuthorityError("runtime history is empty")
    return work, attempts, evidence


def rebuild_runtime_memory(
    repo_root: pathlib.Path,
    runtime_root: pathlib.Path | None = None,
) -> dict[str, Any]:
    repo = pathlib.Path(repo_root).resolve()
    work, attempts, evidence = runtime_documents(repo, runtime_root)
    latest = evidence[-1]
    artifact_binding = latest.get("artifact_binding", {})
    environment_binding = latest.get("environment_binding", {})
    if any(
        not isinstance(value, str) or not value
        for value in (
            artifact_binding.get("scope"),
            artifact_binding.get("sha256"),
            environment_binding.get("id"),
            environment_binding.get("fingerprint"),
        )
    ):
        raise AuthorityError("runtime rebuild inputs are ambiguous")
    core = repo / ".yuan/core/0.1"
    if not core.is_dir():
        raise AuthorityError("Core 0.1 implementation is missing")
    core_text = str(core)
    sys.path.insert(0, core_text)
    core_modules = (
        "authorization_semantics",
        "completion_semantics",
        "conformance",
        "document_validation",
        "replay_pending",
        "replay_trust",
        "runtime_replay",
        "trust_semantics",
    )
    for module_name in core_modules:
        sys.modules.pop(module_name, None)
    try:
        import conformance  # type: ignore
        return conformance.rebuild_run_memory(
            work,
            attempts,
            evidence,
            current_artifact_sha256=artifact_binding["sha256"],
            environment_id=environment_binding["id"],
            environment_fingerprint=environment_binding["fingerprint"],
            trusted_now=datetime(2100, 1, 1, tzinfo=timezone.utc),
        )
    except (ImportError, OSError) as error:
        raise AuthorityError("Core replay implementation is unavailable") from error
    finally:
        if sys.path[0] == core_text:
            sys.path.pop(0)


def seal_runtime(
    repo_root: pathlib.Path,
    runtime_root: pathlib.Path,
    *,
    legacy_snapshot_sha256: str,
    source_projection_sha256: str,
) -> dict[str, Any]:
    repo = pathlib.Path(repo_root).resolve()
    runtime = pathlib.Path(runtime_root).resolve()
    legacy_root = (repo / RUNTIME_ROOT).resolve()
    runs_root = (repo / RUNS_ROOT).resolve()
    if not inside(runtime, repo) or not (
        runtime == legacy_root
        or (
            inside(runtime, runs_root)
            and runtime.parent == runs_root
            and runtime.name not in {"", ".", ".."}
        )
    ):
        raise AuthorityError("runtime root must be .yuan-run or one declared run")
    if not SHA256.fullmatch(legacy_snapshot_sha256):
        raise AuthorityError("legacy snapshot SHA-256 is invalid")
    if not SHA256.fullmatch(source_projection_sha256):
        raise AuthorityError("source projection SHA-256 is invalid")
    memory = runtime / "run-memory.json"
    if not memory.is_file():
        raise AuthorityError("rebuildable run-memory.json is missing")
    try:
        stored_memory = json.loads(memory.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise AuthorityError("run-memory.json is invalid") from error
    if stored_memory != rebuild_runtime_memory(repo, runtime):
        raise AuthorityError("run-memory.json is not a deterministic rebuild")
    manifest = {
        "schema_version": "yuan.runtime-seal/v1",
        "legacy_snapshot_sha256": legacy_snapshot_sha256,
        "source_projection_sha256": source_projection_sha256,
        "immutable_files": immutable_runtime_files(runtime),
        "memory_path": "run-memory.json",
        "memory_rebuildable": True,
    }
    path = runtime / "runtime-manifest.json"
    if path.exists():
        raise AuthorityError("runtime is already sealed")
    atomic_write(path, canonical(manifest), None)
    return manifest


def verify_runtime_at(
    repo_root: pathlib.Path,
    runtime_root: pathlib.Path,
) -> dict[str, Any]:
    repo = pathlib.Path(repo_root).resolve()
    runtime = pathlib.Path(runtime_root).resolve()
    if not inside(runtime, repo):
        raise AuthorityError("runtime verification target escapes repository")
    manifest_path = runtime / "runtime-manifest.json"
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise AuthorityError("runtime manifest missing or invalid") from error
    if manifest.get("schema_version") != "yuan.runtime-seal/v1":
        raise AuthorityError("runtime manifest schema is invalid")
    if immutable_runtime_files(runtime) != manifest.get("immutable_files"):
        raise AuthorityError("runtime immutable content mismatch")
    memory = runtime / manifest.get("memory_path", "")
    try:
        stored_memory = json.loads(memory.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise AuthorityError("runtime memory is not rebuildable JSON") from error
    if stored_memory != rebuild_runtime_memory(repo, runtime):
        raise AuthorityError("runtime memory does not match immutable history")
    return manifest


def verify_runtime(repo_root: pathlib.Path) -> dict[str, Any]:
    repo = pathlib.Path(repo_root).resolve()
    runtime, pointer, pointer_sha256 = resolve_runtime_root(repo)
    manifest = verify_runtime_at(repo, runtime)
    return {
        **manifest,
        "runtime_root": runtime.relative_to(repo).as_posix(),
        "active_run_pointer": pointer,
        "active_run_pointer_sha256": pointer_sha256,
    }
