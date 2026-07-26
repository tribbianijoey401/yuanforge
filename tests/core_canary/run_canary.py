#!/usr/bin/env python3
"""Execute the M5 low-impact Work through the approved Yuan Core reference Port."""

from __future__ import annotations

import argparse
import copy
import dataclasses
import hashlib
import json
import os
import pathlib
import platform
import sys
import tempfile
from datetime import datetime, timezone
from typing import Any


REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
CORE_ROOT = REPO_ROOT / ".yuan" / "core" / "0.1"
VALIDATOR_PATH = pathlib.Path(__file__).with_name("canary_validator.py")
AUTHORITY_PATH = REPO_ROOT / ".yuan-shadow" / "authority.json"
LEGACY_STATE_PATHS = (
    REPO_ROOT / "docs" / "PROGRESS.md",
    REPO_ROOT / "docs" / "20260726-yuan-core-01-upgrade" / "TASK_BOARD.md",
    REPO_ROOT / "docs" / "20260726-yuan-core-01-upgrade" / "SESSION_LOG.md",
    REPO_ROOT / "docs" / "events" / "20260726" / "events.jsonl",
)
CANARY_PAYLOAD = "Yuan Core 0.1 M5 canary: deterministic artifact.\n".encode("utf-8")
ENVIRONMENT_ID = "yuan-reference-port-python-v1"
VALIDATOR_REVISION = "m5-1"
TRUST_ROOT_ID = "task-008-independent-tester"
FIXED_NOW = datetime(2026, 7, 27, 1, 0, tzinfo=timezone.utc)

sys.path.insert(0, str(CORE_ROOT))
import conformance  # noqa: E402
from command_sandbox import PYTHON_PROFILE  # noqa: E402
from reference_port import ReferencePort  # noqa: E402


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _sha256_file(path: pathlib.Path) -> str:
    return _sha256_bytes(path.read_bytes())


def _legacy_state_hashes() -> dict[str, str]:
    return {
        path.relative_to(REPO_ROOT).as_posix(): _sha256_file(path)
        for path in LEGACY_STATE_PATHS
    }


def _canonical_bytes(value: Any) -> bytes:
    return (
        json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
        + "\n"
    ).encode("utf-8")


def _atomic_bytes(
    path: pathlib.Path,
    data: bytes,
    *,
    expected_sha256: str | None,
) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    before = _sha256_file(path) if path.is_file() else None
    if before != expected_sha256:
        raise RuntimeError(f"CAS mismatch for {path}: expected {expected_sha256}, got {before}")
    descriptor, temporary_name = tempfile.mkstemp(
        dir=path.parent, prefix=f".{path.name}.", suffix=".tmp"
    )
    temporary = pathlib.Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        current = _sha256_file(path) if path.is_file() else None
        if current != before:
            raise RuntimeError(f"CAS changed during write for {path}")
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()
    return _sha256_bytes(data)


def _atomic_json(
    path: pathlib.Path,
    value: dict[str, Any],
    *,
    expected_sha256: str | None,
) -> str:
    return _atomic_bytes(path, _canonical_bytes(value), expected_sha256=expected_sha256)


def _binding(binding_id: str, revision: str, digest: str) -> dict[str, str]:
    return {"id": binding_id, "revision": revision, "sha256": digest}


def _environment_fingerprint() -> str:
    return conformance.canonical_digest(
        {
            "python": sys.version,
            "implementation": platform.python_implementation(),
            "platform": platform.platform(),
            "port_profile": PYTHON_PROFILE,
        }
    )


def _harness_binding() -> dict[str, str]:
    files = (
        "authorization_semantics.py",
        "command_sandbox.py",
        "completion_semantics.py",
        "conformance.py",
        "document_validation.py",
        "port_types.py",
        "reference_port.py",
        "replay_trust.py",
        "runtime_replay.py",
        "schema_runtime.py",
        "trust_semantics.py",
    )
    digest = conformance.canonical_digest(
        [{"path": name, "sha256": _sha256_file(CORE_ROOT / name)} for name in files]
    )
    return _binding("yuan.core.reference-harness", "0.1.0-candidate", digest)


def _build_work(output_root: pathlib.Path) -> dict[str, Any]:
    relative_root = output_root.relative_to(REPO_ROOT).as_posix()
    artifact_scope = f"{relative_root}/artifact.txt"
    environment_fingerprint = _environment_fingerprint()
    validator_hash = _sha256_file(VALIDATOR_PATH)
    protocol_hash = _sha256_file(CORE_ROOT / "protocol.md")
    harness_binding = _harness_binding()
    work_id = "WORK-yuan-core-m5-canary"
    work: dict[str, Any] = {
        "schema_version": "yuan.work-contract/v1",
        "work_id": work_id,
        "revision": _binding(work_id, "1", "0" * 64),
        "protocol_binding": _binding(
            "yuan.core.protocol", "0.1.0-candidate", protocol_hash
        ),
        "harness_binding": harness_binding,
        "intent": {
            "goal": "Create and independently verify one deterministic, reversible repository-local artifact through the reference Port.",
            "non_goals": [
                "Do not switch runtime authority.",
                "Do not modify Yuan Core implementation.",
                "Do not write outside the M5 canary evidence directory.",
            ],
            "constraints": [
                "The artifact payload is fixed UTF-8 bytes.",
                "The verifier is pre-bound by immutable SHA-256.",
                "The M4 authority pointer must remain byte-identical and legacy-owned.",
            ],
        },
        "scope": {
            "allowed_paths": [relative_root],
            "denied_paths": [
                ".yuan/core",
                ".yuan-shadow",
                "AGENTS.md",
                "docs/PROGRESS.md",
            ],
            "side_effect_classes": ["none", "filesystem", "command"],
        },
        "authorization": {
            "default": "deny",
            "grants": [
                {
                    "id": "GRANT-m5-canary-local",
                    "action_types": ["file-write", "command", "verify"],
                    "side_effect_classes": ["filesystem", "command", "none"],
                    "scopes": [relative_root],
                    "high_impact": False,
                    "expires_at": "2026-07-28T00:00:00+00:00",
                    "max_uses": 3,
                }
            ],
        },
        "budget": {
            "ticks": 3,
            "tool_calls": 4,
            "strategies": 2,
            "command_seconds": 10,
        },
        "acceptance_criteria": [
            {
                "id": "AC-CANARY-ARTIFACT",
                "type": "contract",
                "required": True,
                "predicate": "artifact bytes and digest exactly equal the Work-bound payload while the legacy authority pointer remains unchanged",
                "artifact_scope": artifact_scope,
                "verifier_binding": {
                    "id": "yuan.m5.canary-validator",
                    "revision": VALIDATOR_REVISION,
                    "sha256": validator_hash,
                    "trust_root_id": TRUST_ROOT_ID,
                    "environment_ids": [ENVIRONMENT_ID],
                    "environment_fingerprints": {
                        ENVIRONMENT_ID: environment_fingerprint
                    },
                    "minimum_assertions": 3,
                },
            }
        ],
        "safety_invariants": [
            {
                "id": "SAFE-LEGACY-AUTHORITY",
                "predicate": "the M4 authority pointer is byte-identical and still selects legacy",
            }
        ],
    }
    work["revision"]["sha256"] = conformance.canonical_digest(
        work, omitted_paths=(("revision", "sha256"),)
    )
    return work


def _base_attempt(work: dict[str, Any], artifact_scope: str) -> dict[str, Any]:
    return {
        "schema_version": "yuan.attempt/v1",
        "attempt_id": "ATT-m5-canary-001",
        "work_binding": copy.deepcopy(work["revision"]),
        "protocol_binding": copy.deepcopy(work["protocol_binding"]),
        "harness_binding": copy.deepcopy(work["harness_binding"]),
        "sequence": 1,
        "strategy_fingerprint": conformance.canonical_digest(
            {
                "strategy": "reference-port-atomic-write-then-prebound-verify",
                "payload_sha256": _sha256_bytes(CANARY_PAYLOAD),
            }
        ),
        "relevant_inputs": [
            {
                "scope": artifact_scope,
                "sha256": _sha256_bytes(b""),
            }
        ],
        "hypothesis": {
            "claim": "The reference Port can atomically create the Work-bound artifact and the pre-bound independent validator will accept it.",
            "falsification": "The Port receipt, artifact bytes, validator result, authority invariant, or replay completion predicate does not match the Work.",
        },
        "action": {
            "type": "file-write",
            "mutating": True,
            "side_effect_class": "filesystem",
            "scope": artifact_scope,
            "authorization_grant_id": "GRANT-m5-canary-local",
            "high_impact": False,
            "self_modification": None,
        },
        "budget_charge": {
            "ticks": 1,
            "tool_calls": 2,
            "strategies": 1,
            "command_seconds": 2,
        },
        "journal": [],
        "side_effect_state": "PREPARED",
        "tool_receipt": None,
        "postcondition": None,
        "evidence_ids": ["EVD-m5-canary-001"],
        "outcome": "PENDING",
    }


def _journal_entry(ordinal: int, state: str, receipt_sha256: str | None) -> dict[str, Any]:
    return {
        "ordinal": ordinal,
        "state": state,
        "recorded_at": (
            FIXED_NOW.replace(minute=ordinal).isoformat()
        ),
        "receipt_sha256": receipt_sha256,
    }


def _validator_command(
    artifact_scope: str,
    authority_sha256: str,
) -> list[str]:
    validator_relative = VALIDATOR_PATH.relative_to(REPO_ROOT).as_posix()
    authority_relative = AUTHORITY_PATH.relative_to(REPO_ROOT).as_posix()
    bootstrap = (
        "import pathlib,sys;"
        "p=pathlib.Path(sys.argv[1]);"
        "sys.argv=[str(p),*sys.argv[2:]];"
        "g={'__name__':'__main__','__file__':str(p)};"
        "exec(compile(p.read_text(encoding='utf-8'),str(p),'exec'),g)"
    )
    return [
        str(pathlib.Path(sys.executable).resolve(strict=True)),
        "-c",
        bootstrap,
        validator_relative,
        artifact_scope,
        CANARY_PAYLOAD.hex(),
        authority_relative,
        authority_sha256,
    ]


def _evidence(
    work: dict[str, Any],
    attempt: dict[str, Any],
    artifact_sha256: str,
    command_receipt: dict[str, Any],
    validator_result: dict[str, Any],
) -> dict[str, Any]:
    verifier = work["acceptance_criteria"][0]["verifier_binding"]
    checks = validator_result["checks"]
    evidence: dict[str, Any] = {
        "schema_version": "yuan.evidence/v1",
        "evidence_id": "EVD-m5-canary-001",
        "sequence": 1,
        "work_binding": copy.deepcopy(work["revision"]),
        "ac_id": "AC-CANARY-ARTIFACT",
        "kind": "contract",
        "created_at": FIXED_NOW.replace(minute=5).isoformat(),
        "source_attempt_id": attempt["attempt_id"],
        "status": validator_result["status"],
        "assertions": validator_result["assertions"],
        "checks": checks,
        "artifact_binding": {
            "scope": work["acceptance_criteria"][0]["artifact_scope"],
            "sha256": artifact_sha256,
        },
        "environment_binding": {
            "id": ENVIRONMENT_ID,
            "fingerprint": _environment_fingerprint(),
        },
        "verifier_binding": {
            key: verifier[key]
            for key in ("id", "revision", "sha256", "trust_root_id")
        },
        "harness_binding": copy.deepcopy(work["harness_binding"]),
        "logs": {
            "stdout_sha256": command_receipt["stdout_sha256"],
            "stderr_sha256": command_receipt["stderr_sha256"],
            "receipt_sha256": conformance.canonical_digest(command_receipt),
        },
        "freshness": {
            "observed_artifact_sha256": artifact_sha256,
            "not_after": "2026-07-28T00:00:00+00:00",
        },
        "independence": {
            "method": "held-out",
            "author_identity": "yuan-reference-port-canary-runner",
            "verifier_identity": "task-008-independent-tester-validator",
            "independent": True,
        },
        "immutable_digest": "0" * 64,
    }
    evidence["immutable_digest"] = conformance.canonical_digest(
        evidence, omitted_paths=(("immutable_digest",),)
    )
    return evidence


def execute(output_root: pathlib.Path) -> dict[str, Any]:
    output_root = output_root.resolve()
    output_root.relative_to(REPO_ROOT)
    if not AUTHORITY_PATH.is_file():
        raise RuntimeError("M4 authority pointer is missing")
    if output_root.exists() and any(path.is_file() for path in output_root.rglob("*")):
        raise RuntimeError("canary output must be absent or empty")
    authority_before = _sha256_file(AUTHORITY_PATH)
    legacy_state_before = _legacy_state_hashes()
    work = _build_work(output_root)
    work_path = output_root / "work-contract.json"
    work_hash = _atomic_json(work_path, work, expected_sha256=None)
    if conformance.validate_document("work-contract", work).errors:
        raise RuntimeError("generated Work Contract is invalid")

    artifact_scope = work["acceptance_criteria"][0]["artifact_scope"]
    attempt = _base_attempt(work, artifact_scope)
    attempt["journal"] = [_journal_entry(1, "PREPARED", None)]
    attempt_path = output_root / "attempts" / "0001.json"
    attempt_hash = _atomic_json(attempt_path, attempt, expected_sha256=None)
    if conformance.authorization_status(
        work,
        attempt["action"],
        attempt["budget_charge"],
        work["budget"],
        trusted_now=FIXED_NOW,
        grant_usage={"GRANT-m5-canary-local": 0},
    ) != "AUTHORIZED":
        raise RuntimeError("Work scope, authorization, or budget rejected the action")

    executable = pathlib.Path(sys.executable).resolve(strict=True)
    port = ReferencePort(
        REPO_ROOT,
        allowed_executables=[executable],
        max_command_seconds=work["budget"]["command_seconds"],
        max_output_bytes=16384,
    )
    attempt["journal"].append(_journal_entry(2, "EXECUTING", None))
    attempt["side_effect_state"] = "EXECUTING"
    attempt_hash = _atomic_json(
        attempt_path, attempt, expected_sha256=attempt_hash
    )
    try:
        write_receipt_object = port.atomic_write(
            artifact_scope, CANARY_PAYLOAD, expected_sha256=None
        )
    except Exception:
        attempt["journal"].append(_journal_entry(3, "UNKNOWN", None))
        attempt["side_effect_state"] = "UNKNOWN"
        attempt["outcome"] = "UNKNOWN"
        _atomic_json(attempt_path, attempt, expected_sha256=attempt_hash)
        raise

    write_receipt = dataclasses.asdict(write_receipt_object)
    write_receipt_digest = conformance.canonical_digest(write_receipt)
    postcondition = {
        "scope": artifact_scope,
        "observed_sha256": write_receipt["after_sha256"],
        "satisfied": (
            _sha256_file(REPO_ROOT / artifact_scope) == write_receipt["after_sha256"]
        ),
    }
    attempt["journal"].append(
        _journal_entry(3, "OBSERVED", write_receipt_digest)
    )
    attempt["side_effect_state"] = "OBSERVED"
    attempt["tool_receipt"] = write_receipt
    attempt["postcondition"] = postcondition
    attempt_hash = _atomic_json(
        attempt_path, attempt, expected_sha256=attempt_hash
    )
    attempt["journal"].append(
        _journal_entry(4, "COMMITTED", write_receipt_digest)
    )
    attempt["side_effect_state"] = "COMMITTED"
    attempt["outcome"] = "SUCCEEDED"
    _atomic_json(attempt_path, attempt, expected_sha256=attempt_hash)
    attempt_errors = conformance.validate_document("attempt", attempt).errors
    if attempt_errors:
        raise RuntimeError(f"committed Attempt invalid: {attempt_errors}")

    command_receipt_object = port.run_command(
        _validator_command(artifact_scope, authority_before),
        timeout_seconds=2,
        cwd=".",
    )
    command_receipt = dataclasses.asdict(command_receipt_object)
    if command_receipt["status"] != "EXITED" or command_receipt["exit_code"] != 0:
        raise RuntimeError(f"validator command failed: {command_receipt}")
    validator_result = json.loads(command_receipt["stdout"])
    if _sha256_file(VALIDATOR_PATH) != work["acceptance_criteria"][0][
        "verifier_binding"
    ]["sha256"]:
        raise RuntimeError("pre-bound verifier changed after Work freeze")
    command_receipt_path = output_root / "receipts" / "validator-command.json"
    validator_result_path = output_root / "receipts" / "validator-result.json"
    _atomic_json(command_receipt_path, command_receipt, expected_sha256=None)
    _atomic_json(validator_result_path, validator_result, expected_sha256=None)

    evidence = _evidence(
        work,
        attempt,
        write_receipt["after_sha256"],
        command_receipt,
        validator_result,
    )
    evidence_path = output_root / "evidence" / "0001.json"
    _atomic_json(evidence_path, evidence, expected_sha256=None)
    evidence_errors = conformance.validate_document("evidence", evidence).errors
    if evidence_errors:
        raise RuntimeError(f"Evidence invalid: {evidence_errors}")
    run_memory = conformance.rebuild_run_memory(
        work,
        [attempt],
        [evidence],
        current_artifact_sha256=write_receipt["after_sha256"],
        environment_id=ENVIRONMENT_ID,
        environment_fingerprint=_environment_fingerprint(),
        trusted_now=FIXED_NOW,
    )
    if run_memory["last_result"] != "COMPLETE":
        raise RuntimeError(f"Core reducer did not complete: {run_memory}")
    memory_path = output_root / "run-memory.json"
    _atomic_json(memory_path, run_memory, expected_sha256=None)
    if conformance.validate_document("run-memory", run_memory).errors:
        raise RuntimeError("rebuilt Run Memory is invalid")
    if _sha256_file(AUTHORITY_PATH) != authority_before:
        raise RuntimeError("Canary changed the M4 authority pointer")
    legacy_state_after = _legacy_state_hashes()
    if legacy_state_after != legacy_state_before:
        raise RuntimeError("Canary changed legacy authority state")

    receipt = {
        "schema_version": "yuan.m5-canary-receipt/v1",
        "status": "PASS",
        "work_contract_sha256": work_hash,
        "artifact_sha256": write_receipt["after_sha256"],
        "attempt_sha256": _sha256_file(attempt_path),
        "evidence_sha256": _sha256_file(evidence_path),
        "run_memory_sha256": _sha256_file(memory_path),
        "command_receipt_sha256": _sha256_file(command_receipt_path),
        "validator_result_sha256": _sha256_file(validator_result_path),
        "validator_sha256": _sha256_file(VALIDATOR_PATH),
        "authority_before_sha256": authority_before,
        "authority_after_sha256": _sha256_file(AUTHORITY_PATH),
        "legacy_state_before": legacy_state_before,
        "legacy_state_after": legacy_state_after,
        "legacy_state_unchanged": legacy_state_before == legacy_state_after,
        "result": run_memory["last_result"],
        "assertions": evidence["assertions"],
    }
    _atomic_json(output_root / "receipt.json", receipt, expected_sha256=None)
    return receipt


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-root", type=pathlib.Path, required=True)
    args = parser.parse_args()
    try:
        receipt = execute(args.output_root)
    except Exception as error:
        print(
            json.dumps(
                {
                    "schema_version": "yuan.m5-canary-receipt/v1",
                    "status": "BLOCKED",
                    "error": f"{type(error).__name__}: {error}",
                },
                ensure_ascii=False,
                sort_keys=True,
            ),
            file=sys.stderr,
        )
        return 2
    print(json.dumps(receipt, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
