"""Crash-safe generation transaction for immutable Yuan runtime appends."""

from __future__ import annotations

import copy
import json
import pathlib
import shutil
from typing import Any

from yuan_authority import (
    AuthorityError,
    advance_core_runtime,
    load_current,
    verify_authority,
)
from yuan_runtime_state import (
    ACTIVE_RUN_PATH,
    RUNS_ROOT,
    artifact_binding_sha256,
    atomic_write,
    canonical,
    file_sha256,
    rebuild_runtime_memory,
    resolve_runtime_root,
    seal_runtime,
    sha256,
    validate_runtime_evidence,
    verify_runtime_at,
    write_immutable,
)


TRANSACTIONS = pathlib.PurePosixPath(".yuan/authority/transactions")


class InjectedCrash(RuntimeError):
    """Test-only crash boundary after a durable transaction phase."""

    def __init__(self, transaction_id: str):
        super().__init__(transaction_id)
        self.transaction_id = transaction_id


def canonical_digest(
    value: Any,
    *,
    omitted_paths: tuple[tuple[str, ...], ...] = (),
) -> str:
    result = copy.deepcopy(value)
    for parts in omitted_paths:
        cursor = result
        for part in parts[:-1]:
            cursor = cursor[part]
        cursor.pop(parts[-1], None)
    return sha256(
        json.dumps(
            result,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
    )


def _journal_path(repo: pathlib.Path, transaction_id: str) -> pathlib.Path:
    if (
        len(transaction_id) != 64
        or any(token not in "0123456789abcdef" for token in transaction_id)
    ):
        raise AuthorityError("transaction id is invalid")
    return repo / TRANSACTIONS / f"{transaction_id}.json"


def _update_journal(
    path: pathlib.Path,
    journal: dict[str, Any],
    expected_sha256: str | None,
) -> str:
    atomic_write(path, canonical(journal), expected_sha256)
    return file_sha256(path)


def _validate_append(
    repo: pathlib.Path,
    runtime: pathlib.Path,
    attempt: dict[str, Any],
    evidence: dict[str, Any],
) -> None:
    work = json.loads(next((runtime / "contracts").glob("*.json")).read_text())
    attempt_count = len(list((runtime / "attempts").glob("*.json")))
    evidence_count = len(list((runtime / "evidence").glob("*.json")))
    if (
        attempt.get("sequence") != attempt_count + 1
        or evidence.get("sequence") != evidence_count + 1
        or attempt.get("work_binding") != work.get("revision")
        or evidence.get("work_binding") != work.get("revision")
        or evidence.get("source_attempt_id") != attempt.get("attempt_id")
        or attempt.get("evidence_ids") != [evidence.get("evidence_id")]
        or evidence.get("immutable_digest")
        != canonical_digest(evidence, omitted_paths=(("immutable_digest",),))
    ):
        raise AuthorityError("append records violate immutable sequence/bindings")
    validate_runtime_evidence(repo, runtime, attempt, evidence)


def _build_generation(
    repo: pathlib.Path,
    runtime: pathlib.Path,
    transaction_id: str,
    attempt: dict[str, Any],
    evidence: dict[str, Any],
    previous_manifest: dict[str, Any],
) -> tuple[pathlib.Path, dict[str, Any]]:
    base_id = json.loads(next((runtime / "contracts").glob("*.json")).read_text())[
        "work_id"
    ]
    generation_id = (
        f"{base_id}-g{attempt['sequence']:04d}-{transaction_id[:12]}"
    )
    final = repo / RUNS_ROOT / generation_id
    pending = repo / RUNS_ROOT / f".pending-{transaction_id}"
    if final.exists() or pending.exists():
        raise AuthorityError("runtime transaction generation already exists")
    for area in ("contracts", "attempts", "evidence"):
        shutil.copytree(runtime / area, pending / area)
    write_immutable(
        pending / "attempts" / f"{attempt['sequence']:04d}.json",
        canonical(attempt),
    )
    write_immutable(
        pending / "evidence" / f"{evidence['sequence']:04d}.json",
        canonical(evidence),
    )
    atomic_write(
        pending / "run-memory.json",
        canonical(rebuild_runtime_memory(repo, pending)),
        None,
    )
    manifest = seal_runtime(
        repo,
        pending,
        legacy_snapshot_sha256=previous_manifest["legacy_snapshot_sha256"],
        source_projection_sha256=file_sha256(
            runtime / "runtime-manifest.json"
        ),
    )
    verify_runtime_at(repo, pending)
    pending.rename(final)
    return final, manifest


def append_runtime_transaction(
    repo_root: pathlib.Path,
    attempt: dict[str, Any],
    evidence: dict[str, Any],
    *,
    expected_authority_pointer_sha256: str,
    expected_active_run_pointer_sha256: str,
    failure_after: str | None = None,
) -> dict[str, Any]:
    repo = pathlib.Path(repo_root).resolve()
    verified = verify_authority(repo)
    if verified["authority"] != "core":
        raise AuthorityError("Core runtime is inactive")
    current = load_current(repo)
    runtime, active_pointer, active_sha = resolve_runtime_root(repo)
    if (
        current["pointer_sha256"] != expected_authority_pointer_sha256
        or active_pointer is None
        or active_sha != expected_active_run_pointer_sha256
    ):
        raise AuthorityError("runtime transaction CAS mismatch")
    try:
        _validate_append(repo, runtime, attempt, evidence)
    except AuthorityError as error:
        return {
            "schema_version": "yuan.runtime-transaction-rejection/v1",
            "state": "REJECTED",
            "reason": "EVIDENCE_TRUST_VALIDATION_FAILED",
            "detail": str(error),
        }
    transaction_id = sha256(
        canonical(
            {
                "authority": expected_authority_pointer_sha256,
                "active_run": expected_active_run_pointer_sha256,
                "attempt": attempt,
                "evidence": evidence,
            }
        )
    )
    journal_path = _journal_path(repo, transaction_id)
    if journal_path.exists():
        raise AuthorityError("runtime transaction already prepared")
    previous_manifest = verify_runtime_at(repo, runtime)
    generation_id = (
        f"{json.loads(next((runtime / 'contracts').glob('*.json')).read_text())['work_id']}"
        f"-g{attempt['sequence']:04d}-{transaction_id[:12]}"
    )
    journal = {
        "schema_version": "yuan.runtime-transaction/v1",
        "transaction_id": transaction_id,
        "state": "PREPARED",
        "authority_pointer_before_sha256": expected_authority_pointer_sha256,
        "active_run_before_sha256": expected_active_run_pointer_sha256,
        "runtime_root": f"{RUNS_ROOT.as_posix()}/{generation_id}",
    }
    journal_sha = _update_journal(journal_path, journal, None)
    generation, manifest = _build_generation(
        repo, runtime, transaction_id, attempt, evidence, previous_manifest
    )
    journal.update(
        {
            "state": "GENERATION_READY",
            "manifest_sha256": file_sha256(
                generation / "runtime-manifest.json"
            ),
        }
    )
    journal_sha = _update_journal(journal_path, journal, journal_sha)
    if failure_after == "generation":
        raise InjectedCrash(transaction_id)
    return _finish_transaction(repo, journal_path, journal, journal_sha, failure_after)


def _finish_transaction(
    repo: pathlib.Path,
    journal_path: pathlib.Path,
    journal: dict[str, Any],
    journal_sha: str,
    failure_after: str | None = None,
) -> dict[str, Any]:
    generation = repo / journal["runtime_root"]
    verify_runtime_at(repo, generation)
    new_active = {
        "schema_version": "yuan.active-run/v1",
        "run_id": generation.name,
        "runtime_root": journal["runtime_root"],
        "manifest_sha256": journal["manifest_sha256"],
    }
    active_path = repo / ACTIVE_RUN_PATH
    new_active_sha = sha256(canonical(new_active))
    actual_active = file_sha256(active_path) if active_path.is_file() else None
    if actual_active == journal["active_run_before_sha256"]:
        atomic_write(
            active_path,
            canonical(new_active),
            journal["active_run_before_sha256"],
        )
    elif actual_active != new_active_sha:
        raise AuthorityError("active-run CAS was won by another transaction")
    journal.update({"state": "ACTIVE_POINTER", "active_run_after_sha256": new_active_sha})
    journal_sha = _update_journal(journal_path, journal, journal_sha)
    if failure_after == "active-pointer":
        raise InjectedCrash(journal["transaction_id"])
    current = load_current(repo)
    if current["pointer_sha256"] == journal["authority_pointer_before_sha256"]:
        receipt = advance_core_runtime(
            repo,
            expected_pointer_sha256=journal["authority_pointer_before_sha256"],
            protocol_activation=journal.get("protocol_activation"),
        )
    elif current["record"].get("runtime_root") == journal["runtime_root"]:
        receipt = {
            "record_sha256": current["record_sha256"],
            "pointer_after_sha256": current["pointer_sha256"],
        }
    else:
        raise AuthorityError("authority CAS was won by another transaction")
    journal.update({"state": "COMMITTED", "authority_receipt": receipt})
    _update_journal(journal_path, journal, journal_sha)
    verify_authority(repo)
    return journal


def recover_runtime_transaction(
    repo_root: pathlib.Path,
    transaction_id: str,
) -> dict[str, Any]:
    repo = pathlib.Path(repo_root).resolve()
    path = _journal_path(repo, transaction_id)
    try:
        payload = path.read_bytes()
        journal = json.loads(payload.decode("utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise AuthorityError("transaction journal missing or invalid") from error
    if journal.get("transaction_id") != transaction_id:
        raise AuthorityError("transaction journal id mismatch")
    if journal.get("state") == "COMMITTED":
        verify_authority(repo)
        return journal
    return _finish_transaction(repo, path, journal, sha256(payload))


def activate_runtime_generation(
    repo_root: pathlib.Path,
    runtime_root: pathlib.Path,
    *,
    expected_authority_pointer_sha256: str,
    protocol_activation: dict[str, Any],
) -> dict[str, Any]:
    repo = pathlib.Path(repo_root).resolve()
    current = load_current(repo)
    if (
        current["pointer_sha256"] != expected_authority_pointer_sha256
        or current["record"].get("authority") != "core"
        or (repo / ACTIVE_RUN_PATH).exists()
    ):
        raise AuthorityError("successor activation CAS mismatch")
    runtime = pathlib.Path(runtime_root).resolve()
    manifest = verify_runtime_at(repo, runtime)
    transaction_id = sha256(
        canonical(
            {
                "authority": expected_authority_pointer_sha256,
                "runtime_root": runtime.relative_to(repo).as_posix(),
                "manifest": file_sha256(runtime / "runtime-manifest.json"),
                "activation": protocol_activation,
            }
        )
    )
    journal_path = _journal_path(repo, transaction_id)
    journal = {
        "schema_version": "yuan.runtime-transaction/v1",
        "transaction_id": transaction_id,
        "state": "GENERATION_READY",
        "authority_pointer_before_sha256": expected_authority_pointer_sha256,
        "active_run_before_sha256": None,
        "runtime_root": runtime.relative_to(repo).as_posix(),
        "manifest_sha256": file_sha256(runtime / "runtime-manifest.json"),
        "protocol_activation": protocol_activation,
    }
    journal_sha = _update_journal(journal_path, journal, None)
    return _finish_transaction(repo, journal_path, journal, journal_sha)


def replace_runtime_generation(
    repo_root: pathlib.Path,
    runtime_root: pathlib.Path,
    *,
    expected_authority_pointer_sha256: str,
    expected_active_run_pointer_sha256: str,
    protocol_activation: dict[str, Any],
    failure_after: str | None = None,
) -> dict[str, Any]:
    """CAS-switch to a sealed successor Work and advance Core authority once."""
    repo = pathlib.Path(repo_root).resolve()
    current = load_current(repo)
    _, active_pointer, active_sha = resolve_runtime_root(repo)
    if (
        current["pointer_sha256"] != expected_authority_pointer_sha256
        or current["record"].get("authority") != "core"
        or active_pointer is None
        or active_sha != expected_active_run_pointer_sha256
    ):
        raise AuthorityError("successor replacement CAS mismatch")
    runtime = pathlib.Path(runtime_root).resolve()
    verify_runtime_at(repo, runtime)
    manifest_sha = file_sha256(runtime / "runtime-manifest.json")
    transaction_id = sha256(
        canonical(
            {
                "authority": expected_authority_pointer_sha256,
                "active_run": expected_active_run_pointer_sha256,
                "runtime_root": runtime.relative_to(repo).as_posix(),
                "manifest": manifest_sha,
                "activation": protocol_activation,
            }
        )
    )
    journal_path = _journal_path(repo, transaction_id)
    journal = {
        "schema_version": "yuan.runtime-transaction/v1",
        "transaction_id": transaction_id,
        "state": "GENERATION_READY",
        "authority_pointer_before_sha256": expected_authority_pointer_sha256,
        "active_run_before_sha256": expected_active_run_pointer_sha256,
        "runtime_root": runtime.relative_to(repo).as_posix(),
        "manifest_sha256": manifest_sha,
        "protocol_activation": protocol_activation,
    }
    journal_sha = _update_journal(journal_path, journal, None)
    return _finish_transaction(
        repo, journal_path, journal, journal_sha, failure_after
    )
