#!/usr/bin/env python3
"""Independent M5 verification, fail-closed branches, and recovery drill."""

from __future__ import annotations

import argparse
import copy
import importlib.util
import json
import pathlib
import sys
import tempfile
from datetime import datetime, timezone
from typing import Any, Callable


REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))
RUNNER_PATH = pathlib.Path(__file__).with_name("run_canary.py")
SPEC = importlib.util.spec_from_file_location("m5_canary_runner", RUNNER_PATH)
assert SPEC and SPEC.loader
RUNNER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(RUNNER)
CONFORMANCE = RUNNER.conformance


def _load(path: pathlib.Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise TypeError(f"{path} is not a JSON object")
    return value


def _record(
    checks: list[dict[str, str]],
    check_id: str,
    predicate: Callable[[], bool],
    observation: str,
) -> None:
    try:
        passed = predicate() is True
        detail = observation
    except Exception as error:
        passed = False
        detail = f"{type(error).__name__}: {error}"
    checks.append(
        {
            "id": check_id,
            "status": "PASS" if passed else "FAIL",
            "observation": detail,
        }
    )


def _rebuild(
    work: dict[str, Any],
    attempts: list[dict[str, Any]],
    evidence: list[dict[str, Any]],
    artifact_sha256: str,
) -> dict[str, Any]:
    return CONFORMANCE.rebuild_run_memory(
        work,
        attempts,
        evidence,
        current_artifact_sha256=artifact_sha256,
        environment_id=RUNNER.ENVIRONMENT_ID,
        environment_fingerprint=RUNNER._environment_fingerprint(),
        trusted_now=RUNNER.FIXED_NOW,
    )


def verify(run_root: pathlib.Path, *, persist: bool) -> dict[str, Any]:
    run_root = run_root.resolve(strict=True)
    work = _load(run_root / "work-contract.json")
    attempt = _load(run_root / "attempts" / "0001.json")
    evidence = _load(run_root / "evidence" / "0001.json")
    memory = _load(run_root / "run-memory.json")
    receipt = _load(run_root / "receipt.json")
    artifact_sha256 = receipt["artifact_sha256"]
    checks: list[dict[str, str]] = []

    rebuilt = _rebuild(work, [attempt], [evidence], artifact_sha256)
    _record(
        checks,
        "M5-SUCCESS-CORE-REDUCER-COMPLETE",
        lambda: rebuilt["last_result"] == "COMPLETE" and rebuilt == memory,
        "persisted success history rebuilds byte-equivalent to COMPLETE",
    )
    _record(
        checks,
        "M5-TYPED-AC-PREBOUND-INDEPENDENT",
        lambda: work["acceptance_criteria"][0]["type"] == "contract"
        and work["acceptance_criteria"][0]["verifier_binding"]["sha256"]
        == RUNNER._sha256_file(RUNNER.VALIDATOR_PATH)
        and evidence["independence"]["independent"] is True
        and evidence["assertions"] >= 3,
        "typed AC uses the pre-bound independent validator with positive assertions",
    )
    _record(
        checks,
        "M5-SCOPE-AUTH-BUDGET",
        lambda: CONFORMANCE.authorization_status(
            work,
            attempt["action"],
            attempt["budget_charge"],
            work["budget"],
            trusted_now=RUNNER.FIXED_NOW,
            grant_usage={"GRANT-m5-canary-local": 0},
        )
        == "AUTHORIZED"
        and memory["remaining_budget"] == {
            key: work["budget"][key] - attempt["budget_charge"][key]
            for key in work["budget"]
        },
        "scope, deny-by-default grant, and immutable budget are mechanically enforced",
    )
    _record(
        checks,
        "M5-REFERENCE-PORT-RECEIPTS",
        lambda: attempt["tool_receipt"]["kind"] == "file-write"
        and _load(run_root / "receipts" / "validator-command.json")["kind"]
        == "command"
        and _load(run_root / "receipts" / "validator-command.json")["sandboxed"]
        is True,
        "file-write and sandboxed command have structured reference Port receipts",
    )
    _record(
        checks,
        "M5-LEGACY-AUTHORITY-UNCHANGED",
        lambda: receipt["authority_before_sha256"]
        == receipt["authority_after_sha256"]
        and receipt["legacy_state_unchanged"] is True
        and receipt["legacy_state_before"] == receipt["legacy_state_after"],
        "canary execution did not write the authority pointer or legacy runtime state",
    )

    stale = copy.deepcopy(evidence)
    stale["freshness"]["observed_artifact_sha256"] = "0" * 64
    stale["immutable_digest"] = CONFORMANCE.canonical_digest(
        stale, omitted_paths=(("immutable_digest",),)
    )
    stale_memory = _rebuild(work, [attempt], [stale], artifact_sha256)
    _record(
        checks,
        "M5-STALE-EVIDENCE-FAILS-CLOSED",
        lambda: stale_memory["last_result"] == "BLOCKED"
        and "INVALID_EVIDENCE" in stale_memory["rebuild"]["errors"],
        "stale Evidence cannot reduce to COMPLETE",
    )

    unknown = copy.deepcopy(attempt)
    unknown["attempt_id"] = "ATT-m5-canary-unknown"
    unknown["journal"] = [
        RUNNER._journal_entry(1, "PREPARED", None),
        RUNNER._journal_entry(2, "EXECUTING", None),
        RUNNER._journal_entry(3, "UNKNOWN", None),
    ]
    unknown["side_effect_state"] = "UNKNOWN"
    unknown["tool_receipt"] = None
    unknown["postcondition"] = None
    unknown["evidence_ids"] = []
    unknown["outcome"] = "UNKNOWN"
    unknown_errors = CONFORMANCE.validate_document("attempt", unknown).errors
    unknown_memory = _rebuild(work, [unknown], [], artifact_sha256)
    _record(
        checks,
        "M5-UNKNOWN-BLOCKS-COMPLETE",
        lambda: not unknown_errors
        and unknown_memory["last_result"] == "BLOCKED"
        and "UNKNOWN_SIDE_EFFECT" in unknown_memory["rebuild"]["errors"],
        "UNKNOWN side effects fail closed",
    )
    _record(
        checks,
        "M5-UNKNOWN-REMAINS-RECONCILABLE",
        lambda: unknown_memory["pending_side_effects"]
        == [{"attempt_id": "ATT-m5-canary-unknown", "state": "UNKNOWN"}],
        "Run Memory must retain the UNKNOWN Attempt so an independent reconciliation can target it",
    )

    _record(
        checks,
        "M5-COMMITTED-NOT-PENDING",
        lambda: attempt["side_effect_state"] == "COMMITTED"
        and rebuilt["pending_side_effects"] == [],
        "a normal COMMITTED side effect must not be projected as pending",
    )

    read_attempt = copy.deepcopy(attempt)
    read_attempt["attempt_id"] = "ATT-m5-canary-read"
    read_attempt["action"] = {
        "type": "file-read",
        "mutating": False,
        "side_effect_class": "none",
        "scope": work["acceptance_criteria"][0]["artifact_scope"],
        "authorization_grant_id": None,
        "high_impact": False,
        "self_modification": None,
    }
    read_attempt["journal"] = []
    read_attempt["side_effect_state"] = "NOT_APPLICABLE"
    read_attempt["tool_receipt"] = None
    read_attempt["postcondition"] = None
    read_attempt["evidence_ids"] = []
    read_attempt["outcome"] = "SUCCEEDED"
    read_memory = _rebuild(work, [read_attempt], [], artifact_sha256)
    _record(
        checks,
        "M5-PURE-READ-NOT-PENDING",
        lambda: not CONFORMANCE.validate_document("attempt", read_attempt).errors
        and read_memory["pending_side_effects"] == [],
        "a valid non-mutating file read cannot manufacture pending work",
    )

    missing_attempt_memory = _rebuild(work, [], [evidence], artifact_sha256)
    _record(
        checks,
        "M5-MISSING-ATTEMPT-BLOCKS-WITHOUT-FORGED-POINTER",
        lambda: missing_attempt_memory["last_result"] == "BLOCKED"
        and "MISSING_ATTEMPT_HISTORY" in missing_attempt_memory["rebuild"]["errors"]
        and missing_attempt_memory["pending_side_effects"] == [],
        "missing Attempt history blocks replay without inventing a reconciliation pointer",
    )

    with tempfile.TemporaryDirectory(prefix="yuan-m5-rebuild-") as temporary:
        disposable = pathlib.Path(temporary) / "run-memory.json"
        disposable.write_text(
            json.dumps(memory, ensure_ascii=False, sort_keys=True),
            encoding="utf-8",
        )
        disposable.unlink()
        rebuilt_after_discard = _rebuild(
            work, [attempt], [evidence], artifact_sha256
        )
        _record(
            checks,
            "M5-DERIVED-RUN-MEMORY-DISCARD-REBUILD",
            lambda: not disposable.exists() and rebuilt_after_discard == memory,
            "the disposable Run Memory projection can be deleted and rebuilt from immutable history",
        )

    pointer = _load(REPO_ROOT / ".yuan-shadow" / "authority.json")
    from scripts import yuan_shadow_support

    def writer_guard_rejects_cross_lane() -> bool:
        try:
            yuan_shadow_support.assert_write_allowed(
                REPO_ROOT,
                pointer,
                "shadow",
                (run_root / "artifact.txt").relative_to(REPO_ROOT).as_posix(),
                receipt["artifact_sha256"],
            )
        except yuan_shadow_support.GuardError:
            return True
        return False

    _record(
        checks,
        "M5-M4-WRITER-GUARD-CROSS-LANE",
        writer_guard_rejects_cross_lane,
        "M4 shadow writer is mechanically denied access to the legacy evidence lane",
    )

    if persist:
        negative = run_root / "negative"
        negative.mkdir(parents=True, exist_ok=True)
        persisted = {
            "stale-evidence.json": stale,
            "stale-run-memory.json": stale_memory,
            "unknown-attempt.json": unknown,
            "unknown-run-memory.json": unknown_memory,
            "read-attempt.json": read_attempt,
            "read-run-memory.json": read_memory,
            "missing-attempt-run-memory.json": missing_attempt_memory,
        }
        for filename, value in persisted.items():
            path = negative / filename
            expected = RUNNER._sha256_file(path) if path.is_file() else None
            RUNNER._atomic_json(path, value, expected_sha256=expected)

    status = "PASS" if checks and all(item["status"] == "PASS" for item in checks) else "FAIL"
    return {
        "schema_version": "yuan.m5-independent-verification/v1",
        "status": status,
        "assertions": len(checks),
        "checks": checks,
        "blockers": [] if status == "PASS" else [
            {
                "id": "M5-B01",
                "route": "task-005",
                "summary": "BLOCKED rebuild does not preserve exactly the valid pending pointers required for reconciliation.",
                "evidence": "negative/unknown-run-memory.json",
            }
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-root", type=pathlib.Path, required=True)
    parser.add_argument("--receipt", type=pathlib.Path, required=True)
    args = parser.parse_args()
    result = verify(args.run_root, persist=True)
    args.receipt.parent.mkdir(parents=True, exist_ok=True)
    args.receipt.write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
