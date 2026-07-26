"""Schema plus cross-field validation for the four persisted Core records."""

from __future__ import annotations

import json
import pathlib
from dataclasses import dataclass
from typing import Any

from schema_runtime import validate_schema
from trust_semantics import canonical_digest


CORE_ROOT = pathlib.Path(__file__).resolve().parent
KINDS = ("work-contract", "run-memory", "attempt", "evidence")
JOURNAL_PATHS = {
    ("PREPARED",),
    ("PREPARED", "EXECUTING"),
    ("PREPARED", "EXECUTING", "OBSERVED"),
    ("PREPARED", "EXECUTING", "OBSERVED", "COMMITTED"),
    ("PREPARED", "EXECUTING", "UNKNOWN"),
    ("PREPARED", "EXECUTING", "OBSERVED", "UNKNOWN"),
}


@dataclass(frozen=True)
class ValidationResult:
    errors: list[str]
    assertions: int


def _schema_path(kind: str) -> pathlib.Path:
    if kind not in KINDS:
        raise ValueError(f"unknown document kind: {kind}")
    return CORE_ROOT / f"{kind}.schema.yaml"


def _work_errors(document: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    for field, code in (
        ("acceptance_criteria", "DUPLICATE_AC_ID"),
        ("safety_invariants", "DUPLICATE_SAFETY_ID"),
    ):
        ids = [
            item.get("id")
            for item in document.get(field, [])
            if isinstance(item, dict)
        ]
        if len(ids) != len(set(ids)):
            errors.append(code)
    grants = document.get("authorization", {}).get("grants", [])
    grant_ids = [item.get("id") for item in grants if isinstance(item, dict)]
    if len(grant_ids) != len(set(grant_ids)):
        errors.append("DUPLICATE_GRANT_ID")
    return errors


def _attempt_errors(document: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    action = document.get("action", {})
    journal = document.get("journal", [])
    states = tuple(item.get("state") for item in journal if isinstance(item, dict))
    ordinals = [item.get("ordinal") for item in journal if isinstance(item, dict)]
    mutating = action.get("mutating") is True
    if action.get("type") in {"file-write", "command"} and not mutating:
        errors.append("MUTATING_ACTION_DISGUISED")
    if not mutating:
        if journal or document.get("side_effect_state") != "NOT_APPLICABLE":
            errors.append("NON_MUTATING_JOURNAL")
        return errors
    if states not in JOURNAL_PATHS or ordinals != list(range(1, len(journal) + 1)):
        errors.append("INVALID_JOURNAL_TRANSITION")
    state = document.get("side_effect_state")
    if state != (states[-1] if states else None):
        errors.append("JOURNAL_STATE_MISMATCH")
    if not action.get("authorization_grant_id") or action.get("side_effect_class") == "none":
        errors.append("MUTATION_NOT_AUTHORIZED")
    receipt = document.get("tool_receipt")
    postcondition = document.get("postcondition")
    if state in {"OBSERVED", "COMMITTED"}:
        if not isinstance(receipt, dict) or not isinstance(postcondition, dict):
            errors.append("SIDE_EFFECT_PROOF_MISSING")
        else:
            receipt_digest = canonical_digest(receipt)
            proof_entries = [
                item
                for item in journal
                if item.get("state") in {"OBSERVED", "COMMITTED"}
            ]
            if any(
                item.get("receipt_sha256") != receipt_digest for item in proof_entries
            ):
                errors.append("RECEIPT_BINDING_MISMATCH")
            if (
                postcondition.get("satisfied") is not True
                or postcondition.get("scope") != action.get("scope")
                or (
                    action.get("type") == "file-write"
                    and postcondition.get("observed_sha256")
                    != receipt.get("after_sha256")
                )
            ):
                errors.append("POSTCONDITION_MISMATCH")
            if action.get("type") == "file-write" and (
                receipt.get("kind") != "file-write"
                or receipt.get("path") != action.get("scope")
                or receipt.get("status") not in {"CREATED", "REPLACED"}
            ):
                errors.append("RECEIPT_SCOPE_MISMATCH")
    outcome = document.get("outcome")
    if state == "UNKNOWN" and outcome != "UNKNOWN":
        errors.append("UNKNOWN_OUTCOME_MISMATCH")
    if state == "COMMITTED" and outcome != "SUCCEEDED":
        errors.append("COMMITTED_OUTCOME_MISMATCH")
    if state in {"PREPARED", "EXECUTING", "OBSERVED"} and outcome == "SUCCEEDED":
        errors.append("PENDING_OUTCOME_MISMATCH")
    return errors


def _evidence_errors(document: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    assertions = document.get("assertions")
    checks = document.get("checks", [])
    if assertions == 0:
        errors.append("ZERO_ASSERTIONS")
    if not isinstance(assertions, int) or isinstance(assertions, bool) or assertions != len(checks):
        errors.append("ASSERTION_COUNT_MISMATCH")
    ids = [item.get("id") for item in checks if isinstance(item, dict)]
    if len(ids) != len(set(ids)):
        errors.append("DUPLICATE_CHECK_ID")
    if document.get("status") == "PASS" and any(
        item.get("status") != "PASS" for item in checks
    ):
        errors.append("PASS_WITH_FAILED_CHECK")
    artifact = document.get("artifact_binding", {})
    if (
        document.get("freshness", {}).get("observed_artifact_sha256")
        != artifact.get("sha256")
    ):
        errors.append("STALE_ARTIFACT_BINDING")
    independence = document.get("independence", {})
    if (
        independence.get("independent")
        and independence.get("author_identity") == independence.get("verifier_identity")
    ):
        errors.append("SELF_ATTESTATION")
    if document.get("immutable_digest") != canonical_digest(
        document, omitted_paths=(("immutable_digest",),)
    ):
        errors.append("IMMUTABLE_DIGEST_MISMATCH")
    return errors


def _semantic_errors(kind: str, document: dict[str, Any]) -> list[str]:
    if kind == "work-contract":
        return _work_errors(document)
    if kind == "attempt":
        return _attempt_errors(document)
    if kind == "evidence":
        return _evidence_errors(document)
    pending = document.get("pending_side_effects", [])
    return (
        ["COMPLETE_WITH_PENDING_SIDE_EFFECT"]
        if document.get("last_result") == "COMPLETE" and pending
        else []
    )


def validate_document(kind: str, document: dict[str, Any]) -> ValidationResult:
    schema = json.loads(_schema_path(kind).read_text(encoding="utf-8"))
    errors: list[str] = []
    assertions = validate_schema(document, schema, schema, "$", errors)
    errors.extend(_semantic_errors(kind, document))
    return ValidationResult(list(dict.fromkeys(errors)), assertions + 1)


def work_revision_valid(work: dict[str, Any]) -> bool:
    return (
        work.get("revision", {}).get("id") == work.get("work_id")
        and work.get("revision", {}).get("sha256")
        == canonical_digest(work, omitted_paths=(("revision", "sha256"),))
    )
