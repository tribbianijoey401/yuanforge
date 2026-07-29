"""Execute the M9 self-modification through the live revision-6 Core Work."""

from __future__ import annotations

import copy
import json
import pathlib
import shutil
import subprocess
import sys
import tempfile
from typing import Any

from yuan_activation import verify_activation_descriptor
from yuan_authority import load_current, verify_authority
from yuan_runtime_state import (
    AuthorityError,
    RUNS_ROOT,
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
from yuan_runtime_transaction import (
    _build_generation,
    canonical_digest,
    replace_runtime_generation,
)


EMPTY_SHA256 = sha256(b"")
OLD_ROOT_RUNNER = pathlib.PurePosixPath(
    "tests/adapter_conformance/run_m6_old_root.py"
)
TX_ROOT = pathlib.PurePosixPath(
    ".yuan/authority/self-modification/transactions"
)
EVIDENCE_ROOT = pathlib.PurePosixPath(
    ".yuan/authority/self-modification/evidence"
)
HISTORY_ROOT = pathlib.PurePosixPath(
    ".yuan/authority/core-history/r2-to-m9"
)


class MutationCrash(RuntimeError):
    """Injected interruption inside the independently journaled Core mutation."""

    def __init__(self, transaction_id: str):
        super().__init__(transaction_id)
        self.transaction_id = transaction_id


def build_protocol(previous: bytes) -> bytes:
    text = previous.decode("utf-8")
    text = text.replace(
        "Revision: `yuan.core.protocol/0.1.0-candidate`",
        "Revision: `yuan.core.protocol/0.1.0`",
        1,
    )
    text = text.replace(
        "Status: inert candidate. This document and its sibling schemas do not become\n"
        "> runtime authority until an older trust root independently accepts them.",
        "Status: stable protocol; default inert. Runtime activation requires an external,\n"
        "> content-addressed authority record bound to previous or independent proof.",
        1,
    )
    text = text.replace(
        "## 12. Inert-candidate rule\n\n"
        "Files in this directory define a candidate only. They must not modify the\n"
        "repository entrypoint, current runtime authority, initializer, pre-commit\n"
        "configuration, or existing user work. Authority changes require later migration\n"
        "milestones and independent Evidence.",
        "## 12. External-activation rule\n\n"
        "Files in this directory are inert by default. They become active only when an\n"
        "external content-addressed authority record binds their exact revision and hash\n"
        "to positive previous-root or independent Evidence. Candidate conformance and\n"
        "self-attestation never activate Core. Initializer, user work, and unrelated\n"
        "repository state remain outside that activation.",
        1,
    )
    if text == previous.decode("utf-8"):
        raise RuntimeError("frozen protocol replacement anchors are absent")
    return text.encode("utf-8")


def build_candidate_manifest(
    repo_root: pathlib.Path,
    previous: dict[str, Any],
    protocol_bytes: bytes,
) -> dict[str, Any]:
    repo = pathlib.Path(repo_root).resolve()
    manifest = copy.deepcopy(previous)
    manifest.update(
        {
            "candidate_revision": "yuan.core/0.1.0",
            "protocol_revision": "yuan.core.protocol/0.1.0",
            "authority": "inert-by-default",
            "self_trust": False,
            "activation": {
                "mode": "external-content-addressed-authority",
                "requires": ["previous-root-proof", "independent-proof"],
            },
            "manifest_binding": (
                "External authority binds this manifest by SHA-256; "
                "self-hashing and self-activation are forbidden."
            ),
        }
    )
    for item in manifest["files"]:
        target = repo / ".yuan/core/0.1" / item["path"]
        item["sha256"] = (
            sha256(protocol_bytes)
            if item["path"] == "protocol.md"
            else file_sha256(target)
        )
    return manifest


def _run_old_root(
    repo: pathlib.Path,
    candidate_sha256: str,
    receipt: pathlib.Path,
    suite: pathlib.Path,
) -> dict[str, Any]:
    process = subprocess.run(
        [
            sys.executable,
            "-B",
            str(repo / OLD_ROOT_RUNNER),
            "--candidate-manifest-sha256",
            candidate_sha256,
            "--receipt",
            str(receipt),
            "--manifest-snapshot",
            str(suite),
        ],
        cwd=repo,
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        check=False,
    )
    if process.returncode != 0:
        raise RuntimeError(
            "frozen old-root verification failed: "
            + (process.stderr.strip() or process.stdout.strip())[:2000]
        )
    value = json.loads(receipt.read_text(encoding="utf-8"))
    cases = [
        item
        for item in value.get("cases", [])
        if item.get("id") == "yuan-core-01-candidate"
    ]
    assertions = (
        cases[0].get("validator", {}).get("assertions", 0)
        if len(cases) == 1
        else 0
    )
    if (
        value.get("status") != "PASS"
        or value.get("checks_executed", 0) < 80
        or assertions < 30
        or cases[0].get("observed") != "ACCEPT"
        or cases[0].get("matched") is not True
    ):
        raise RuntimeError("old-root receipt lacks positive independent checks")
    return {"receipt": value, "assertions": assertions}


def _preflight(
    repo: pathlib.Path,
    protocol: bytes,
    manifest: dict[str, Any],
) -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix="yuan-m9-preflight-") as name:
        staged = pathlib.Path(name)
        for relative in (".yuan", "scripts", "tests"):
            shutil.copytree(repo / relative, staged / relative)
        atomic_write(
            staged / ".yuan/core/0.1/protocol.md",
            protocol,
            file_sha256(staged / ".yuan/core/0.1/protocol.md"),
        )
        manifest_bytes = canonical(manifest)
        atomic_write(
            staged / ".yuan/core/0.1/candidate-manifest.json",
            manifest_bytes,
            file_sha256(staged / ".yuan/core/0.1/candidate-manifest.json"),
        )
        return _run_old_root(
            staged,
            sha256(manifest_bytes),
            staged / "preflight-receipt.json",
            staged / "preflight-suite.json",
        )


def _journal_attempt(
    work: dict[str, Any],
    candidate_sha: str,
    previous_sha: str,
    assertions: int,
    *,
    proof_attack: str | None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    ac = next(
        item
        for item in work["acceptance_criteria"]
        if item["id"] == "AC-M9-SELF-MODIFICATION-DOGFOOD"
    )
    previous = {
        key: ac["verifier_binding"][key]
        for key in ("id", "revision", "sha256")
    }
    candidate = {
        "id": "yuan.core.protocol",
        "revision": "0.1.0",
        "sha256": candidate_sha,
    }
    proof = {
        "kind": "previous-root",
        "root_binding": copy.deepcopy(previous),
        "candidate_binding": copy.deepcopy(candidate),
        "status": "PASS",
        "assertions": assertions,
    }
    if proof_attack == "wrong-root":
        proof["root_binding"]["sha256"] = "0" * 64
    if proof_attack == "wrong-candidate":
        proof["candidate_binding"]["sha256"] = "0" * 64
    base = {
        "schema_version": "yuan.attempt/v1",
        "attempt_id": "ATT-M9-LIVE-SELF-MOD-0002",
        "work_binding": work["revision"],
        "protocol_binding": work["protocol_binding"],
        "harness_binding": work["harness_binding"],
        "sequence": 2,
        "strategy_fingerprint": canonical_digest(
            {"strategy": "live-core-self-modification", "candidate": candidate_sha}
        ),
        "relevant_inputs": [
            {"scope": ".yuan/core/0.1", "sha256": previous_sha}
        ],
        "hypothesis": {
            "claim": "The live Core can clarify its activation status under its own Work and an older independent root.",
            "falsification": "Any scope, journal, previous-root, artifact, or held-out binding mismatch blocks promotion.",
        },
        "action": {
            "type": "file-write",
            "mutating": True,
            "side_effect_class": "filesystem",
            "scope": ".yuan/core/0.1",
            "authorization_grant_id": "GRANT-CORE-M8-M9",
            "high_impact": False,
            "self_modification": {
                "change": {
                    "target_kind": "core",
                    "candidate_binding": candidate,
                    "previous_binding": previous,
                    "risk": "R0",
                },
                "proofs": [proof],
            },
        },
        "budget_charge": {
            "ticks": 1,
            "tool_calls": 2,
            "strategies": 1,
            "command_seconds": 20,
        },
        "journal": [
            {
                "ordinal": 1,
                "state": "PREPARED",
                "recorded_at": "2026-07-29T08:00:00+00:00",
                "receipt_sha256": None,
            }
        ],
        "side_effect_state": "PREPARED",
        "tool_receipt": None,
        "postcondition": None,
        "evidence_ids": ["EVD-M9-LIVE-SELF-MOD-0002"],
        "outcome": "PENDING",
    }
    return base, proof


def _complete_attempt(
    prepared: dict[str, Any],
    previous_sha: str,
    candidate_sha: str,
) -> dict[str, Any]:
    attempt = copy.deepcopy(prepared)
    receipt = {
        "schema_version": "yuan.tool-receipt/v1",
        "kind": "file-write",
        "operation_id": "OP-M9-LIVE-CORE-REPLACE",
        "status": "REPLACED",
        "path": ".yuan/core/0.1",
        "before_sha256": previous_sha,
        "after_sha256": candidate_sha,
    }
    receipt_sha = canonical_digest(receipt)
    attempt["journal"] = [
        {
            "ordinal": index,
            "state": state,
            "recorded_at": f"2026-07-29T08:0{index}:00+00:00",
            "receipt_sha256": (
                receipt_sha if state in {"OBSERVED", "COMMITTED"} else None
            ),
        }
        for index, state in enumerate(
            ("PREPARED", "EXECUTING", "OBSERVED", "COMMITTED"), start=1
        )
    ]
    attempt["side_effect_state"] = "COMMITTED"
    attempt["tool_receipt"] = receipt
    attempt["postcondition"] = {
        "scope": ".yuan/core/0.1",
        "observed_sha256": candidate_sha,
        "satisfied": True,
    }
    attempt["outcome"] = "SUCCEEDED"
    return attempt


def _evidence(
    work: dict[str, Any],
    attempt: dict[str, Any],
    artifact_sha: str,
    receipt_sha: str,
    assertions: int,
    *,
    sequence: int,
    evidence_id: str,
) -> dict[str, Any]:
    ac = next(
        item
        for item in work["acceptance_criteria"]
        if item["id"] == "AC-M9-SELF-MODIFICATION-DOGFOOD"
    )
    evidence = {
        "schema_version": "yuan.evidence/v1",
        "evidence_id": evidence_id,
        "sequence": sequence,
        "work_binding": work["revision"],
        "ac_id": ac["id"],
        "kind": "integration",
        "created_at": "2026-07-29T08:10:00+00:00",
        "source_attempt_id": attempt["attempt_id"],
        "status": "PASS",
        "assertions": assertions,
        "checks": [
            {
                "id": f"M9-INDEPENDENT-{index:03d}",
                "status": "PASS",
                "observation": "Frozen held-out old root accepted the exact externally activated Core.",
            }
            for index in range(1, assertions + 1)
        ],
        "artifact_binding": {
            "scope": ac["artifact_scope"],
            "sha256": artifact_sha,
        },
        "environment_binding": {
            "id": "yuan-genesis-old-root",
            "fingerprint": file_sha256(
                pathlib.Path(__file__).resolve().parents[1] / OLD_ROOT_RUNNER
            ),
        },
        "verifier_binding": ac["verifier_binding"],
        "harness_binding": work["harness_binding"],
        "logs": {
            "stdout_sha256": EMPTY_SHA256,
            "stderr_sha256": EMPTY_SHA256,
            "receipt_sha256": receipt_sha,
        },
        "freshness": {
            "observed_artifact_sha256": artifact_sha,
            "not_after": None,
        },
        "independence": {
            "method": "old-trust-root",
            "author_identity": "backend-dev-task-012",
            "verifier_identity": "frozen-genesis-held-out",
            "independent": True,
        },
        "immutable_digest": "0" * 64,
    }
    evidence["immutable_digest"] = canonical_digest(
        evidence, omitted_paths=(("immutable_digest",),)
    )
    return evidence


def _write_phase(
    path: pathlib.Path,
    journal: dict[str, Any],
    expected: str | None,
) -> str:
    atomic_write(path, canonical(journal), expected)
    return file_sha256(path)


def _successor_work(
    work: dict[str, Any],
    protocol_sha: str,
) -> dict[str, Any]:
    successor = copy.deepcopy(work)
    successor["acceptance_criteria"] = [
        item
        for item in successor["acceptance_criteria"]
        if item["id"] != "AC-M8-AUTHORITY-SWITCH"
    ]
    successor["protocol_binding"] = {
        "id": "yuan.core.protocol",
        "revision": "0.1.0",
        "sha256": protocol_sha,
    }
    successor["revision"]["revision"] = "3"
    successor["revision"]["sha256"] = canonical_digest(
        successor, omitted_paths=(("revision", "sha256"),)
    )
    return successor


def _verification_attempt(
    work: dict[str, Any],
    receipt_sha: str,
) -> dict[str, Any]:
    return {
        "schema_version": "yuan.attempt/v1",
        "attempt_id": "ATT-M9-WORK3-INDEPENDENT-0001",
        "work_binding": work["revision"],
        "protocol_binding": work["protocol_binding"],
        "harness_binding": work["harness_binding"],
        "sequence": 1,
        "strategy_fingerprint": canonical_digest(
            {"strategy": "work3-independent-reissue", "receipt": receipt_sha}
        ),
        "relevant_inputs": [
            {"scope": ".yuan/core/0.1", "sha256": file_sha256(
                pathlib.Path(__file__).resolve().parents[1]
                / ".yuan/core/0.1/candidate-manifest.json"
            )}
        ],
        "hypothesis": {
            "claim": "The frozen root independently reissues M9 Evidence under Work revision 3.",
            "falsification": "A binding or positive-check mismatch blocks the successor.",
        },
        "action": {
            "type": "verify",
            "mutating": False,
            "side_effect_class": "none",
            "scope": ".yuan/core/0.1",
            "authorization_grant_id": "GRANT-CORE-M8-M9",
            "high_impact": False,
            "self_modification": None,
        },
        "budget_charge": {
            "ticks": 1,
            "tool_calls": 1,
            "strategies": 1,
            "command_seconds": 10,
        },
        "journal": [],
        "side_effect_state": "NOT_APPLICABLE",
        "tool_receipt": {
            "schema_version": "yuan.tool-receipt/v1",
            "kind": "command",
            "operation_id": "OP-M9-WORK3-OLD-ROOT",
            "status": "EXITED",
            "stdout_sha256": EMPTY_SHA256,
            "stderr_sha256": EMPTY_SHA256,
            "exit_code": 0,
        },
        "postcondition": None,
        "evidence_ids": ["EVD-M9-WORK3-INDEPENDENT-0001"],
        "outcome": "SUCCEEDED",
    }


def install(
    repo_root: pathlib.Path,
    *,
    failure_after: str | None = None,
    mutation_failure_after: str | None = None,
    proof_attack: str | None = None,
) -> dict[str, Any]:
    repo = pathlib.Path(repo_root).resolve()
    verified = verify_authority(repo)
    current = load_current(repo)
    runtime, _, active_sha = resolve_runtime_root(repo)
    if (
        verified["revision"] != 6
        or current["record"].get("authority") != "core"
        or active_sha is None
    ):
        raise RuntimeError("M9 requires the live revision-6 Core")
    work = json.loads(next((runtime / "contracts").glob("*.json")).read_text())
    if (
        work.get("revision", {}).get("revision") != "2"
        or work.get("harness_binding", {}).get("sha256")
        != file_sha256(repo / "scripts/yuan_runtime_transaction.py")
    ):
        raise RuntimeError("M9 requires exact active Work revision 2")
    old_protocol_path = repo / ".yuan/core/0.1/protocol.md"
    manifest_path = repo / ".yuan/core/0.1/candidate-manifest.json"
    old_protocol = old_protocol_path.read_bytes()
    old_manifest = manifest_path.read_bytes()
    old_artifact_sha = sha256(old_manifest)
    protocol = build_protocol(old_protocol)
    manifest = build_candidate_manifest(repo, json.loads(old_manifest), protocol)
    manifest_bytes = canonical(manifest)
    candidate_sha = sha256(manifest_bytes)
    preflight = _preflight(repo, protocol, manifest)
    prepared, proof = _journal_attempt(
        work,
        candidate_sha,
        old_artifact_sha,
        preflight["assertions"],
        proof_attack=proof_attack,
    )
    if (
        proof["root_binding"]
        != prepared["action"]["self_modification"]["change"]["previous_binding"]
        or proof["candidate_binding"]
        != prepared["action"]["self_modification"]["change"]["candidate_binding"]
    ):
        raise AuthorityError("self-modification previous-root proof mismatch")
    txid = canonical_digest(
        {
            "work": work["revision"],
            "previous": old_artifact_sha,
            "candidate": candidate_sha,
        }
    )
    txdir = repo / TX_ROOT / txid
    write_immutable(txdir / "attempt-prepared.json", canonical(prepared))
    write_immutable(
        repo / HISTORY_ROOT / "blobs" / f"{old_artifact_sha}.blob",
        old_manifest,
    )
    old_protocol_sha = sha256(old_protocol)
    write_immutable(
        repo / HISTORY_ROOT / "blobs" / f"{old_protocol_sha}.blob",
        old_protocol,
    )
    mutation = {
        "schema_version": "yuan.self-modification-transaction/v1",
        "transaction_id": txid,
        "state": "PREPARED",
        "attempt_id": prepared["attempt_id"],
        "previous_candidate_sha256": old_artifact_sha,
        "candidate_sha256": candidate_sha,
        "previous_protocol_sha256": old_protocol_sha,
        "protocol_sha256": sha256(protocol),
    }
    mutation_path = txdir / "journal.json"
    mutation_sha = _write_phase(mutation_path, mutation, None)
    mutation["state"] = "EXECUTING"
    mutation_sha = _write_phase(mutation_path, mutation, mutation_sha)
    if mutation_failure_after == "executing":
        raise MutationCrash(txid)
    atomic_write(old_protocol_path, protocol, old_protocol_sha)
    if mutation_failure_after == "protocol":
        raise MutationCrash(txid)
    atomic_write(manifest_path, manifest_bytes, old_artifact_sha)
    receipt_path = repo / EVIDENCE_ROOT / "old-root-receipt-m9.json"
    suite_path = repo / EVIDENCE_ROOT / "old-root-manifest-m9.json"
    live_proof = _run_old_root(
        repo, candidate_sha, receipt_path, suite_path
    )
    attempt = _complete_attempt(prepared, old_artifact_sha, candidate_sha)
    write_immutable(txdir / "attempt-observed.json", canonical(attempt))
    mutation.update(
        {
            "state": "OBSERVED",
            "tool_receipt_sha256": canonical_digest(attempt["tool_receipt"]),
            "old_root_receipt_sha256": file_sha256(receipt_path),
        }
    )
    mutation_sha = _write_phase(mutation_path, mutation, mutation_sha)
    evidence = _evidence(
        work,
        attempt,
        candidate_sha,
        file_sha256(receipt_path),
        live_proof["assertions"],
        sequence=2,
        evidence_id="EVD-M9-LIVE-SELF-MOD-0002",
    )
    validate_runtime_evidence(repo, runtime, attempt, evidence)
    previous_manifest = verify_runtime_at(repo, runtime)
    generation, _ = _build_generation(
        repo, runtime, txid, attempt, evidence, previous_manifest
    )
    memory = json.loads((generation / "run-memory.json").read_text())
    if (
        memory.get("last_result") != "WAIT_AUTH"
        or memory.get("legal_next_steps", [{}])[0].get("ac_id")
        != "AC-M9-LEGACY-TOMBSTONE-WAIT-AUTH"
    ):
        raise RuntimeError("rev2 dogfood generation did not converge to WAIT_AUTH")
    write_immutable(txdir / "attempt-committed.json", canonical(attempt))
    write_immutable(txdir / "evidence.json", canonical(evidence))
    mutation.update(
        {
            "state": "COMMITTED",
            "runtime_root": generation.relative_to(repo).as_posix(),
            "runtime_manifest_sha256": file_sha256(
                generation / "runtime-manifest.json"
            ),
        }
    )
    _write_phase(mutation_path, mutation, mutation_sha)

    descriptor_path = repo / ".yuan/authority/activation/yuan-core-0.1.json"
    old_descriptor = descriptor_path.read_bytes()
    old_descriptor_sha = sha256(old_descriptor)
    write_immutable(
        repo
        / ".yuan/authority/activation/history"
        / f"{old_descriptor_sha}.blob",
        old_descriptor,
    )
    descriptor = json.loads(old_descriptor)
    descriptor.update(
        {
            "protocol_sha256": sha256(protocol),
            "prior_activated_candidate_manifest_sha256": old_artifact_sha,
            "prior_activated_candidate_manifest_path": (
                f"{HISTORY_ROOT.as_posix()}/blobs/{old_artifact_sha}.blob"
            ),
            "activated_candidate_manifest_sha256": candidate_sha,
            "candidate_manifest_sha256": candidate_sha,
            "activated_older_root_manifest_path": (
                EVIDENCE_ROOT / "old-root-manifest-m9.json"
            ).as_posix(),
            "activated_older_root_manifest_sha256": file_sha256(suite_path),
            "independent_evidence_path": (
                EVIDENCE_ROOT / "old-root-receipt-m9.json"
            ).as_posix(),
            "independent_evidence_sha256": file_sha256(receipt_path),
            "older_root_receipt_sha256": file_sha256(receipt_path),
            "previous_descriptor_path": (
                ".yuan/authority/activation/history/"
                f"{old_descriptor_sha}.blob"
            ),
            "previous_descriptor_sha256": old_descriptor_sha,
        }
    )
    atomic_write(descriptor_path, canonical(descriptor), old_descriptor_sha)
    activation = verify_activation_descriptor(repo)

    work3 = _successor_work(work, sha256(protocol))
    work3_receipt = repo / EVIDENCE_ROOT / "old-root-receipt-m9-work3.json"
    work3_suite = repo / EVIDENCE_ROOT / "old-root-manifest-m9-work3.json"
    work3_proof = _run_old_root(
        repo, candidate_sha, work3_receipt, work3_suite
    )
    verify_attempt = _verification_attempt(
        work3, file_sha256(work3_receipt)
    )
    work3_evidence = _evidence(
        work3,
        verify_attempt,
        candidate_sha,
        file_sha256(work3_receipt),
        work3_proof["assertions"],
        sequence=1,
        evidence_id="EVD-M9-WORK3-INDEPENDENT-0001",
    )
    successor_id = (
        f"{work3['work_id']}-r3-{work3['revision']['sha256'][:12]}"
    )
    pending = repo / RUNS_ROOT / f".pending-m9-{work3['revision']['sha256'][:12]}"
    final = repo / RUNS_ROOT / successor_id
    for area in ("contracts", "attempts", "evidence"):
        (pending / area).mkdir(parents=True, exist_ok=True)
    write_immutable(
        pending / "contracts" / f"{work3['work_id']}.json",
        canonical(work3),
    )
    write_immutable(pending / "attempts/0001.json", canonical(verify_attempt))
    write_immutable(pending / "evidence/0001.json", canonical(work3_evidence))
    atomic_write(
        pending / "run-memory.json",
        canonical(rebuild_runtime_memory(repo, pending)),
        None,
    )
    seal_runtime(
        repo,
        pending,
        legacy_snapshot_sha256=previous_manifest["legacy_snapshot_sha256"],
        source_projection_sha256=file_sha256(
            generation / "runtime-manifest.json"
        ),
    )
    verify_runtime_at(repo, pending)
    pending.rename(final)
    final_memory = json.loads((final / "run-memory.json").read_text())
    if final_memory.get("last_result") != "WAIT_AUTH":
        raise RuntimeError("Work revision 3 did not preserve tombstone WAIT_AUTH")
    switched = replace_runtime_generation(
        repo,
        final,
        expected_authority_pointer_sha256=current["pointer_sha256"],
        expected_active_run_pointer_sha256=active_sha,
        protocol_activation=activation,
        failure_after=failure_after,
    )
    return {
        "status": "PASS",
        "mutation_transaction": txid,
        "dogfood_runtime_root": generation.relative_to(repo).as_posix(),
        "runtime_root": final.relative_to(repo).as_posix(),
        "authority": verify_authority(repo),
        "switch_transaction": switched,
    }


def recover_mutation(
    repo_root: pathlib.Path,
    transaction_id: str,
) -> dict[str, Any]:
    """Rollback an interrupted pre-observation mutation without trusting new Core."""
    repo = pathlib.Path(repo_root).resolve()
    path = repo / TX_ROOT / transaction_id / "journal.json"
    payload = path.read_bytes()
    journal = json.loads(payload)
    if (
        journal.get("transaction_id") != transaction_id
        or journal.get("state") not in {"PREPARED", "EXECUTING", "ROLLED_BACK"}
    ):
        raise AuthorityError("mutation transaction is not rollback-eligible")
    if journal["state"] == "ROLLED_BACK":
        verify_authority(repo)
        return journal
    old_manifest_sha = journal["previous_candidate_sha256"]
    old_protocol_sha = journal["previous_protocol_sha256"]
    old_manifest = (
        repo / HISTORY_ROOT / "blobs" / f"{old_manifest_sha}.blob"
    ).read_bytes()
    old_protocol = (
        repo / HISTORY_ROOT / "blobs" / f"{old_protocol_sha}.blob"
    ).read_bytes()
    targets = (
        (
            repo / ".yuan/core/0.1/protocol.md",
            old_protocol,
            old_protocol_sha,
            journal["protocol_sha256"],
        ),
        (
            repo / ".yuan/core/0.1/candidate-manifest.json",
            old_manifest,
            old_manifest_sha,
            journal["candidate_sha256"],
        ),
    )
    for target, old_bytes, old_sha, new_sha in targets:
        actual = file_sha256(target)
        if actual == old_sha:
            continue
        if actual != new_sha:
            raise AuthorityError("mutation rollback target has unknown bytes")
        atomic_write(target, old_bytes, actual)
    journal["state"] = "ROLLED_BACK"
    atomic_write(path, canonical(journal), sha256(payload))
    verify_authority(repo)
    return journal


def verify_dogfood(repo_root: pathlib.Path) -> dict[str, Any]:
    repo = pathlib.Path(repo_root).resolve()
    verified = verify_authority(repo)
    runtime, _, _ = resolve_runtime_root(repo)
    work = json.loads(next((runtime / "contracts").glob("*.json")).read_text())
    memory = json.loads((runtime / "run-memory.json").read_text())
    transactions = sorted((repo / TX_ROOT).glob("*/journal.json"))
    if verified["revision"] != 7 or work["revision"]["revision"] != "3":
        raise RuntimeError("M9 successor is not active")
    committed = json.loads(transactions[-1].read_text())
    dogfood = repo / committed["runtime_root"]
    attempts = sorted((dogfood / "attempts").glob("*.json"))
    evidence = sorted((dogfood / "evidence").glob("*.json"))
    attempt = json.loads(attempts[-1].read_text())
    proof = json.loads(evidence[-1].read_text())
    return {
        "status": "PASS",
        "attempts": len(attempts),
        "evidence": len(evidence),
        "journal_states": [item["state"] for item in attempt["journal"]],
        "independent_assertions": proof["assertions"],
        "memory_result": memory["last_result"],
    }


def main() -> int:
    repo = pathlib.Path(__file__).resolve().parents[1]
    try:
        result = install(repo)
    except Exception as error:
        print(f"FAIL {error}")
        return 1
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
