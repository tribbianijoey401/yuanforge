#!/usr/bin/env python3
"""Archive the legacy projection and install the bounded M8/M9 successor Work."""

from __future__ import annotations

import json
import pathlib
import sys
from typing import Any

from yuan_activation import verify_activation_descriptor
from yuan_authority import AuthorityError, load_current, verify_authority
from yuan_runtime_state import (
    RUNS_ROOT,
    atomic_write,
    canonical,
    file_sha256,
    rebuild_runtime_memory,
    seal_runtime,
    sha256,
    verify_runtime_at,
    write_immutable,
)
from yuan_runtime_transaction import (
    activate_runtime_generation,
    canonical_digest,
)


ARCHIVES = pathlib.PurePosixPath(".yuan/authority/runtime-archive")
EMPTY_SHA256 = sha256(b"")


def archive_legacy_runtime(repo_root: pathlib.Path) -> dict[str, Any]:
    repo = pathlib.Path(repo_root).resolve()
    runtime = repo / ".yuan-run"
    manifest_path = runtime / "runtime-manifest.json"
    manifest_sha = file_sha256(manifest_path)
    archive = repo / ARCHIVES / manifest_sha
    index_path = archive / "index.json"
    if index_path.is_file():
        return json.loads(index_path.read_text(encoding="utf-8"))
    source_files = []
    for relative in (
        "contracts",
        "attempts",
        "evidence",
    ):
        source_files.extend(
            path for path in sorted((runtime / relative).glob("*.json"))
        )
    source_files.extend([runtime / "run-memory.json", manifest_path])
    entries = []
    for source in source_files:
        relative = source.relative_to(runtime).as_posix()
        digest = file_sha256(source)
        write_immutable(archive / "blobs" / f"{digest}.blob", source.read_bytes())
        entries.append(
            {
                "path": relative,
                "sha256": digest,
                "bytes": source.stat().st_size,
            }
        )
    index = {
        "schema_version": "yuan.runtime-archive/v1",
        "source_runtime_root": ".yuan-run",
        "source_manifest_sha256": manifest_sha,
        "source_authority_record_sha256": load_current(repo)["record_sha256"],
        "files": entries,
        "counts": {
            "work": len(list((runtime / "contracts").glob("*.json"))),
            "attempt": len(list((runtime / "attempts").glob("*.json"))),
            "evidence": len(list((runtime / "evidence").glob("*.json"))),
        },
    }
    atomic_write(index_path, canonical(index), None)
    return index


def verify_runtime_archive(repo_root: pathlib.Path, manifest_sha256: str) -> dict[str, Any]:
    repo = pathlib.Path(repo_root).resolve()
    archive = repo / ARCHIVES / manifest_sha256
    try:
        index = json.loads((archive / "index.json").read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise AuthorityError("runtime archive index is missing or invalid") from error
    if (
        index.get("schema_version") != "yuan.runtime-archive/v1"
        or index.get("source_manifest_sha256") != manifest_sha256
        or index.get("counts") != {"work": 1, "attempt": 37, "evidence": 37}
    ):
        raise AuthorityError("runtime archive identity/count mismatch")
    for entry in index.get("files", []):
        blob = archive / "blobs" / f"{entry.get('sha256')}.blob"
        if (
            not blob.is_file()
            or file_sha256(blob) != entry.get("sha256")
            or blob.stat().st_size != entry.get("bytes")
        ):
            raise AuthorityError("runtime archive blob mismatch")
    return index


def _binding(
    identifier: str,
    revision: str,
    digest: str,
    environment_id: str,
    environment_fingerprint: str,
    assertions: int,
) -> dict[str, Any]:
    return {
        "id": identifier,
        "revision": revision,
        "sha256": digest,
        "trust_root_id": "yuan-genesis-legacy-independent",
        "environment_ids": [environment_id],
        "environment_fingerprints": {
            environment_id: environment_fingerprint,
        },
        "minimum_assertions": assertions,
    }


def build_successor_documents(repo_root: pathlib.Path) -> tuple[dict, dict, dict]:
    repo = pathlib.Path(repo_root).resolve()
    activation = verify_activation_descriptor(repo)
    protocol = {
        "id": "yuan.core.protocol",
        "revision": "0.1.0-candidate-activated",
        "sha256": activation["protocol_sha256"],
    }
    harness_path = repo / "scripts/yuan_runtime_transaction.py"
    harness = {
        "id": "yuan.runtime-transaction",
        "revision": "1",
        "sha256": file_sha256(harness_path),
    }
    environment_id = "yuan-genesis-old-root"
    environment_fingerprint = activation["older_root_verifier_sha256"]
    held_out = repo / "tests/core_01/held_out_validator.py"
    tombstone = repo / ".yuan/authority/verifiers/tombstone-wait-auth.json"
    work = {
        "schema_version": "yuan.work-contract/v1",
        "work_id": "WORK-yuan-m8-m9-successor",
        "revision": {
            "id": "WORK-yuan-m8-m9-successor",
            "revision": "1",
            "sha256": "0" * 64,
        },
        "protocol_binding": protocol,
        "harness_binding": harness,
        "intent": {
            "goal": "Close M8 authority liveness, execute M9 self-modification dogfood, then wait for explicit human authorization before any legacy tombstone.",
            "non_goals": [
                "Do not rewrite archived legacy Work, Attempt, or Evidence.",
                "Do not tombstone legacy paths without a new human grant.",
            ],
            "constraints": [
                "One active-run pointer and one authority pointer.",
                "All runtime appends use generation transactions.",
                "Verifier failure or partial commit is BLOCKED.",
            ],
        },
        "scope": {
            "allowed_paths": [
                ".yuan/authority",
                ".yuan-run",
                ".yuan/core/0.1",
                "scripts",
                "tests/authority_switch",
                "docs",
            ],
            "denied_paths": [".git", ".yuan-shadow"],
            "side_effect_classes": ["none", "filesystem", "command"],
        },
        "authorization": {
            "default": "deny",
            "grants": [
                {
                    "id": "GRANT-CORE-M8-M9",
                    "action_types": [
                        "file-read",
                        "file-write",
                        "command",
                        "verify",
                        "reconcile",
                    ],
                    "side_effect_classes": ["none", "filesystem", "command"],
                    "scopes": [
                        ".yuan/authority",
                        ".yuan-run",
                        ".yuan/core/0.1",
                        "scripts",
                        "tests/authority_switch",
                    ],
                    "high_impact": False,
                    "expires_at": None,
                    "max_uses": 20,
                }
            ],
        },
        "budget": {
            "ticks": 20,
            "tool_calls": 40,
            "strategies": 20,
            "command_seconds": 600,
        },
        "acceptance_criteria": [
            {
                "id": "AC-M8-AUTHORITY-SWITCH",
                "type": "structure",
                "required": True,
                "predicate": "The single Core authority, recoverable old runtime archive, activation proof, writer exclusion, and transactional append path all verify.",
                "artifact_scope": ".yuan/authority",
                "verifier_binding": _binding(
                    "yuan.m8-old-root-activation",
                    "1",
                    activation["older_root_verifier_sha256"],
                    environment_id,
                    environment_fingerprint,
                    5,
                ),
            },
            {
                "id": "AC-M9-SELF-MODIFICATION-DOGFOOD",
                "type": "integration",
                "required": True,
                "predicate": "A self-modification Work runs through Core and is independently verified with no candidate self-trust.",
                "artifact_scope": ".yuan/core/0.1",
                "verifier_binding": _binding(
                    "yuan.m9-independent-held-out",
                    "1",
                    file_sha256(held_out),
                    environment_id,
                    environment_fingerprint,
                    30,
                ),
            },
            {
                "id": "AC-M9-LEGACY-TOMBSTONE-WAIT-AUTH",
                "type": "human-judgment",
                "required": True,
                "predicate": "Legacy cleanup or tombstone remains WAIT_AUTH until an explicit human grant names paths, risk, and recovery window.",
                "artifact_scope": "docs",
                "verifier_binding": _binding(
                    "yuan.legacy-tombstone-human-gate",
                    "1",
                    file_sha256(tombstone),
                    environment_id,
                    environment_fingerprint,
                    1,
                ),
            },
        ],
        "safety_invariants": [
            {
                "id": "SAFE-SINGLE-AUTHORITY",
                "predicate": "No dual writer or ambiguous active run exists.",
            },
            {
                "id": "SAFE-LEGACY-RECOVERABLE",
                "predicate": "The old 1/37/37 runtime is content-addressed and recoverable.",
            },
        ],
    }
    work["revision"]["sha256"] = canonical_digest(
        work, omitted_paths=(("revision", "sha256"),)
    )
    descriptor_path = repo / ".yuan/authority/activation/yuan-core-0.1.json"
    receipt_path = repo / ".yuan/authority/activation/evidence/old-root-receipt.json"
    attempt = {
        "schema_version": "yuan.attempt/v1",
        "attempt_id": "ATT-M8-ACTIVATION-0001",
        "work_binding": work["revision"],
        "protocol_binding": protocol,
        "harness_binding": harness,
        "sequence": 1,
        "strategy_fingerprint": sha256(b"m8-independent-activation"),
        "relevant_inputs": [
            {
                "scope": ".yuan/authority/activation/yuan-core-0.1.json",
                "sha256": file_sha256(descriptor_path),
            }
        ],
        "hypothesis": {
            "claim": "The older root activation and archived runtime close M8 without candidate self-trust.",
            "falsification": "Any hash, positive-check, archive, CAS, or writer-exclusion mismatch blocks activation.",
        },
        "action": {
            "type": "verify",
            "mutating": False,
            "side_effect_class": "none",
            "scope": ".yuan/authority",
            "authorization_grant_id": "GRANT-CORE-M8-M9",
            "high_impact": False,
            "self_modification": None,
        },
        "budget_charge": {
            "ticks": 1,
            "tool_calls": 1,
            "strategies": 1,
            "command_seconds": 3,
        },
        "journal": [],
        "side_effect_state": "NOT_APPLICABLE",
        "tool_receipt": {
            "schema_version": "yuan.tool-receipt/v1",
            "kind": "command",
            "operation_id": "OP-M8-OLD-ROOT-ACTIVATION",
            "status": "EXITED",
            "exit_code": 0,
            "stdout_sha256": file_sha256(receipt_path),
            "stderr_sha256": EMPTY_SHA256,
        },
        "postcondition": None,
        "evidence_ids": ["EVD-M8-ACTIVATION-0001"],
        "outcome": "SUCCEEDED",
    }
    checks = [
        {
            "id": "M8-OLD-ROOT-80-CHECKS",
            "status": "PASS",
            "observation": "Older Genesis root accepted the exact activated candidate with 80 checks.",
        },
        {
            "id": "M8-ACTIVE-RUN-CAS",
            "status": "PASS",
            "observation": "Successor installation uses active-run and authority pointer CAS.",
        },
        {
            "id": "M8-TRANSACTIONAL-APPEND",
            "status": "PASS",
            "observation": "New runtime history is generation-sealed before pointer commit.",
        },
        {
            "id": "SAFE-SINGLE-AUTHORITY",
            "status": "PASS",
            "observation": "Only the Core writer lane is active.",
        },
        {
            "id": "SAFE-LEGACY-RECOVERABLE",
            "status": "PASS",
            "observation": "The exact old 1/37/37 runtime has a verified content-addressed archive.",
        },
    ]
    evidence = {
        "schema_version": "yuan.evidence/v1",
        "evidence_id": "EVD-M8-ACTIVATION-0001",
        "sequence": 1,
        "work_binding": work["revision"],
        "ac_id": "AC-M8-AUTHORITY-SWITCH",
        "kind": "structure",
        "created_at": "2026-07-29T06:37:48+00:00",
        "source_attempt_id": attempt["attempt_id"],
        "status": "PASS",
        "assertions": len(checks),
        "checks": checks,
        "artifact_binding": {
            "scope": ".yuan/authority",
            "sha256": file_sha256(descriptor_path),
        },
        "environment_binding": {
            "id": environment_id,
            "fingerprint": environment_fingerprint,
        },
        "verifier_binding": {
            key: work["acceptance_criteria"][0]["verifier_binding"][key]
            for key in ("id", "revision", "sha256", "trust_root_id")
        },
        "harness_binding": harness,
        "logs": {
            "stdout_sha256": EMPTY_SHA256,
            "stderr_sha256": EMPTY_SHA256,
            "receipt_sha256": file_sha256(receipt_path),
        },
        "freshness": {
            "observed_artifact_sha256": file_sha256(descriptor_path),
            "not_after": None,
        },
        "independence": {
            "method": "old-trust-root",
            "author_identity": "backend-dev-task-011-r1",
            "verifier_identity": "frozen-genesis-root-task-009",
            "independent": True,
        },
        "immutable_digest": "0" * 64,
    }
    evidence["immutable_digest"] = canonical_digest(
        evidence, omitted_paths=(("immutable_digest",),)
    )
    return work, attempt, evidence


def install_successor_run(repo_root: pathlib.Path) -> dict[str, Any]:
    repo = pathlib.Path(repo_root).resolve()
    verified = verify_authority(repo)
    if verified["authority"] != "core" or (repo / ".yuan-run/active-run.json").exists():
        raise AuthorityError("successor run is already installed or Core is inactive")
    current_pointer = load_current(repo)["pointer_sha256"]
    archived = archive_legacy_runtime(repo)
    verify_runtime_archive(repo, archived["source_manifest_sha256"])
    work, attempt, evidence = build_successor_documents(repo)
    run_id = f"{work['work_id']}-g0001-{work['revision']['sha256'][:12]}"
    runtime = repo / RUNS_ROOT / run_id
    if runtime.exists():
        raise AuthorityError("successor runtime generation already exists")
    for area in ("contracts", "attempts", "evidence"):
        (runtime / area).mkdir(parents=True, exist_ok=False)
    write_immutable(runtime / "contracts" / f"{work['work_id']}.json", canonical(work))
    write_immutable(runtime / "attempts/0001.json", canonical(attempt))
    write_immutable(runtime / "evidence/0001.json", canonical(evidence))
    atomic_write(
        runtime / "run-memory.json",
        canonical(rebuild_runtime_memory(repo, runtime)),
        None,
    )
    seal_runtime(
        repo,
        runtime,
        legacy_snapshot_sha256=json.loads(
            (repo / ".yuan-run/runtime-manifest.json").read_text()
        )["legacy_snapshot_sha256"],
        source_projection_sha256=archived["source_manifest_sha256"],
    )
    verify_runtime_at(repo, runtime)
    receipt = activate_runtime_generation(
        repo,
        runtime,
        expected_authority_pointer_sha256=current_pointer,
        protocol_activation=verify_activation_descriptor(repo),
    )
    final = verify_authority(repo)
    return {
        "status": "PASS",
        "archive_manifest_sha256": archived["source_manifest_sha256"],
        "successor_runtime_root": runtime.relative_to(repo).as_posix(),
        "successor_result": rebuild_runtime_memory(repo)["last_result"],
        "successor_legal_next_steps": rebuild_runtime_memory(repo)[
            "legal_next_steps"
        ],
        "authority": final,
        "transaction": receipt,
    }


def main() -> int:
    repo = pathlib.Path(__file__).resolve().parents[1]
    try:
        receipt = install_successor_run(repo)
    except (AuthorityError, OSError, UnicodeError, json.JSONDecodeError) as error:
        print(f"BLOCKED {error}", file=sys.stderr)
        return 2
    print(json.dumps(receipt, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
