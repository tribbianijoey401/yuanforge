#!/usr/bin/env python3
"""Independent M3 held-out verifier for the inert Yuan Core 0.1 candidate.

This file is intentionally outside ``.yuan/core/0.1`` and was not visible to
the task-005 author.  It emits the frozen bootstrap validator result shape so
the older M1 verifier can treat this as a trusted validator.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import importlib
import json
import pathlib
import sys
import tempfile
from datetime import datetime, timezone
from typing import Any, Callable

sys.dont_write_bytecode = True


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _load_json(path: pathlib.Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise TypeError(f"{path} is not a JSON object")
    return value


def _load_candidate(candidate: pathlib.Path) -> tuple[Any, Any, Any]:
    candidate = candidate.resolve(strict=True)
    sys.path.insert(0, str(candidate))
    for name in ("schema_runtime", "port_types", "conformance", "reference_port"):
        sys.modules.pop(name, None)
    try:
        conformance = importlib.import_module("conformance")
        reference_port = importlib.import_module("reference_port")
        port_types = importlib.import_module("port_types")
    finally:
        sys.path.pop(0)
    return conformance, reference_port, port_types


def _check(
    checks: list[dict[str, str]],
    check_id: str,
    predicate: Callable[[], bool],
) -> None:
    try:
        passed = predicate() is True
        observation = "expected invariant held" if passed else "expected invariant was violated"
    except Exception as error:  # A verifier exception is a failed check, never a pass.
        passed = False
        observation = f"{type(error).__name__}: {error}"
    checks.append(
        {
            "id": check_id,
            "status": "PASS" if passed else "FAIL",
            "observation": observation,
        }
    )


def _completion_fixture(candidate: pathlib.Path) -> tuple[dict[str, Any], dict[str, Any]]:
    work = _load_json(candidate / "fixtures" / "valid" / "work-contract.json")
    evidence = _load_json(candidate / "fixtures" / "valid" / "evidence.json")
    return work, evidence


def _completion(
    conformance: Any,
    work: dict[str, Any],
    evidence: dict[str, Any],
    *,
    artifact_sha256: str | None = None,
    environment_id: str | None = None,
) -> bool:
    return conformance.completion_satisfied(
        work,
        [evidence],
        current_artifact_sha256=artifact_sha256
        or evidence["artifact_binding"]["sha256"],
        environment_id=environment_id or evidence["environment_binding"]["id"],
        side_effect_states=["NOT_APPLICABLE"],
        safety_invariants={"SAFE-01": True},
    )


def _semantic_checks(candidate: pathlib.Path) -> list[dict[str, str]]:
    conformance, reference_port, port_types = _load_candidate(candidate)
    checks: list[dict[str, str]] = []
    work, evidence = _completion_fixture(candidate)

    _check(
        checks,
        "five-primitives-and-six-results",
        lambda: tuple(conformance.RESULTS)
        == ("CONTINUE", "CORRECT", "COMPLETE", "BLOCKED", "WAIT_AUTH", "BUDGET_EXIT")
        and all(
            token in (candidate / "protocol.md").read_text(encoding="utf-8")
            for token in ("Protocol", "Work Contract", "Run Memory", "Attempt", "Evidence")
        ),
    )
    _check(checks, "typed-ac-baseline-completes", lambda: _completion(conformance, work, evidence))

    wrong_work = copy.deepcopy(evidence)
    wrong_work["work_binding"]["sha256"] = "0" * 64
    _check(
        checks,
        "evidence-must-bind-current-work-revision",
        lambda: not _completion(conformance, work, wrong_work),
    )

    wrong_harness = copy.deepcopy(evidence)
    wrong_harness["harness_binding"]["sha256"] = "0" * 64
    _check(
        checks,
        "evidence-must-bind-work-harness-revision",
        lambda: not _completion(conformance, work, wrong_harness),
    )

    wrong_environment = copy.deepcopy(evidence)
    wrong_environment["environment_binding"]["fingerprint"] = "0" * 64
    _check(
        checks,
        "evidence-must-bind-current-environment-fingerprint",
        lambda: not _completion(conformance, work, wrong_environment),
    )

    expired = copy.deepcopy(evidence)
    expired["freshness"]["not_after"] = "2000-01-01T00:00:00+00:00"
    _check(
        checks,
        "expired-evidence-fails-closed",
        lambda: not _completion(conformance, work, expired),
    )

    forged_digest = copy.deepcopy(evidence)
    forged_digest["immutable_digest"] = "0" * 64
    _check(
        checks,
        "evidence-immutable-digest-is-verified",
        lambda: bool(conformance.validate_document("evidence", forged_digest).errors),
    )

    zero = copy.deepcopy(evidence)
    zero["assertions"] = 0
    zero["checks"] = []
    _check(
        checks,
        "zero-assertions-rejected",
        lambda: not _completion(conformance, work, zero),
    )

    stale = copy.deepcopy(evidence)
    stale["freshness"]["observed_artifact_sha256"] = "0" * 64
    _check(
        checks,
        "stale-artifact-rejected",
        lambda: not _completion(conformance, work, stale),
    )

    self_attested = copy.deepcopy(evidence)
    self_attested["independence"]["verifier_identity"] = self_attested["independence"][
        "author_identity"
    ]
    _check(
        checks,
        "self-attestation-rejected",
        lambda: not _completion(conformance, work, self_attested),
    )

    baseline_attempt = _load_json(candidate / "fixtures" / "valid" / "attempt.json")
    _check(
        checks,
        "attempt-baseline-valid",
        lambda: not conformance.validate_document("attempt", baseline_attempt).errors,
    )

    committed_without_receipt = copy.deepcopy(baseline_attempt)
    committed_without_receipt["action"].update(
        {
            "type": "file-write",
            "mutating": True,
            "side_effect_class": "filesystem",
            "authorization_grant_id": "GRANT-core-candidate",
        }
    )
    committed_without_receipt["journal"] = [
        {
            "ordinal": ordinal,
            "state": state,
            "recorded_at": f"2026-07-26T14:3{ordinal}:00+00:00",
            "receipt_sha256": None,
        }
        for ordinal, state in enumerate(
            ("PREPARED", "EXECUTING", "OBSERVED", "COMMITTED"), start=1
        )
    ]
    committed_without_receipt["side_effect_state"] = "COMMITTED"
    committed_without_receipt["tool_receipt"] = None
    committed_without_receipt["outcome"] = "SUCCEEDED"
    _check(
        checks,
        "committed-side-effect-requires-bound-receipt",
        lambda: bool(
            conformance.validate_document("attempt", committed_without_receipt).errors
        ),
    )

    unknown_succeeded = copy.deepcopy(committed_without_receipt)
    unknown_succeeded["journal"] = unknown_succeeded["journal"][:2] + [
        {
            "ordinal": 3,
            "state": "UNKNOWN",
            "recorded_at": "2026-07-26T14:33:00+00:00",
            "receipt_sha256": None,
        }
    ]
    unknown_succeeded["side_effect_state"] = "UNKNOWN"
    unknown_succeeded["outcome"] = "SUCCEEDED"
    _check(
        checks,
        "unknown-side-effect-cannot-succeed",
        lambda: bool(conformance.validate_document("attempt", unknown_succeeded).errors),
    )

    disguised_mutation = copy.deepcopy(baseline_attempt)
    disguised_mutation["action"].update(
        {
            "type": "file-write",
            "mutating": False,
            "side_effect_class": "filesystem",
            "authorization_grant_id": None,
        }
    )
    _check(
        checks,
        "mutating-action-type-cannot-claim-non-mutating",
        lambda: bool(conformance.validate_document("attempt", disguised_mutation).errors),
    )

    _check(
        checks,
        "run-memory-has-deterministic-rebuild",
        lambda: callable(getattr(conformance, "rebuild_run_memory", None)),
    )
    _check(
        checks,
        "self-modification-has-old-root-enforcer",
        lambda: callable(getattr(conformance, "self_modification_authorized", None)),
    )

    def rebuild_self_modification_and_scope_are_consistent() -> bool:
        self_work = copy.deepcopy(work)
        self_work["acceptance_criteria"][0]["verifier_binding"].update(
            {
                "id": "candidate-self-verifier",
                "revision": "candidate",
                "sha256": "e" * 64,
                "trust_root_id": "candidate-new-root",
            }
        )
        self_work["revision"]["sha256"] = conformance.canonical_digest(
            self_work, omitted_paths=(("revision", "sha256"),)
        )
        self_attempt = copy.deepcopy(baseline_attempt)
        self_attempt["work_binding"] = copy.deepcopy(self_work["revision"])
        receipt = {
            "schema_version": "yuan.tool-receipt/v1",
            "kind": "file-write",
            "operation_id": "OP-self-mod-without-old-root",
            "status": "REPLACED",
            "path": ".yuan/core/0.1",
            "before_sha256": "1" * 64,
            "after_sha256": "2" * 64,
        }
        receipt_digest = conformance.canonical_digest(receipt)
        self_attempt["action"].update(
            {
                "type": "file-write",
                "mutating": True,
                "side_effect_class": "filesystem",
                "authorization_grant_id": "GRANT-core-candidate",
            }
        )
        self_attempt["journal"] = [
            {
                "ordinal": ordinal,
                "state": state,
                "recorded_at": f"2026-07-26T14:4{ordinal}:00+00:00",
                "receipt_sha256": (
                    receipt_digest if state in {"OBSERVED", "COMMITTED"} else None
                ),
            }
            for ordinal, state in enumerate(
                ("PREPARED", "EXECUTING", "OBSERVED", "COMMITTED"), start=1
            )
        ]
        self_attempt["side_effect_state"] = "COMMITTED"
        self_attempt["tool_receipt"] = receipt
        self_attempt["postcondition"] = {
            "scope": ".yuan/core/0.1",
            "observed_sha256": "2" * 64,
            "satisfied": True,
        }
        self_attempt["outcome"] = "SUCCEEDED"
        self_evidence = copy.deepcopy(evidence)
        self_evidence["work_binding"] = copy.deepcopy(self_work["revision"])
        self_evidence["verifier_binding"].update(
            {
                "id": "candidate-self-verifier",
                "revision": "candidate",
                "sha256": "e" * 64,
                "trust_root_id": "candidate-new-root",
            }
        )
        self_evidence["independence"].update(
            {
                "method": "held-out",
                "author_identity": "candidate-author",
                "verifier_identity": "candidate-alias",
                "independent": True,
            }
        )
        self_evidence["immutable_digest"] = conformance.canonical_digest(
            self_evidence, omitted_paths=(("immutable_digest",),)
        )
        sys.path.insert(0, str(candidate))
        try:
            rebuilt = conformance.rebuild_run_memory(
                self_work,
                [self_attempt],
                [self_evidence],
                current_artifact_sha256=self_evidence["artifact_binding"]["sha256"],
                environment_id=self_evidence["environment_binding"]["id"],
                environment_fingerprint=self_evidence["environment_binding"][
                    "fingerprint"
                ],
                trusted_now=datetime(2026, 7, 26, 15, 0, tzinfo=timezone.utc),
            )
        finally:
            sys.path.pop(0)
        blocked_baseline = conformance.rebuild_run_memory(
            work,
            [baseline_attempt],
            [evidence],
            current_artifact_sha256=evidence["artifact_binding"]["sha256"],
            environment_id=evidence["environment_binding"]["id"],
            environment_fingerprint=evidence["environment_binding"]["fingerprint"],
            trusted_now=datetime(2026, 7, 26, 15, 0, tzinfo=timezone.utc),
            expected_attempts_digest="0" * 64,
        )
        return (
            rebuilt["last_result"] == "BLOCKED"
            and rebuilt["work_binding"] == self_work["revision"]
            and blocked_baseline["last_result"] == "BLOCKED"
            and blocked_baseline["artifact_binding"]["scope"]
            == evidence["artifact_binding"]["scope"]
        )

    _check(
        checks,
        "rebuild-selfmod-revision-and-port-scope-consistent",
        rebuild_self_modification_and_scope_are_consistent,
    )

    base_signals = {
        "state_consistent": True,
        "side_effect_states": [],
        "legal_next_step": True,
        "authorization_required": False,
        "budget_exhausted": False,
        "completion_satisfied": False,
        "hypothesis_refuted": False,
        "different_strategy_available": False,
        "new_relevant_evidence": False,
    }
    priority_cases = [
        ({"state_consistent": False, "authorization_required": True}, "BLOCKED"),
        ({"authorization_required": True, "budget_exhausted": True}, "WAIT_AUTH"),
        ({"budget_exhausted": True, "completion_satisfied": True}, "BUDGET_EXIT"),
        ({"completion_satisfied": True, "hypothesis_refuted": True}, "COMPLETE"),
        (
            {
                "hypothesis_refuted": True,
                "different_strategy_available": True,
                "new_relevant_evidence": True,
            },
            "CORRECT",
        ),
        ({"new_relevant_evidence": True}, "CONTINUE"),
    ]
    _check(
        checks,
        "six-result-priority-is-mutually-exclusive",
        lambda: all(
            conformance.reduce_tick({**base_signals, **signals}) == expected
            for signals, expected in priority_cases
        ),
    )

    charge = {"ticks": 1, "tool_calls": 1, "strategies": 1, "command_seconds": 1}
    remaining = {"ticks": 2, "tool_calls": 2, "strategies": 2, "command_seconds": 2}
    action = {
        "type": "file-write",
        "side_effect_class": "filesystem",
        "scope": ".yuan/core/0.1/new-file",
        "authorization_grant_id": "GRANT-core-candidate",
        "high_impact": False,
    }
    _check(
        checks,
        "scope-auth-budget-baseline-authorized",
        lambda: conformance.authorization_status(work, action, charge, remaining)
        == "AUTHORIZED",
    )
    escaped_action = {**action, "scope": "../outside"}
    _check(
        checks,
        "scope-path-escape-blocked",
        lambda: conformance.authorization_status(work, escaped_action, charge, remaining)
        == "BLOCKED",
    )
    expired_work = copy.deepcopy(work)
    expired_work["authorization"]["grants"][0]["expires_at"] = "2000-01-01T00:00:00+00:00"
    _check(
        checks,
        "expired-grant-waits-for-authorization",
        lambda: conformance.authorization_status(expired_work, action, charge, remaining)
        == "WAIT_AUTH",
    )
    exhausted = {**charge, "ticks": 3}
    _check(
        checks,
        "over-budget-action-exits",
        lambda: conformance.authorization_status(work, action, exhausted, remaining)
        == "BUDGET_EXIT",
    )
    _check(
        checks,
        "same-strategy-without-new-evidence-rejected",
        lambda: conformance.repeated_without_new_evidence(
            [
                {
                    "fingerprint": "a" * 64,
                    "relevant_inputs_digest": "b" * 64,
                    "latest_evidence_sequence": 4,
                }
            ],
            "a" * 64,
            "b" * 64,
            latest_evidence_sequence=4,
        ),
    )

    with tempfile.TemporaryDirectory(prefix="yuan-m3-port-") as temporary:
        temp_root = pathlib.Path(temporary)
        port_root = temp_root / "root"
        port_root.mkdir()
        executable = pathlib.Path(sys.executable).resolve(strict=True)
        port = reference_port.ReferencePort(
            port_root,
            allowed_executables=[executable],
            max_command_seconds=2,
            max_output_bytes=32,
        )

        _check(
            checks,
            "file-path-escape-rejected",
            lambda: _raises(port_types.ScopeViolation, lambda: port.read("../outside")),
        )
        first = port.atomic_write("state.bin", b"one", expected_sha256=None)
        _check(
            checks,
            "file-write-cas-and-hash",
            lambda: first.after_sha256 == _sha256_bytes(b"one")
            and port.atomic_write(
                "state.bin", b"two", expected_sha256=first.after_sha256
            ).after_sha256
            == _sha256_bytes(b"two"),
        )
        _check(
            checks,
            "file-write-stale-cas-rejected",
            lambda: _raises(
                port_types.CASMismatch,
                lambda: port.atomic_write(
                    "state.bin", b"three", expected_sha256="0" * 64
                ),
            ),
        )
        timeout_receipt = port.run_command(
            [str(executable), "-c", "import time; time.sleep(1)"],
            timeout_seconds=0.1,
        )
        _check(
            checks,
            "command-timeout-has-bounded-receipt",
            lambda: timeout_receipt.status == "TIMED_OUT"
            and timeout_receipt.exit_code is None
            and timeout_receipt.duration_seconds < 1.0,
        )
        output_receipt = port.run_command(
            [str(executable), "-c", "print('界' * 100)"],
            timeout_seconds=1.0,
        )
        _check(
            checks,
            "command-output-is-utf8-bounded-with-full-digest",
            lambda: output_receipt.status == "EXITED"
            and output_receipt.stdout_truncated is True
            and len(output_receipt.stdout.encode("utf-8")) <= 32
            and len(output_receipt.stdout_sha256) == 64,
        )

        outside = temp_root / "escaped.txt"

        def command_escape_rejected() -> bool:
            try:
                port.run_command(
                    [
                        str(executable),
                        "-c",
                        "import pathlib,sys; pathlib.Path(sys.argv[1]).write_text('escaped')",
                        str(outside),
                    ],
                    timeout_seconds=1.0,
                )
            except port_types.CommandRejected:
                return not outside.exists()
            return False

        _check(
            checks,
            "command-arguments-cannot-escape-work-scope",
            command_escape_rejected,
        )

    return checks


def _raises(error_type: type[BaseException], operation: Callable[[], Any]) -> bool:
    try:
        operation()
    except error_type:
        return True
    return False


def run(candidate: pathlib.Path) -> dict[str, Any]:
    try:
        checks = _semantic_checks(candidate.resolve(strict=True))
    except Exception as error:
        checks = [
            {
                "id": "held-out-validator-executed",
                "status": "FAIL",
                "observation": f"{type(error).__name__}: {error}",
            }
        ]
    status = "PASS" if checks and all(item["status"] == "PASS" for item in checks) else "FAIL"
    return {
        "schema_version": "yuan.validator-result/v1",
        "status": status,
        "assertions": len(checks),
        "checks": [{"id": item["id"], "status": item["status"]} for item in checks],
        "observations": checks,
        "producer": "task-006-independent-held-out",
        "created_at": datetime.now(timezone.utc).isoformat(),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("candidate", type=pathlib.Path)
    parser.add_argument("--receipt", type=pathlib.Path)
    args = parser.parse_args()
    result = run(args.candidate)
    payload = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.receipt:
        args.receipt.parent.mkdir(parents=True, exist_ok=True)
        args.receipt.write_text(payload, encoding="utf-8", newline="\n")
    print(payload, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
