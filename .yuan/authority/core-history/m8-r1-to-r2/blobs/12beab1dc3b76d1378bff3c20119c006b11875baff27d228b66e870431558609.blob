"""Evidence validity and the sole Core completion predicate."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from document_validation import validate_document, work_revision_valid
from trust_semantics import (
    immutable_binding_matches,
    parse_trusted_time,
    trusted_now as resolve_trusted_now,
)


def _valid_evidence_for_ac(
    work: dict[str, Any],
    ac: dict[str, Any],
    evidence: dict[str, Any],
    artifact_sha256: str,
    environment_id: str,
    environment_fingerprint: str,
    observed_now: datetime,
) -> bool:
    binding = ac["verifier_binding"]
    not_after = evidence["freshness"].get("not_after")
    try:
        fresh = not_after is None or observed_now <= parse_trusted_time(not_after)
    except (TypeError, ValueError):
        fresh = False
    return (
        not validate_document("evidence", evidence).errors
        and immutable_binding_matches(evidence["work_binding"], work["revision"])
        and immutable_binding_matches(evidence["harness_binding"], work["harness_binding"])
        and evidence["status"] == "PASS"
        and evidence["ac_id"] == ac["id"]
        and evidence["kind"] == ac["type"]
        and evidence["assertions"] >= binding["minimum_assertions"]
        and evidence["artifact_binding"]["scope"] == ac["artifact_scope"]
        and evidence["artifact_binding"]["sha256"] == artifact_sha256
        and evidence["environment_binding"]["id"] == environment_id
        and evidence["environment_binding"]["fingerprint"] == environment_fingerprint
        and environment_id in binding["environment_ids"]
        and binding["environment_fingerprints"].get(environment_id)
        == environment_fingerprint
        and all(
            evidence["verifier_binding"][key] == binding[key]
            for key in ("id", "revision", "sha256", "trust_root_id")
        )
        and evidence["independence"]["independent"] is True
        and fresh
    )


def completion_satisfied(
    work: dict[str, Any],
    evidence_items: list[dict[str, Any]],
    *,
    current_artifact_sha256: str,
    environment_id: str,
    environment_fingerprint: str | None = None,
    side_effect_states: list[str],
    safety_invariants: dict[str, bool],
    trusted_now: datetime | None = None,
) -> bool:
    if validate_document("work-contract", work).errors or not work_revision_valid(work):
        return False
    if any(
        state not in {"COMMITTED", "NOT_APPLICABLE"}
        for state in side_effect_states
    ):
        return False
    required_safety = {item["id"] for item in work["safety_invariants"]}
    if any(safety_invariants.get(item) is not True for item in required_safety):
        return False
    observed_now = resolve_trusted_now(trusted_now)
    for ac in (item for item in work["acceptance_criteria"] if item["required"]):
        expected_fingerprint = ac["verifier_binding"]["environment_fingerprints"].get(
            environment_id
        )
        active_fingerprint = environment_fingerprint or expected_fingerprint
        if not isinstance(active_fingerprint, str) or not any(
            _valid_evidence_for_ac(
                work,
                ac,
                item,
                current_artifact_sha256,
                environment_id,
                active_fingerprint,
                observed_now,
            )
            for item in evidence_items
        ):
            return False
    return True
