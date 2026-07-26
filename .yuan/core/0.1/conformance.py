#!/usr/bin/env python3
"""Author-visible conformance runner for the inert Yuan Core 0.1 candidate.

This development aid cannot establish its own trust. M3 verification belongs
to the frozen Genesis verifier and an independent held-out suite.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
from typing import Any

from authorization_semantics import authorization_status
from completion_semantics import completion_satisfied
from document_validation import (
    KINDS,
    ValidationResult,
    validate_document,
    work_revision_valid,
)
from trust_semantics import canonical_digest, self_modification_authorized

CORE_ROOT = pathlib.Path(__file__).resolve().parent
RESULTS = ("CONTINUE", "CORRECT", "COMPLETE", "BLOCKED", "WAIT_AUTH", "BUDGET_EXIT")


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
    if signals.get("new_relevant_evidence") is True and signals.get(
        "legal_next_step"
    ) is True:
        return "CONTINUE"
    return "BLOCKED"


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


def rebuild_run_memory(
    work: dict[str, Any],
    attempts: list[dict[str, Any]],
    evidence_items: list[dict[str, Any]],
    **kwargs: Any,
) -> dict[str, Any]:
    from runtime_replay import rebuild

    return rebuild(
        work,
        attempts,
        evidence_items,
        validate_document=validate_document,
        work_revision_valid=work_revision_valid,
        completion_satisfied=completion_satisfied,
        **kwargs,
    )


def _sha256(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run_candidate(root: pathlib.Path) -> dict[str, Any]:
    checks: list[dict[str, str]] = []
    protocol = (root / "protocol.md").read_text(encoding="utf-8")
    for token in (*RESULTS, "PREPARED", "UNKNOWN", "fail-closed"):
        checks.append(
            {
                "id": f"protocol-{token.lower()}",
                "status": "PASS" if token in protocol else "FAIL",
            }
        )
    for kind in KINDS:
        schema = json.loads((root / f"{kind}.schema.yaml").read_text(encoding="utf-8"))
        checks.append(
            {
                "id": f"schema-{kind}",
                "status": (
                    "PASS"
                    if schema.get("$schema") and schema.get("type") == "object"
                    else "FAIL"
                ),
            }
        )
        fixture = json.loads(
            (root / "fixtures" / "valid" / f"{kind}.json").read_text(
                encoding="utf-8"
            )
        )
        checks.append(
            {
                "id": f"fixture-{kind}",
                "status": "PASS" if not validate_document(kind, fixture).errors else "FAIL",
            }
        )
    manifest = json.loads(
        (root / "candidate-manifest.json").read_text(encoding="utf-8")
    )
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
        matches = path.is_file() and _sha256(path) == item["sha256"]
        checks.append(
            {
                "id": f"manifest-{item['path']}",
                "status": "PASS" if matches else "FAIL",
            }
        )
    status = (
        "PASS"
        if checks and all(item["status"] == "PASS" for item in checks)
        else "FAIL"
    )
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
