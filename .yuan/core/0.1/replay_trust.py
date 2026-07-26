"""Trust and scope invariants applied during deterministic replay."""

from __future__ import annotations

from typing import Any

from trust_semantics import (
    immutable_binding_matches,
    self_modification_authorized,
)


def artifact_scope(
    work: dict[str, Any],
    attempts: list[dict[str, Any]],
    evidence_items: list[dict[str, Any]],
) -> str:
    candidates: list[Any] = []
    candidates.extend(
        item.get("artifact_binding", {}).get("scope")
        for item in reversed(evidence_items)
        if isinstance(item, dict)
    )
    for item in reversed(attempts):
        if not isinstance(item, dict):
            continue
        candidates.append((item.get("postcondition") or {}).get("scope"))
        candidates.append(item.get("action", {}).get("scope"))
        candidates.extend(
            relevant.get("scope")
            for relevant in reversed(item.get("relevant_inputs", []))
            if isinstance(relevant, dict)
        )
    candidates.extend(
        item.get("artifact_scope")
        for item in work.get("acceptance_criteria", [])
        if isinstance(item, dict)
    )
    candidates.extend(work.get("scope", {}).get("allowed_paths", []))
    return next(
        (item for item in candidates if isinstance(item, str) and item),
        "unresolved-artifact-scope",
    )


def protected_target_kind(scope: Any) -> str | None:
    if not isinstance(scope, str):
        return None
    normalized = scope.replace("\\", "/").strip("/")
    for prefix, kind in (
        (".yuan/core", "core"),
        (".yuan/protocol", "protocol"),
        (".yuan/harness", "harness"),
        (".yuan/validator", "validator"),
        (".yuan/authority", "authority"),
    ):
        if normalized == prefix or normalized.startswith(f"{prefix}/"):
            return kind
    return None


def replay_self_modification_authorized(
    work: dict[str, Any],
    attempt: dict[str, Any],
    evidence_items: list[dict[str, Any]],
    trusted_now: Any,
) -> bool:
    action = attempt.get("action", {})
    target_kind = protected_target_kind(action.get("scope"))
    if action.get("mutating") is not True or target_kind is None:
        return True
    record = action.get("self_modification")
    if not isinstance(record, dict):
        return False
    change = record.get("change")
    proofs = record.get("proofs")
    receipt = attempt.get("tool_receipt")
    if (
        not isinstance(change, dict)
        or not isinstance(proofs, list)
        or change.get("target_kind") != target_kind
        or not isinstance(receipt, dict)
        or change.get("candidate_binding", {}).get("sha256")
        != receipt.get("after_sha256")
    ):
        return False
    required_verifiers = [
        item.get("verifier_binding")
        for item in work.get("acceptance_criteria", [])
        if isinstance(item, dict) and item.get("required") is True
    ]
    for proof in proofs:
        if not isinstance(proof, dict):
            continue
        if proof.get("kind") == "previous-root" and not any(
            immutable_binding_matches(change.get("previous_binding"), verifier)
            for verifier in required_verifiers
        ):
            return False
        if proof.get("kind") == "independent-root" and not any(
            item.get("independence", {}).get("independent") is True
            and item.get("verifier_binding", {}).get("trust_root_id")
            == proof.get("root_id")
            for item in evidence_items
        ):
            return False
        if proof.get("kind") == "human-grant" and proof.get("grant_id") not in {
            item.get("id")
            for item in work.get("authorization", {}).get("grants", [])
            if isinstance(item, dict)
        }:
            return False
    return self_modification_authorized(change, proofs, now=trusted_now)
