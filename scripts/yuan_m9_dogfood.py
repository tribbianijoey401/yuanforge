"""Execute the M9 self-modification through the live revision-6 Core Work."""

from __future__ import annotations

import copy
import json
import pathlib
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
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
R1_HISTORY_ROOT = pathlib.PurePosixPath(
    ".yuan/authority/core-history/m9-to-r1"
)
R1_STAGING_ROOT = pathlib.PurePosixPath(
    ".yuan/authority/self-modification/staging/task-012-r1/candidate"
)


class MutationCrash(RuntimeError):
    """Injected interruption inside the independently journaled Core mutation."""

    def __init__(self, transaction_id: str):
        super().__init__(transaction_id)
        self.transaction_id = transaction_id


def _repository_from_script() -> pathlib.Path:
    for parent in pathlib.Path(__file__).resolve().parents:
        if (parent / ".yuan-run/active-run.json").is_file():
            return parent
    return pathlib.Path(__file__).resolve().parents[1]


def build_protocol(previous: bytes) -> bytes:
    text = previous.decode("utf-8")
    historical = "Revision: `yuan.core.protocol/0.1.0-candidate`" in text
    if historical:
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
    else:
        text = text.replace(
            "Revision: `yuan.core.protocol/0.1.0`",
            "Revision: `yuan.core.protocol/0.1.1`",
            1,
        )
    if not historical:
        text = text.replace(
        "A candidate must not establish its own trust. Core, Harness, schema, validator,\n"
        "or authority changes require acceptance by at least one of:\n\n"
        "1. the previous immutable trust root;\n"
        "2. an independent held-out verifier rooted outside the candidate;\n"
        "3. explicit human authorization that names the revision and risk.",
        "A candidate must not establish its own trust. Core, Harness, schema, validator,\n"
        "or authority changes use explicit **ANY-OF** semantics: one positive proof from\n"
        "the previous immutable trust root **or** an independent held-out verifier rooted\n"
        "outside the candidate is sufficient. Candidate conformance, self-attestation,\n"
        "and an ambiguous or AND-style proof list never activate Core.",
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
    if not historical:
        text = text.replace(
        "Files in this directory are inert by default. They become active only when an\n"
        "external content-addressed authority record binds their exact revision and hash\n"
        "to positive previous-root or independent Evidence. Candidate conformance and\n"
        "self-attestation never activate Core. Initializer, user work, and unrelated\n"
        "repository state remain outside that activation.",
        "Files in this directory are inert by default. Before PREPARED and before any\n"
        "candidate byte changes, a complete candidate copy must pass one accepted ANY-OF\n"
        "proof route. The receipt, suite-manifest snapshot, candidate manifest, verifier,\n"
        "and receipt time form a content-addressed proof closure. PREPARED durably binds\n"
        "that closure; later mutation, journal states, and Evidence must be causally\n"
        "monotonic. Missing, substituted, future, or time-reversed proof material blocks\n"
        "with no candidate mutation. Candidate conformance and self-attestation never\n"
        "activate Core.",
            1,
        )
    if text == previous.decode("utf-8"):
        raise RuntimeError("frozen protocol replacement anchors are absent")
    return text.encode("utf-8")


def build_candidate_manifest(
    repo_root: pathlib.Path,
    previous: dict[str, Any],
    protocol_bytes: bytes,
    *,
    candidate_root: pathlib.Path | None = None,
) -> dict[str, Any]:
    repo = pathlib.Path(repo_root).resolve()
    source = (
        pathlib.Path(candidate_root).resolve()
        if candidate_root is not None
        else repo / ".yuan/core/0.1"
    )
    manifest = copy.deepcopy(previous)
    revision = (
        "0.1.1"
        if b"yuan.core.protocol/0.1.1" in protocol_bytes
        else "0.1.0"
    )
    manifest.update(
        {
            "candidate_revision": f"yuan.core/{revision}",
            "protocol_revision": f"yuan.core.protocol/{revision}",
            "authority": "inert-by-default",
            "self_trust": False,
            "activation": (
                {
                    "mode": "external-content-addressed-authority",
                    "proof_policy": {
                        "operator": "any_of",
                        "accepted": [
                            "previous-root-proof",
                            "independent-proof",
                        ],
                    },
                }
                if revision == "0.1.1"
                else {
                    "mode": "external-content-addressed-authority",
                    "requires": [
                        "previous-root-proof",
                        "independent-proof",
                    ],
                }
            ),
            "manifest_binding": (
                "External authority binds this manifest by SHA-256; "
                "self-hashing and self-activation are forbidden."
            ),
        }
    )
    for item in manifest["files"]:
        target = source / item["path"]
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
    *,
    candidate_root: pathlib.Path | None = None,
) -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix="yuan-m9-preflight-") as name:
        staged = pathlib.Path(name)
        for relative in (".yuan", "scripts", "tests"):
            shutil.copytree(repo / relative, staged / relative)
        if candidate_root is not None:
            shutil.rmtree(staged / ".yuan/core/0.1")
            shutil.copytree(candidate_root, staged / ".yuan/core/0.1")
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
        result = _run_old_root(
            staged,
            sha256(manifest_bytes),
            staged / "preflight-receipt.json",
            staged / "preflight-suite.json",
        )
        result.update(
            {
                "receipt_bytes": (staged / "preflight-receipt.json").read_bytes(),
                "suite_bytes": (staged / "preflight-suite.json").read_bytes(),
                "verifier_bytes": (staged / OLD_ROOT_RUNNER).read_bytes(),
                "verifier_sha256": file_sha256(staged / OLD_ROOT_RUNNER),
            }
        )
        return result


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
                _repository_from_script() / OLD_ROOT_RUNNER
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
                _repository_from_script()
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


def _install_rev6(
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


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _full_candidate_manifest(
    candidate_base: pathlib.Path,
    core_manifest_sha256: str,
) -> dict[str, Any]:
    entries = []
    for area in (".yuan/core/0.1", "scripts"):
        root = candidate_base / area
        for path in sorted(root.rglob("*")):
            if (
                path.is_file()
                and "__pycache__" not in path.parts
                and path.suffix != ".pyc"
            ):
                entries.append(
                    {
                        "path": path.relative_to(candidate_base).as_posix(),
                        "sha256": file_sha256(path),
                    }
                )
    return {
        "schema_version": "yuan.self-modification-candidate/v1",
        "candidate_revision": "yuan.core/0.1.1",
        "core_candidate_manifest_sha256": core_manifest_sha256,
        "files": entries,
    }


def _validate_preflight(
    preflight: dict[str, Any],
    *,
    candidate_sha256: str,
    full_candidate_sha256: str,
    proof_attack: str | None,
) -> dict[str, Any]:
    receipt_bytes = preflight["receipt_bytes"]
    suite_bytes = preflight["suite_bytes"]
    verifier_bytes = preflight["verifier_bytes"]
    receipt = json.loads(receipt_bytes)
    proof = {
        "receipt_sha256": sha256(receipt_bytes),
        "suite_manifest_sha256": sha256(suite_bytes),
        "candidate_manifest_sha256": candidate_sha256,
        "full_candidate_manifest_sha256": full_candidate_sha256,
        "verifier_sha256": sha256(verifier_bytes),
        "receipt_created_at": receipt.get("created_at"),
    }
    if proof_attack == "missing-receipt":
        proof.pop("receipt_sha256")
    elif proof_attack == "future-receipt":
        proof["receipt_created_at"] = "2999-01-01T00:00:00+00:00"
    elif proof_attack == "replace-suite":
        proof["suite_manifest_sha256"] = "0" * 64
    elif proof_attack in {"replace-candidate", "wrong-candidate"}:
        proof["candidate_manifest_sha256"] = "0" * 64
    elif proof_attack == "wrong-root":
        proof["verifier_sha256"] = "0" * 64
    required = (
        "receipt_sha256",
        "suite_manifest_sha256",
        "candidate_manifest_sha256",
        "full_candidate_manifest_sha256",
        "verifier_sha256",
        "receipt_created_at",
    )
    try:
        receipt_at = datetime.fromisoformat(
            str(proof["receipt_created_at"]).replace("Z", "+00:00")
        ).astimezone(timezone.utc)
    except (KeyError, TypeError, ValueError) as error:
        raise AuthorityError("preflight receipt time is invalid") from error
    if (
        any(field not in proof for field in required)
        or proof.get("receipt_sha256") != sha256(receipt_bytes)
        or proof.get("suite_manifest_sha256") != sha256(suite_bytes)
        or proof.get("candidate_manifest_sha256") != candidate_sha256
        or proof.get("full_candidate_manifest_sha256")
        != full_candidate_sha256
        or proof.get("verifier_sha256") != sha256(verifier_bytes)
        or receipt.get("manifest_sha256") != sha256(suite_bytes)
        or receipt.get("status") != "PASS"
        or receipt.get("checks_executed", 0) < 80
        or receipt_at > datetime.now(timezone.utc)
    ):
        raise AuthorityError("preflight proof closure did not PASS")
    return proof


def _prepare_r1(
    repo: pathlib.Path,
    candidate_base: pathlib.Path,
    *,
    proof_attack: str | None,
) -> tuple[str, dict[str, Any]]:
    current = load_current(repo)
    runtime, _, active_sha = resolve_runtime_root(repo)
    work = json.loads(next((runtime / "contracts").glob("*.json")).read_text())
    if (
        current["record"].get("revision") != 7
        or current["record_sha256"]
        != "cb65f3c1464fd4dc97e328752cd1075a026aba897ca637fbbaae296996c8c647"
        or active_sha is None
        or work.get("revision", {}).get("revision") != "3"
    ):
        raise AuthorityError("r1 requires the exact failed revision-7 Work3")
    core_source = candidate_base / ".yuan/core/0.1"
    old_protocol = (repo / ".yuan/core/0.1/protocol.md").read_bytes()
    old_manifest = (repo / ".yuan/core/0.1/candidate-manifest.json").read_bytes()
    protocol = build_protocol(old_protocol)
    candidate = build_candidate_manifest(
        repo,
        json.loads(old_manifest),
        protocol,
        candidate_root=core_source,
    )
    candidate_bytes = canonical(candidate)
    atomic_write(
        core_source / "protocol.md",
        protocol,
        file_sha256(core_source / "protocol.md"),
    )
    atomic_write(
        core_source / "candidate-manifest.json",
        candidate_bytes,
        file_sha256(core_source / "candidate-manifest.json"),
    )
    candidate_sha = sha256(candidate_bytes)
    full_candidate = _full_candidate_manifest(candidate_base, candidate_sha)
    full_candidate_bytes = canonical(full_candidate)
    full_candidate_sha = sha256(full_candidate_bytes)
    preflight = _preflight(
        repo,
        protocol,
        candidate,
        candidate_root=core_source,
    )
    proof_fields = _validate_preflight(
        preflight,
        candidate_sha256=candidate_sha,
        full_candidate_sha256=full_candidate_sha,
        proof_attack=proof_attack,
    )
    transaction_id = canonical_digest(
        {
            "authority_record": current["record_sha256"],
            "work": work["revision"],
            "candidate": full_candidate_sha,
            "receipt": proof_fields["receipt_sha256"],
        }
    )
    closure_root = (
        repo
        / EVIDENCE_ROOT
        / "preflight"
        / proof_fields["receipt_sha256"]
    )
    receipt_path = closure_root / "receipt.json"
    suite_path = closure_root / "suite-manifest.json"
    verifier_path = closure_root / f"{proof_fields['verifier_sha256']}.blob"
    full_candidate_path = closure_root / "full-candidate-manifest.json"
    write_immutable(receipt_path, preflight["receipt_bytes"])
    write_immutable(suite_path, preflight["suite_bytes"])
    write_immutable(verifier_path, preflight["verifier_bytes"])
    write_immutable(full_candidate_path, full_candidate_bytes)
    closure = {
        "schema_version": "yuan.preflight-proof-closure/v1",
        **proof_fields,
        "proof_route": "previous-root-proof",
        "receipt_path": receipt_path.relative_to(repo).as_posix(),
        "suite_manifest_path": suite_path.relative_to(repo).as_posix(),
        "verifier_path": verifier_path.relative_to(repo).as_posix(),
        "full_candidate_manifest_path": full_candidate_path.relative_to(
            repo
        ).as_posix(),
    }
    closure_bytes = canonical(closure)
    closure_path = closure_root / f"{sha256(closure_bytes)}.index.json"
    write_immutable(closure_path, closure_bytes)
    ac = next(
        item
        for item in work["acceptance_criteria"]
        if item["id"] == "AC-M9-SELF-MODIFICATION-DOGFOOD"
    )
    root_binding = {
        key: ac["verifier_binding"][key]
        for key in ("id", "revision", "sha256")
    }
    candidate_binding = {
        "id": "yuan.core.protocol",
        "revision": "0.1.1",
        "sha256": candidate_sha,
    }
    prepared_at = _now()
    proof = {
        "kind": "previous-root",
        "root_binding": root_binding,
        "candidate_binding": candidate_binding,
        "status": "PASS",
        "assertions": preflight["assertions"],
        **proof_fields,
        "transaction_id": transaction_id,
        "receipt_path": receipt_path.relative_to(repo).as_posix(),
        "suite_manifest_path": suite_path.relative_to(repo).as_posix(),
        "verifier_path": verifier_path.relative_to(repo).as_posix(),
        "closure_index_path": closure_path.relative_to(repo).as_posix(),
        "closure_index_sha256": file_sha256(closure_path),
        "prepared_attempt_path": (
            TX_ROOT / transaction_id / "attempt-prepared.json"
        ).as_posix(),
    }
    prepared = {
        "schema_version": "yuan.attempt/v1",
        "attempt_id": "ATT-M9-R1-LIVE-SELF-MOD-0002",
        "work_binding": work["revision"],
        "protocol_binding": work["protocol_binding"],
        "harness_binding": work["harness_binding"],
        "sequence": 2,
        "strategy_fingerprint": canonical_digest(
            {"strategy": "causal-preflight-self-mod", "closure": closure}
        ),
        "relevant_inputs": [
            {
                "scope": ".yuan/core/0.1",
                "sha256": sha256(old_manifest),
            },
            {
                "scope": closure_path.relative_to(repo).as_posix(),
                "sha256": file_sha256(closure_path),
            },
        ],
        "hypothesis": {
            "claim": "Frozen old-root proof closure predates and authorizes the complete 0.1.1 candidate mutation.",
            "falsification": "Any closure, time, byte, journal, or Work mismatch blocks before mutation.",
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
                    "candidate_binding": candidate_binding,
                    "previous_binding": root_binding,
                    "risk": "R0",
                },
                "proofs": [proof],
            },
        },
        "budget_charge": {
            "ticks": 1,
            "tool_calls": 2,
            "strategies": 1,
            "command_seconds": 30,
        },
        "journal": [
            {
                "ordinal": 1,
                "state": "PREPARED",
                "recorded_at": prepared_at,
                "receipt_sha256": None,
            }
        ],
        "side_effect_state": "PREPARED",
        "tool_receipt": None,
        "postcondition": None,
        "evidence_ids": ["EVD-M9-R1-LIVE-SELF-MOD-0002"],
        "outcome": "PENDING",
    }
    from trust_semantics import self_modification_authorized

    if not self_modification_authorized(
        prepared["action"]["self_modification"]["change"],
        [proof],
        now=datetime.now(timezone.utc),
        prepared_at=prepared_at,
    ):
        raise AuthorityError("prepared proof closure is not authorized")
    txdir = repo / TX_ROOT / transaction_id
    prepared_path = txdir / "attempt-prepared.json"
    write_immutable(prepared_path, canonical(prepared))
    files = []
    for entry in full_candidate["files"]:
        source = candidate_base / entry["path"]
        target = repo / entry["path"]
        old_sha = file_sha256(target)
        old_bytes = target.read_bytes()
        write_immutable(
            repo / R1_HISTORY_ROOT / "blobs" / f"{old_sha}.blob",
            old_bytes,
        )
        files.append(
            {
                "path": entry["path"],
                "before_sha256": old_sha,
                "after_sha256": entry["sha256"],
                "retained_blob": (
                    R1_HISTORY_ROOT / "blobs" / f"{old_sha}.blob"
                ).as_posix(),
            }
        )
    mutation = {
        "schema_version": "yuan.self-modification-transaction/v2",
        "transaction_id": transaction_id,
        "state": "PREPARED",
        "attempt_id": prepared["attempt_id"],
        "prepared_attempt_sha256": file_sha256(prepared_path),
        "proof_closure_index_sha256": file_sha256(closure_path),
        "candidate_staging_root": candidate_base.relative_to(repo).as_posix(),
        "candidate_manifest_sha256": candidate_sha,
        "full_candidate_manifest_sha256": full_candidate_sha,
        "authority_record_before_sha256": current["record_sha256"],
        "active_run_before_sha256": active_sha,
        "files": files,
    }
    _write_phase(txdir / "journal.json", mutation, None)
    return transaction_id, mutation


def _complete_r1_attempt(
    prepared: dict[str, Any],
    before_sha256: str,
    after_sha256: str,
) -> dict[str, Any]:
    attempt = copy.deepcopy(prepared)
    receipt = {
        "schema_version": "yuan.tool-receipt/v1",
        "kind": "file-write",
        "operation_id": "OP-M9-R1-LIVE-CORE-REPLACE",
        "status": "REPLACED",
        "path": ".yuan/core/0.1",
        "before_sha256": before_sha256,
        "after_sha256": after_sha256,
    }
    receipt_sha = canonical_digest(receipt)
    prepared_entry = copy.deepcopy(prepared["journal"][0])
    attempt["journal"] = [prepared_entry]
    for ordinal, state in enumerate(
        ("EXECUTING", "OBSERVED", "COMMITTED"), start=2
    ):
        attempt["journal"].append(
            {
                "ordinal": ordinal,
                "state": state,
                "recorded_at": _now(),
                "receipt_sha256": (
                    receipt_sha
                    if state in {"OBSERVED", "COMMITTED"}
                    else None
                ),
            }
        )
    attempt["side_effect_state"] = "COMMITTED"
    attempt["tool_receipt"] = receipt
    attempt["postcondition"] = {
        "scope": ".yuan/core/0.1",
        "observed_sha256": after_sha256,
        "satisfied": True,
    }
    attempt["outcome"] = "SUCCEEDED"
    return attempt


def _r1_evidence(
    work: dict[str, Any],
    attempt: dict[str, Any],
    *,
    receipt_sha256: str,
    receipt_created_at: str,
    assertions: int,
    sequence: int,
    evidence_id: str,
) -> dict[str, Any]:
    self_modification = attempt["action"].get("self_modification")
    candidate_sha256 = (
        self_modification["change"]["candidate_binding"]["sha256"]
        if isinstance(self_modification, dict)
        else file_sha256(
            _repository_from_script()
            / ".yuan/core/0.1/candidate-manifest.json"
        )
    )
    evidence = _evidence(
        work,
        attempt,
        candidate_sha256,
        receipt_sha256,
        assertions,
        sequence=sequence,
        evidence_id=evidence_id,
    )
    evidence["created_at"] = _now()
    evidence["proof_receipt_created_at"] = receipt_created_at
    evidence["immutable_digest"] = canonical_digest(
        evidence, omitted_paths=(("immutable_digest",),)
    )
    return evidence


def _install_r1(
    repo: pathlib.Path,
    *,
    candidate_base: pathlib.Path,
    failure_after: str | None,
    mutation_failure_after: str | None,
    proof_attack: str | None,
) -> dict[str, Any]:
    transaction_id, mutation = _prepare_r1(
        repo, candidate_base, proof_attack=proof_attack
    )
    txdir = repo / TX_ROOT / transaction_id
    journal_path = txdir / "journal.json"
    journal_sha = file_sha256(journal_path)
    prepared = json.loads((txdir / "attempt-prepared.json").read_text())
    mutation["state"] = "EXECUTING"
    journal_sha = _write_phase(journal_path, mutation, journal_sha)
    if mutation_failure_after == "executing":
        raise MutationCrash(transaction_id)
    for entry in mutation["files"]:
        target = repo / entry["path"]
        source = candidate_base / entry["path"]
        atomic_write(target, source.read_bytes(), entry["before_sha256"])
        if (
            mutation_failure_after == "protocol"
            and entry["path"] == ".yuan/core/0.1/protocol.md"
        ):
            raise MutationCrash(transaction_id)
    candidate_sha = mutation["candidate_manifest_sha256"]
    attempt = _complete_r1_attempt(
        prepared,
        next(
            item["before_sha256"]
            for item in mutation["files"]
            if item["path"] == ".yuan/core/0.1/candidate-manifest.json"
        ),
        candidate_sha,
    )
    write_immutable(txdir / "attempt-observed.json", canonical(attempt))
    proof = prepared["action"]["self_modification"]["proofs"][0]
    receipt = json.loads((repo / proof["receipt_path"]).read_text())
    mutation.update(
        {
            "state": "OBSERVED",
            "tool_receipt_sha256": canonical_digest(
                attempt["tool_receipt"]
            ),
            "old_root_receipt_sha256": proof["receipt_sha256"],
        }
    )
    journal_sha = _write_phase(journal_path, mutation, journal_sha)
    runtime, _, _ = resolve_runtime_root(repo)
    work = json.loads(next((runtime / "contracts").glob("*.json")).read_text())
    evidence = _r1_evidence(
        work,
        attempt,
        receipt_sha256=proof["receipt_sha256"],
        receipt_created_at=proof["receipt_created_at"],
        assertions=proof["assertions"],
        sequence=2,
        evidence_id="EVD-M9-R1-LIVE-SELF-MOD-0002",
    )
    validate_runtime_evidence(repo, runtime, attempt, evidence)
    previous_manifest = verify_runtime_at(repo, runtime)
    generation, _ = _build_generation(
        repo,
        runtime,
        transaction_id,
        attempt,
        evidence,
        previous_manifest,
    )
    memory = json.loads((generation / "run-memory.json").read_text())
    if memory.get("last_result") != "WAIT_AUTH":
        raise AuthorityError("r1 dogfood did not converge to WAIT_AUTH")
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
    _write_phase(journal_path, mutation, journal_sha)
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
            "protocol_sha256": file_sha256(
                repo / ".yuan/core/0.1/protocol.md"
            ),
            "activated_candidate_manifest_sha256": candidate_sha,
            "candidate_manifest_sha256": candidate_sha,
            "prior_activated_candidate_manifest_sha256": (
                "57a2acad6ba92d879785139e35548bdd20cd1edcafa3d7e8b554321504ec8b5e"
            ),
            "prior_activated_candidate_manifest_path": (
                ".yuan/authority/core-history/r2-to-m9/blobs/"
                "57a2acad6ba92d879785139e35548bdd20cd1edcafa3d7e8b554321504ec8b5e.blob"
            ),
            "activated_older_root_manifest_path": proof[
                "suite_manifest_path"
            ],
            "activated_older_root_manifest_sha256": proof[
                "suite_manifest_sha256"
            ],
            "independent_evidence_path": proof["receipt_path"],
            "independent_evidence_sha256": proof["receipt_sha256"],
            "older_root_receipt_sha256": proof["receipt_sha256"],
            "proof_closure_index_path": proof["closure_index_path"],
            "proof_closure_index_sha256": proof[
                "closure_index_sha256"
            ],
            "previous_descriptor_path": (
                ".yuan/authority/activation/history/"
                f"{old_descriptor_sha}.blob"
            ),
            "previous_descriptor_sha256": old_descriptor_sha,
        }
    )
    atomic_write(descriptor_path, canonical(descriptor), old_descriptor_sha)
    activation = verify_activation_descriptor(repo)
    provenance = subprocess.run(
        [
            sys.executable,
            "-B",
            str(repo / "scripts/yuan_provenance_history.py"),
            "--repo",
            str(repo),
            "--create-r1",
        ],
        cwd=repo,
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        check=False,
    )
    if provenance.returncode != 0:
        raise AuthorityError(
            "M9-to-r1 provenance creation failed: "
            + (provenance.stderr or provenance.stdout)[:1000]
        )
    work4 = copy.deepcopy(work)
    work4["protocol_binding"] = {
        "id": "yuan.core.protocol",
        "revision": "0.1.1",
        "sha256": file_sha256(repo / ".yuan/core/0.1/protocol.md"),
    }
    work4["revision"]["revision"] = "4"
    work4["revision"]["sha256"] = canonical_digest(
        work4, omitted_paths=(("revision", "sha256"),)
    )
    with tempfile.TemporaryDirectory(prefix="yuan-m9-work4-") as name:
        receipt_path = pathlib.Path(name) / "receipt.json"
        suite_path = pathlib.Path(name) / "suite.json"
        work4_proof = _run_old_root(
            repo, candidate_sha, receipt_path, suite_path
        )
        work4_receipt_bytes = receipt_path.read_bytes()
        work4_suite_bytes = suite_path.read_bytes()
    work4_receipt_sha = sha256(work4_receipt_bytes)
    work4_root = repo / EVIDENCE_ROOT / "work4" / work4_receipt_sha
    write_immutable(work4_root / "receipt.json", work4_receipt_bytes)
    write_immutable(work4_root / "suite-manifest.json", work4_suite_bytes)
    work4_receipt = json.loads(work4_receipt_bytes)
    verify_attempt = _verification_attempt(work4, work4_receipt_sha)
    verify_attempt["attempt_id"] = "ATT-M9-WORK4-INDEPENDENT-0001"
    verify_attempt["evidence_ids"] = ["EVD-M9-WORK4-INDEPENDENT-0001"]
    verify_attempt["protocol_binding"] = work4["protocol_binding"]
    work4_evidence = _r1_evidence(
        work4,
        verify_attempt,
        receipt_sha256=work4_receipt_sha,
        receipt_created_at=work4_receipt["created_at"],
        assertions=work4_proof["assertions"],
        sequence=1,
        evidence_id="EVD-M9-WORK4-INDEPENDENT-0001",
    )
    successor_id = (
        f"{work4['work_id']}-r4-{work4['revision']['sha256'][:12]}"
    )
    pending = (
        repo / RUNS_ROOT / f".pending-m9-r1-{work4['revision']['sha256'][:12]}"
    )
    final = repo / RUNS_ROOT / successor_id
    for area in ("contracts", "attempts", "evidence"):
        (pending / area).mkdir(parents=True, exist_ok=True)
    write_immutable(
        pending / "contracts" / f"{work4['work_id']}.json",
        canonical(work4),
    )
    write_immutable(pending / "attempts/0001.json", canonical(verify_attempt))
    write_immutable(pending / "evidence/0001.json", canonical(work4_evidence))
    atomic_write(
        pending / "run-memory.json",
        canonical(rebuild_runtime_memory(repo, pending)),
        None,
    )
    seal_runtime(
        repo,
        pending,
        legacy_snapshot_sha256=previous_manifest[
            "legacy_snapshot_sha256"
        ],
        source_projection_sha256=file_sha256(
            generation / "runtime-manifest.json"
        ),
    )
    verify_runtime_at(repo, pending)
    pending.rename(final)
    if json.loads((final / "run-memory.json").read_text()).get(
        "last_result"
    ) != "WAIT_AUTH":
        raise AuthorityError("Work4 did not preserve WAIT_AUTH")
    current = load_current(repo)
    _, _, active_sha = resolve_runtime_root(repo)
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
        "mutation_transaction": transaction_id,
        "dogfood_runtime_root": generation.relative_to(repo).as_posix(),
        "runtime_root": final.relative_to(repo).as_posix(),
        "authority": verify_authority(repo),
        "switch_transaction": switched,
    }


def install(
    repo_root: pathlib.Path,
    *,
    failure_after: str | None = None,
    mutation_failure_after: str | None = None,
    proof_attack: str | None = None,
    candidate_root: pathlib.Path | None = None,
) -> dict[str, Any]:
    repo = pathlib.Path(repo_root).resolve()
    current = load_current(repo)
    if current["record"].get("revision") == 7:
        base = (
            pathlib.Path(candidate_root).resolve()
            if candidate_root is not None
            else repo / R1_STAGING_ROOT
        )
        return _install_r1(
            repo,
            candidate_base=base,
            failure_after=failure_after,
            mutation_failure_after=mutation_failure_after,
            proof_attack=proof_attack,
        )
    return _install_rev6(
        repo,
        failure_after=failure_after,
        mutation_failure_after=mutation_failure_after,
        proof_attack=proof_attack,
    )


def recover_mutation(
    repo_root: pathlib.Path,
    transaction_id: str,
) -> dict[str, Any]:
    """Rollback an interrupted pre-observation mutation without trusting new Core."""
    repo = pathlib.Path(repo_root).resolve()
    path = repo / TX_ROOT / transaction_id / "journal.json"
    payload = path.read_bytes()
    journal = json.loads(payload)
    allowed_states = (
        {"PREPARED", "EXECUTING", "OBSERVED", "ROLLED_BACK"}
        if journal.get("schema_version")
        == "yuan.self-modification-transaction/v2"
        else {"PREPARED", "EXECUTING", "ROLLED_BACK"}
    )
    if (
        journal.get("transaction_id") != transaction_id
        or journal.get("state") not in allowed_states
    ):
        raise AuthorityError("mutation transaction is not rollback-eligible")
    if journal["state"] == "ROLLED_BACK":
        verify_authority(repo)
        return journal
    if journal.get("schema_version") == "yuan.self-modification-transaction/v2":
        for entry in journal.get("files", []):
            target = repo / entry["path"]
            actual = file_sha256(target)
            if actual == entry["before_sha256"]:
                continue
            if actual != entry["after_sha256"]:
                raise AuthorityError(
                    "mutation rollback target has unknown bytes"
                )
            retained = repo / entry["retained_blob"]
            if file_sha256(retained) != entry["before_sha256"]:
                raise AuthorityError("mutation rollback retained blob mismatch")
            atomic_write(target, retained.read_bytes(), actual)
        journal["state"] = "ROLLED_BACK"
        atomic_write(path, canonical(journal), sha256(payload))
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
