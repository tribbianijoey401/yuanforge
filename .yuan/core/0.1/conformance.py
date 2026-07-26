#!/usr/bin/env python3
"""Author-visible conformance helpers for the inert Yuan Core 0.1 candidate.

This module is development evidence only. M3 must use the frozen older trust
root and independent held-out tests; a candidate cannot establish its own trust.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import re
import sys
from dataclasses import dataclass
from typing import Any

from schema_runtime import validate_schema

CORE_ROOT = pathlib.Path(__file__).resolve().parent
KINDS = ("work-contract", "run-memory", "attempt", "evidence")
RESULTS = ("CONTINUE", "CORRECT", "COMPLETE", "BLOCKED", "WAIT_AUTH", "BUDGET_EXIT")
SHA256 = re.compile(r"^[0-9a-f]{64}$")
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


def _semantic_errors(kind: str, document: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if kind == "work-contract":
        for field, code in (
            ("acceptance_criteria", "DUPLICATE_AC_ID"),
            ("safety_invariants", "DUPLICATE_SAFETY_ID"),
        ):
            ids = [item.get("id") for item in document.get(field, []) if isinstance(item, dict)]
            if len(ids) != len(set(ids)):
                errors.append(code)
        grant_ids = [item.get("id") for item in document.get("authorization", {}).get("grants", [])]
        if len(grant_ids) != len(set(grant_ids)):
            errors.append("DUPLICATE_GRANT_ID")
    elif kind == "attempt":
        action = document.get("action", {})
        journal = document.get("journal", [])
        states = tuple(item.get("state") for item in journal if isinstance(item, dict))
        ordinals = [item.get("ordinal") for item in journal if isinstance(item, dict)]
        mutating = action.get("mutating") is True
        if mutating:
            if states not in JOURNAL_PATHS or ordinals != list(range(1, len(journal) + 1)):
                errors.append("INVALID_JOURNAL_TRANSITION")
            if document.get("side_effect_state") != (states[-1] if states else None):
                errors.append("JOURNAL_STATE_MISMATCH")
            if not action.get("authorization_grant_id") or action.get("side_effect_class") == "none":
                errors.append("MUTATION_NOT_AUTHORIZED")
        elif journal or document.get("side_effect_state") != "NOT_APPLICABLE":
            errors.append("NON_MUTATING_JOURNAL")
    elif kind == "evidence":
        assertions = document.get("assertions")
        checks = document.get("checks", [])
        if assertions == 0:
            errors.append("ZERO_ASSERTIONS")
        if not isinstance(assertions, int) or assertions != len(checks):
            errors.append("ASSERTION_COUNT_MISMATCH")
        ids = [item.get("id") for item in checks if isinstance(item, dict)]
        if len(ids) != len(set(ids)):
            errors.append("DUPLICATE_CHECK_ID")
        if document.get("status") == "PASS" and any(item.get("status") != "PASS" for item in checks):
            errors.append("PASS_WITH_FAILED_CHECK")
        artifact = document.get("artifact_binding", {})
        if document.get("freshness", {}).get("observed_artifact_sha256") != artifact.get("sha256"):
            errors.append("STALE_ARTIFACT_BINDING")
        independence = document.get("independence", {})
        if independence.get("independent") and independence.get("author_identity") == independence.get("verifier_identity"):
            errors.append("SELF_ATTESTATION")
    elif kind == "run-memory":
        pending = document.get("pending_side_effects", [])
        if document.get("last_result") == "COMPLETE" and pending:
            errors.append("COMPLETE_WITH_PENDING_SIDE_EFFECT")
    return errors


def validate_document(kind: str, document: dict[str, Any]) -> ValidationResult:
    schema = json.loads(_schema_path(kind).read_text(encoding="utf-8"))
    errors: list[str] = []
    assertions = validate_schema(document, schema, schema, "$", errors)
    errors.extend(_semantic_errors(kind, document))
    return ValidationResult(list(dict.fromkeys(errors)), assertions + 1)


def _valid_evidence_for_ac(
    ac: dict[str, Any],
    evidence: dict[str, Any],
    artifact_sha256: str,
    environment_id: str,
) -> bool:
    binding = ac["verifier_binding"]
    return (
        not validate_document("evidence", evidence).errors
        and evidence["status"] == "PASS"
        and evidence["ac_id"] == ac["id"]
        and evidence["kind"] == ac["type"]
        and evidence["assertions"] >= binding["minimum_assertions"]
        and evidence["artifact_binding"]["scope"] == ac["artifact_scope"]
        and evidence["artifact_binding"]["sha256"] == artifact_sha256
        and evidence["environment_binding"]["id"] == environment_id
        and environment_id in binding["environment_ids"]
        and all(evidence["verifier_binding"][key] == binding[key] for key in ("id", "revision", "sha256", "trust_root_id"))
        and evidence["independence"]["independent"] is True
    )


def completion_satisfied(
    work: dict[str, Any],
    evidence_items: list[dict[str, Any]],
    *,
    current_artifact_sha256: str,
    environment_id: str,
    side_effect_states: list[str],
    safety_invariants: dict[str, bool],
) -> bool:
    if validate_document("work-contract", work).errors:
        return False
    if any(state not in {"COMMITTED", "NOT_APPLICABLE"} for state in side_effect_states):
        return False
    required_safety = {item["id"] for item in work["safety_invariants"]}
    if any(safety_invariants.get(item) is not True for item in required_safety):
        return False
    for ac in (item for item in work["acceptance_criteria"] if item["required"]):
        if not any(_valid_evidence_for_ac(ac, item, current_artifact_sha256, environment_id) for item in evidence_items):
            return False
    return True


def reduce_tick(signals: dict[str, Any]) -> str:
    states = signals.get("side_effect_states", [])
    if (
        signals.get("state_consistent") is not True
        or "UNKNOWN" in states
        or signals.get("legal_next_step") is False
    ):
        return "BLOCKED"
    if signals.get("authorization_required") is True:
        return "WAIT_AUTH"
    if signals.get("budget_exhausted") is True:
        return "BUDGET_EXIT"
    if signals.get("completion_satisfied") is True:
        return "COMPLETE"
    if (
        signals.get("hypothesis_refuted") is True
        and signals.get("different_strategy_available") is True
    ):
        return "CORRECT"
    if signals.get("new_relevant_evidence") is True and signals.get("legal_next_step") is True:
        return "CONTINUE"
    return "BLOCKED"


def _scope_contains(parent: str, child: str) -> bool:
    parent_path = pathlib.PurePosixPath(parent.replace("\\", "/"))
    child_path = pathlib.PurePosixPath(child.replace("\\", "/"))
    if child_path.is_absolute() or ".." in child_path.parts:
        return False
    return child_path == parent_path or parent_path in child_path.parents


def authorization_status(
    work: dict[str, Any],
    action: dict[str, Any],
    charge: dict[str, Any],
    remaining: dict[str, Any],
) -> str:
    if validate_document("work-contract", work).errors:
        return "BLOCKED"
    scope = action.get("scope")
    if not isinstance(scope, str):
        return "BLOCKED"
    declared_scope = work["scope"]
    if (
        action.get("side_effect_class") not in declared_scope["side_effect_classes"]
        or not any(_scope_contains(item, scope) for item in declared_scope["allowed_paths"])
        or any(_scope_contains(item, scope) for item in declared_scope["denied_paths"])
    ):
        return "BLOCKED"
    grant = next(
        (
            item
            for item in work["authorization"]["grants"]
            if item["id"] == action.get("authorization_grant_id")
        ),
        None,
    )
    if (
        grant is None
        or action.get("type") not in grant["action_types"]
        or action.get("side_effect_class") not in grant["side_effect_classes"]
        or not any(_scope_contains(item, scope) for item in grant["scopes"])
        or (action.get("high_impact") is True and grant["high_impact"] is not True)
    ):
        return "WAIT_AUTH"
    budget_fields = ("ticks", "tool_calls", "strategies", "command_seconds")
    if any(
        not isinstance(charge.get(item), (int, float))
        or charge[item] < 0
        or charge[item] > remaining.get(item, -1)
        for item in budget_fields
    ):
        return "BUDGET_EXIT"
    return "AUTHORIZED"


def repeated_without_new_evidence(
    history: list[dict[str, Any]],
    strategy_fingerprint: str,
    relevant_inputs_digest: str,
    *,
    latest_evidence_sequence: int,
) -> bool:
    return any(
        item.get("fingerprint") == strategy_fingerprint
        and item.get("relevant_inputs_digest") == relevant_inputs_digest
        and item.get("latest_evidence_sequence", -1) >= latest_evidence_sequence
        for item in history
    )


def _sha256(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run_candidate(root: pathlib.Path) -> dict[str, Any]:
    checks: list[dict[str, str]] = []
    protocol = (root / "protocol.md").read_text(encoding="utf-8")
    for token in (*RESULTS, "PREPARED", "UNKNOWN", "fail-closed"):
        checks.append({"id": f"protocol-{token.lower()}", "status": "PASS" if token in protocol else "FAIL"})
    for kind in KINDS:
        schema = json.loads((root / f"{kind}.schema.yaml").read_text(encoding="utf-8"))
        checks.append({"id": f"schema-{kind}", "status": "PASS" if schema.get("$schema") and schema.get("type") == "object" else "FAIL"})
        fixture = json.loads((root / "fixtures" / "valid" / f"{kind}.json").read_text(encoding="utf-8"))
        checks.append({"id": f"fixture-{kind}", "status": "PASS" if not validate_document(kind, fixture).errors else "FAIL"})
    manifest = json.loads((root / "candidate-manifest.json").read_text(encoding="utf-8"))
    for relative, expected_error in manifest["negative_fixtures"].items():
        filename = pathlib.PurePosixPath(relative).name
        kind = next(item for item in KINDS if filename.startswith(f"{item}-"))
        document = json.loads((root / relative).read_text(encoding="utf-8"))
        errors = validate_document(kind, document).errors
        checks.append(
            {
                "id": f"negative-{filename}",
                "status": "PASS" if expected_error in errors else "FAIL",
            }
        )
    for item in manifest["files"]:
        path = root / item["path"]
        status = path.is_file() and _sha256(path) == item["sha256"]
        checks.append({"id": f"manifest-{item['path']}", "status": "PASS" if status else "FAIL"})
    status = "PASS" if checks and all(item["status"] == "PASS" for item in checks) else "FAIL"
    return {
        "schema_version": "yuan.validator-result/v1",
        "status": status,
        "assertions": len(checks),
        "checks": checks,
        "candidate_revision": manifest.get("candidate_revision"),
        "candidate_manifest_sha256": _sha256(root / "candidate-manifest.json"),
        "warning": "author-visible candidate self-check; not Genesis or M3 proof",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--candidate", type=pathlib.Path, default=CORE_ROOT)
    parser.add_argument("--receipt", type=pathlib.Path)
    args = parser.parse_args()
    try:
        result = run_candidate(args.candidate.resolve())
    except (OSError, ValueError, KeyError, json.JSONDecodeError) as error:
        result = {
            "schema_version": "yuan.validator-result/v1",
            "status": "FAIL",
            "assertions": 1,
            "checks": [{"id": "candidate-readable", "status": "FAIL"}],
            "error": str(error),
        }
    payload = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.receipt:
        args.receipt.write_text(payload, encoding="utf-8", newline="\n")
    print(payload, end="")
    return 0 if result["status"] == "PASS" and result["assertions"] > 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
