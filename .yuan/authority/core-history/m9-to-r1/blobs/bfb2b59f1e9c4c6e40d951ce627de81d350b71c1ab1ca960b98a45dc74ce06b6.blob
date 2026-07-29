from __future__ import annotations

import copy
import json
import pathlib
import unittest

from _load import CORE_ROOT, load_core_module


conformance = load_core_module("conformance")


class SchemaContractTests(unittest.TestCase):
    def test_candidate_self_check_covers_negative_fixtures_and_manifest(self) -> None:
        result = conformance.run_candidate(CORE_ROOT)
        self.assertEqual("PASS", result["status"])
        check_ids = {item["id"] for item in result["checks"]}
        self.assertIn("negative-evidence-zero-assertions.json", check_ids)
        self.assertIn("manifest-protocol.md", check_ids)

    def test_all_four_schemas_parse_as_json_compatible_yaml(self) -> None:
        for filename in (
            "work-contract.schema.yaml",
            "run-memory.schema.yaml",
            "attempt.schema.yaml",
            "evidence.schema.yaml",
        ):
            with self.subTest(filename=filename):
                schema = json.loads((CORE_ROOT / filename).read_text(encoding="utf-8"))
                self.assertEqual("https://json-schema.org/draft/2020-12/schema", schema["$schema"])
                self.assertEqual("object", schema["type"])

    def test_valid_author_fixtures_satisfy_schema_and_semantics(self) -> None:
        for kind in ("work-contract", "run-memory", "attempt", "evidence"):
            with self.subTest(kind=kind):
                document = json.loads(
                    (CORE_ROOT / "fixtures" / "valid" / f"{kind}.json").read_text(
                        encoding="utf-8"
                    )
                )
                result = conformance.validate_document(kind, document)
                self.assertEqual([], result.errors)
                self.assertGreater(result.assertions, 0)

    def test_invalid_author_fixtures_are_rejected(self) -> None:
        expected = {
            "work-contract-duplicate-ac.json": "DUPLICATE_AC_ID",
            "attempt-invalid-journal.json": "INVALID_JOURNAL_TRANSITION",
            "evidence-zero-assertions.json": "ZERO_ASSERTIONS",
            "run-memory-unknown-complete.json": "COMPLETE_WITH_PENDING_SIDE_EFFECT",
        }
        for filename, reason in expected.items():
            with self.subTest(filename=filename):
                kind = {
                    "work-contract-duplicate-ac.json": "work-contract",
                    "attempt-invalid-journal.json": "attempt",
                    "evidence-zero-assertions.json": "evidence",
                    "run-memory-unknown-complete.json": "run-memory",
                }[filename]
                document = json.loads(
                    (CORE_ROOT / "fixtures" / "invalid" / filename).read_text(
                        encoding="utf-8"
                    )
                )
                result = conformance.validate_document(kind, document)
                self.assertIn(reason, result.errors)


class ReducerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.work = json.loads(
            (CORE_ROOT / "fixtures" / "valid" / "work-contract.json").read_text(
                encoding="utf-8"
            )
        )
        self.evidence = json.loads(
            (CORE_ROOT / "fixtures" / "valid" / "evidence.json").read_text(
                encoding="utf-8"
            )
        )

    def signals(self, **overrides: object) -> dict[str, object]:
        base: dict[str, object] = {
            "state_consistent": True,
            "side_effect_states": ["COMMITTED"],
            "authorization_required": False,
            "budget_exhausted": False,
            "completion_satisfied": False,
            "hypothesis_refuted": False,
            "different_strategy_available": False,
            "new_relevant_evidence": False,
            "legal_next_step": True,
        }
        base.update(overrides)
        return base

    def test_six_results_have_a_single_frozen_priority(self) -> None:
        cases = (
            (self.signals(side_effect_states=["UNKNOWN"], authorization_required=True), "BLOCKED"),
            (self.signals(authorization_required=True, budget_exhausted=True), "WAIT_AUTH"),
            (self.signals(budget_exhausted=True, completion_satisfied=True), "BUDGET_EXIT"),
            (self.signals(completion_satisfied=True), "COMPLETE"),
            (
                self.signals(
                    hypothesis_refuted=True,
                    different_strategy_available=True,
                    new_relevant_evidence=True,
                ),
                "CORRECT",
            ),
            (self.signals(new_relevant_evidence=True), "CONTINUE"),
            (self.signals(legal_next_step=False), "BLOCKED"),
        )
        for signals, expected in cases:
            with self.subTest(expected=expected):
                self.assertEqual(expected, conformance.reduce_tick(signals))

    def test_completion_requires_current_independent_bound_evidence(self) -> None:
        self.assertTrue(
            conformance.completion_satisfied(
                self.work,
                [self.evidence],
                current_artifact_sha256=self.evidence["artifact_binding"]["sha256"],
                environment_id=self.evidence["environment_binding"]["id"],
                side_effect_states=["COMMITTED"],
                safety_invariants={"SAFE-01": True},
            )
        )
        mutations = [
            ("zero_assertions", lambda item: item.update(assertions=0)),
            (
                "stale_artifact",
                lambda item: item["artifact_binding"].update(sha256="0" * 64),
            ),
            (
                "wrong_environment",
                lambda item: item["environment_binding"].update(id="other-env"),
            ),
            (
                "wrong_verifier",
                lambda item: item["verifier_binding"].update(sha256="1" * 64),
            ),
            (
                "not_independent",
                lambda item: item["independence"].update(independent=False),
            ),
        ]
        for name, mutate in mutations:
            with self.subTest(name=name):
                evidence = copy.deepcopy(self.evidence)
                mutate(evidence)
                self.assertFalse(
                    conformance.completion_satisfied(
                        self.work,
                        [evidence],
                        current_artifact_sha256=self.evidence["artifact_binding"]["sha256"],
                        environment_id=self.evidence["environment_binding"]["id"],
                        side_effect_states=["COMMITTED"],
                        safety_invariants={"SAFE-01": True},
                    )
                )
        self.assertFalse(
            conformance.completion_satisfied(
                self.work,
                [self.evidence],
                current_artifact_sha256=self.evidence["artifact_binding"]["sha256"],
                environment_id=self.evidence["environment_binding"]["id"],
                side_effect_states=["UNKNOWN"],
                safety_invariants={"SAFE-01": True},
            )
        )

    def test_scope_authorization_and_budget_are_fail_closed(self) -> None:
        action = {
            "type": "file-write",
            "mutating": True,
            "side_effect_class": "filesystem",
            "scope": ".yuan/core/0.1/state.json",
            "authorization_grant_id": "GRANT-core-candidate",
            "high_impact": False,
        }
        charge = {
            "ticks": 1,
            "tool_calls": 1,
            "strategies": 1,
            "command_seconds": 1,
        }
        remaining = {
            "ticks": 2,
            "tool_calls": 2,
            "strategies": 2,
            "command_seconds": 2,
        }
        self.assertEqual(
            "AUTHORIZED",
            conformance.authorization_status(self.work, action, charge, remaining),
        )
        outside = copy.deepcopy(action)
        outside["scope"] = "AGENTS.md"
        self.assertEqual(
            "BLOCKED",
            conformance.authorization_status(self.work, outside, charge, remaining),
        )
        ungranted = copy.deepcopy(action)
        ungranted["authorization_grant_id"] = None
        self.assertEqual(
            "WAIT_AUTH",
            conformance.authorization_status(self.work, ungranted, charge, remaining),
        )
        expensive = copy.deepcopy(charge)
        expensive["tool_calls"] = 3
        self.assertEqual(
            "BUDGET_EXIT",
            conformance.authorization_status(self.work, action, expensive, remaining),
        )

    def test_same_strategy_same_inputs_without_new_evidence_is_rejected(self) -> None:
        fingerprint = "1" * 64
        inputs = "2" * 64
        history = [
            {
                "fingerprint": fingerprint,
                "relevant_inputs_digest": inputs,
                "latest_evidence_sequence": 5,
            }
        ]
        self.assertTrue(
            conformance.repeated_without_new_evidence(
                history, fingerprint, inputs, latest_evidence_sequence=5
            )
        )
        self.assertFalse(
            conformance.repeated_without_new_evidence(
                history, fingerprint, inputs, latest_evidence_sequence=6
            )
        )


if __name__ == "__main__":
    unittest.main()
