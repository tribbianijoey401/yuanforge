"""Deterministic reconstruction of bounded Run Memory from immutable history."""

from __future__ import annotations

from typing import Any, Callable

from trust_semantics import canonical_digest, immutable_binding_matches


def _collection_digest(items: list[dict[str, Any]]) -> str:
    return canonical_digest(items)


def _blocked(
    work: dict[str, Any],
    artifact_sha256: str,
    environment_id: str,
    environment_fingerprint: str,
    attempts_digest: str,
    evidence_digest: str,
    attempt_ids: list[str],
    evidence_ids: list[str],
    errors: list[str],
) -> dict[str, Any]:
    return {
        "schema_version": "yuan.run-memory/v1",
        "run_id": f"RUN-{work.get('work_id', 'invalid')}",
        "projection_sequence": len(attempt_ids) + len(evidence_ids),
        "work_binding": work.get("revision", {}),
        "protocol_binding": work.get("protocol_binding", {}),
        "artifact_binding": {"scope": ".", "sha256": artifact_sha256},
        "environment_binding": {
            "id": environment_id,
            "fingerprint": environment_fingerprint,
        },
        "remaining_budget": work.get(
            "budget",
            {"ticks": 0, "tool_calls": 0, "strategies": 0, "command_seconds": 0},
        ),
        "ac_evidence": {},
        "active_hypotheses": [],
        "pending_side_effects": [],
        "attempted_strategies": [],
        "legal_next_steps": [],
        "last_result": "BLOCKED",
        "rebuild": {
            "attempt_ids": attempt_ids,
            "evidence_ids": evidence_ids,
            "attempts_digest": attempts_digest,
            "evidence_digest": evidence_digest,
            "errors": sorted(set(errors)),
        },
    }


def rebuild(
    work: dict[str, Any],
    attempts: list[dict[str, Any]],
    evidence_items: list[dict[str, Any]],
    *,
    current_artifact_sha256: str,
    environment_id: str,
    environment_fingerprint: str,
    trusted_now: Any,
    validate_document: Callable[[str, dict[str, Any]], Any],
    work_revision_valid: Callable[[dict[str, Any]], bool],
    completion_satisfied: Callable[..., bool],
    expected_attempts_digest: str | None = None,
    expected_evidence_digest: str | None = None,
) -> dict[str, Any]:
    attempt_ids = [item.get("attempt_id", "") for item in attempts]
    evidence_ids = [item.get("evidence_id", "") for item in evidence_items]
    attempts_digest = _collection_digest(attempts)
    evidence_digest = _collection_digest(evidence_items)
    errors: list[str] = []
    if validate_document("work-contract", work).errors or not work_revision_valid(work):
        errors.append("INVALID_WORK")
    if expected_attempts_digest not in {None, attempts_digest}:
        errors.append("ATTEMPTS_DIGEST_MISMATCH")
    if expected_evidence_digest not in {None, evidence_digest}:
        errors.append("EVIDENCE_DIGEST_MISMATCH")
    if len(attempt_ids) != len(set(attempt_ids)) or any(not item for item in attempt_ids):
        errors.append("AMBIGUOUS_ATTEMPT_ID")
    if len(evidence_ids) != len(set(evidence_ids)) or any(not item for item in evidence_ids):
        errors.append("AMBIGUOUS_EVIDENCE_ID")
    sequences = [item.get("sequence") for item in attempts]
    if sequences != list(range(1, len(attempts) + 1)):
        errors.append("ATTEMPT_ORDER_INVALID")
    evidence_sequences = [item.get("sequence") for item in evidence_items]
    if evidence_sequences != list(range(1, len(evidence_items) + 1)):
        errors.append("EVIDENCE_ORDER_INVALID")
    evidence_by_id = {item.get("evidence_id"): item for item in evidence_items}
    attempts_by_id = {item.get("attempt_id"): item for item in attempts}
    for attempt in attempts:
        if validate_document("attempt", attempt).errors:
            errors.append("INVALID_ATTEMPT")
        if not immutable_binding_matches(attempt.get("work_binding"), work.get("revision")):
            errors.append("ATTEMPT_WORK_MISMATCH")
        if not immutable_binding_matches(
            attempt.get("protocol_binding"), work.get("protocol_binding")
        ):
            errors.append("ATTEMPT_PROTOCOL_MISMATCH")
        if not immutable_binding_matches(
            attempt.get("harness_binding"), work.get("harness_binding")
        ):
            errors.append("ATTEMPT_HARNESS_MISMATCH")
        if any(item not in evidence_by_id for item in attempt.get("evidence_ids", [])):
            errors.append("MISSING_EVIDENCE_HISTORY")
    for evidence in evidence_items:
        if validate_document("evidence", evidence).errors:
            errors.append("INVALID_EVIDENCE")
        source = evidence.get("source_attempt_id")
        if source not in attempts_by_id:
            errors.append("MISSING_ATTEMPT_HISTORY")
        elif evidence.get("evidence_id") not in attempts_by_id[source].get("evidence_ids", []):
            errors.append("EVIDENCE_SOURCE_MISMATCH")
        if not immutable_binding_matches(evidence.get("work_binding"), work.get("revision")):
            errors.append("EVIDENCE_WORK_MISMATCH")
    if errors:
        return _blocked(
            work,
            current_artifact_sha256,
            environment_id,
            environment_fingerprint,
            attempts_digest,
            evidence_digest,
            attempt_ids,
            evidence_ids,
            errors,
        )
    remaining = dict(work["budget"])
    for attempt in attempts:
        for field in remaining:
            remaining[field] -= attempt["budget_charge"][field]
    if any(value < 0 for value in remaining.values()):
        errors.append("BUDGET_HISTORY_INVALID")
    pending = [
        {"attempt_id": item["attempt_id"], "state": item["side_effect_state"]}
        for item in attempts
        if item["side_effect_state"] not in {"COMMITTED", "NOT_APPLICABLE"}
    ]
    if any(item["state"] == "UNKNOWN" for item in pending):
        errors.append("UNKNOWN_SIDE_EFFECT")
    if errors:
        return _blocked(
            work,
            current_artifact_sha256,
            environment_id,
            environment_fingerprint,
            attempts_digest,
            evidence_digest,
            attempt_ids,
            evidence_ids,
            errors,
        )
    ac_evidence: dict[str, list[str]] = {}
    safety: dict[str, bool] = {}
    for evidence in evidence_items:
        ac_evidence.setdefault(evidence["ac_id"], []).append(evidence["evidence_id"])
        for check in evidence["checks"]:
            if check["id"].startswith("SAFE-"):
                safety[check["id"]] = check["status"] == "PASS"
    completed = completion_satisfied(
        work,
        evidence_items,
        current_artifact_sha256=current_artifact_sha256,
        environment_id=environment_id,
        environment_fingerprint=environment_fingerprint,
        side_effect_states=[item["side_effect_state"] for item in attempts],
        safety_invariants=safety,
        trusted_now=trusted_now,
    )
    result = "COMPLETE" if completed else "CONTINUE"
    if any(value == 0 for value in remaining.values()) and not completed:
        result = "BUDGET_EXIT"
    hypotheses = [
        {
            "id": f"HYP-{item['attempt_id']}",
            "claim": item["hypothesis"]["claim"],
            "falsification": item["hypothesis"]["falsification"],
        }
        for item in attempts[-3:]
        if item["outcome"] != "SUCCEEDED"
    ]
    return {
        "schema_version": "yuan.run-memory/v1",
        "run_id": f"RUN-{work['work_id']}",
        "projection_sequence": len(attempts) + len(evidence_items),
        "work_binding": work["revision"],
        "protocol_binding": work["protocol_binding"],
        "artifact_binding": {
            "scope": evidence_items[-1]["artifact_binding"]["scope"],
            "sha256": current_artifact_sha256,
        },
        "environment_binding": {
            "id": environment_id,
            "fingerprint": environment_fingerprint,
        },
        "remaining_budget": remaining,
        "ac_evidence": ac_evidence,
        "active_hypotheses": hypotheses,
        "pending_side_effects": pending,
        "attempted_strategies": [
            {
                "fingerprint": item["strategy_fingerprint"],
                "relevant_inputs_digest": canonical_digest(item["relevant_inputs"]),
                "latest_evidence_sequence": max(
                    (
                        index + 1
                        for index, evidence in enumerate(evidence_items)
                        if evidence["source_attempt_id"] == item["attempt_id"]
                    ),
                    default=0,
                ),
            }
            for item in attempts
        ],
        "legal_next_steps": [],
        "last_result": result,
        "rebuild": {
            "attempt_ids": attempt_ids,
            "evidence_ids": evidence_ids,
            "attempts_digest": attempts_digest,
            "evidence_digest": evidence_digest,
            "errors": [],
        },
    }
