from __future__ import annotations

import copy
import json
import pathlib
import sys
import tempfile
import unittest
from datetime import datetime, timezone

from _load import CORE_ROOT, load_core_module


conformance = load_core_module("conformance")
reference_port = load_core_module("reference_port")
port_types = load_core_module("port_types")


def fixture(kind: str) -> dict:
    return json.loads(
        (CORE_ROOT / "fixtures" / "valid" / f"{kind}.json").read_text(encoding="utf-8")
    )


class EvidenceTrustTests(unittest.TestCase):
    def setUp(self) -> None:
        self.work = fixture("work-contract")
        self.evidence = fixture("evidence")
        self.now = datetime(2026, 7, 26, 15, 0, tzinfo=timezone.utc)

    def complete(self, evidence: dict) -> bool:
        return conformance.completion_satisfied(
            self.work,
            [evidence],
            current_artifact_sha256=self.evidence["artifact_binding"]["sha256"],
            environment_id=self.evidence["environment_binding"]["id"],
            environment_fingerprint=self.evidence["environment_binding"]["fingerprint"],
            side_effect_states=["NOT_APPLICABLE"],
            safety_invariants={"SAFE-01": True},
            trusted_now=self.now,
        )

    def test_completion_binds_work_harness_environment_freshness_and_digest(self) -> None:
        self.assertTrue(self.complete(self.evidence))
        mutations = (
            lambda item: item["work_binding"].update(sha256="0" * 64),
            lambda item: item["harness_binding"].update(sha256="0" * 64),
            lambda item: item["environment_binding"].update(fingerprint="0" * 64),
            lambda item: item["freshness"].update(not_after="2000-01-01T00:00:00+00:00"),
            lambda item: item.update(immutable_digest="0" * 64),
        )
        for mutate in mutations:
            evidence = copy.deepcopy(self.evidence)
            mutate(evidence)
            with self.subTest(mutation=mutate):
                self.assertFalse(self.complete(evidence))

    def test_canonical_evidence_digest_is_machine_verified(self) -> None:
        expected = conformance.canonical_digest(
            self.evidence, omitted_paths=(("immutable_digest",),)
        )
        self.assertEqual(expected, self.evidence["immutable_digest"])
        forged = copy.deepcopy(self.evidence)
        forged["checks"][0]["observation"] = "forged after signing"
        self.assertIn(
            "IMMUTABLE_DIGEST_MISMATCH",
            conformance.validate_document("evidence", forged).errors,
        )


class AttemptJournalTests(unittest.TestCase):
    def mutating_attempt(self) -> dict:
        attempt = fixture("attempt")
        receipt = {
            "schema_version": "yuan.tool-receipt/v1",
            "kind": "file-write",
            "operation_id": "OP-write-001",
            "status": "REPLACED",
            "path": ".yuan/core/0.1",
            "before_sha256": "1" * 64,
            "after_sha256": "2" * 64,
        }
        receipt_digest = conformance.canonical_digest(receipt)
        attempt["action"].update(
            {
                "type": "file-write",
                "mutating": True,
                "side_effect_class": "filesystem",
                "authorization_grant_id": "GRANT-core-candidate",
            }
        )
        attempt["journal"] = [
            {
                "ordinal": index,
                "state": state,
                "recorded_at": f"2026-07-26T14:3{index}:00+00:00",
                "receipt_sha256": receipt_digest if state in {"OBSERVED", "COMMITTED"} else None,
            }
            for index, state in enumerate(
                ("PREPARED", "EXECUTING", "OBSERVED", "COMMITTED"), start=1
            )
        ]
        attempt["side_effect_state"] = "COMMITTED"
        attempt["tool_receipt"] = receipt
        attempt["postcondition"] = {
            "scope": ".yuan/core/0.1",
            "observed_sha256": "2" * 64,
            "satisfied": True,
        }
        attempt["outcome"] = "SUCCEEDED"
        return attempt

    def test_committed_side_effect_requires_bound_receipt_and_postcondition(self) -> None:
        attempt = self.mutating_attempt()
        self.assertEqual([], conformance.validate_document("attempt", attempt).errors)
        for field in ("tool_receipt", "postcondition"):
            forged = copy.deepcopy(attempt)
            forged[field] = None
            with self.subTest(field=field):
                self.assertTrue(conformance.validate_document("attempt", forged).errors)

    def test_unknown_cannot_succeed_and_mutating_kind_cannot_disguise_itself(self) -> None:
        attempt = self.mutating_attempt()
        attempt["journal"] = attempt["journal"][:2] + [
            {
                "ordinal": 3,
                "state": "UNKNOWN",
                "recorded_at": "2026-07-26T14:33:00+00:00",
                "receipt_sha256": None,
            }
        ]
        attempt["side_effect_state"] = "UNKNOWN"
        self.assertIn(
            "UNKNOWN_OUTCOME_MISMATCH",
            conformance.validate_document("attempt", attempt).errors,
        )
        disguised = fixture("attempt")
        disguised["action"].update(type="file-write", mutating=False)
        self.assertIn(
            "MUTATING_ACTION_DISGUISED",
            conformance.validate_document("attempt", disguised).errors,
        )


class RebuildAndSelfModificationTests(unittest.TestCase):
    def test_rebuild_is_deterministic_and_fail_closed(self) -> None:
        work = fixture("work-contract")
        attempt = fixture("attempt")
        evidence = fixture("evidence")
        kwargs = {
            "current_artifact_sha256": evidence["artifact_binding"]["sha256"],
            "environment_id": evidence["environment_binding"]["id"],
            "environment_fingerprint": evidence["environment_binding"]["fingerprint"],
            "trusted_now": datetime(2026, 7, 26, 15, 0, tzinfo=timezone.utc),
        }
        rebuilt = conformance.rebuild_run_memory(work, [attempt], [evidence], **kwargs)
        self.assertEqual("COMPLETE", rebuilt["last_result"])
        repeated = conformance.rebuild_run_memory(work, [attempt], [evidence], **kwargs)
        self.assertEqual(rebuilt, repeated)
        out_of_order = copy.deepcopy(attempt)
        out_of_order["sequence"] = 2
        self.assertEqual(
            "BLOCKED",
            conformance.rebuild_run_memory(work, [out_of_order], [evidence], **kwargs)[
                "last_result"
            ],
        )
        self.assertEqual(
            "BLOCKED",
            conformance.rebuild_run_memory(
                work,
                [attempt],
                [evidence],
                expected_attempts_digest="0" * 64,
                **kwargs,
            )["last_result"],
        )

    def test_self_modification_requires_one_exact_independent_root(self) -> None:
        change = {
            "target_kind": "core",
            "candidate_binding": {"id": "core", "revision": "2", "sha256": "2" * 64},
            "previous_binding": {"id": "core", "revision": "1", "sha256": "1" * 64},
            "risk": "R0",
        }
        self.assertFalse(conformance.self_modification_authorized(change, []))
        previous_proof = {
            "kind": "previous-root",
            "root_binding": change["previous_binding"],
            "candidate_binding": change["candidate_binding"],
            "status": "PASS",
            "assertions": 1,
        }
        self.assertTrue(
            conformance.self_modification_authorized(change, [previous_proof])
        )
        forged = copy.deepcopy(previous_proof)
        forged["candidate_binding"]["revision"] = "other"
        self.assertFalse(conformance.self_modification_authorized(change, [forged]))


class AuthorizationAndSandboxTests(unittest.TestCase):
    def test_expired_or_spent_grant_waits_for_authorization(self) -> None:
        work = fixture("work-contract")
        action = {
            "type": "file-write",
            "side_effect_class": "filesystem",
            "scope": ".yuan/core/0.1/new-file",
            "authorization_grant_id": "GRANT-core-candidate",
            "high_impact": False,
        }
        charge = {"ticks": 1, "tool_calls": 1, "strategies": 1, "command_seconds": 1}
        remaining = {"ticks": 2, "tool_calls": 2, "strategies": 2, "command_seconds": 2}
        work["authorization"]["grants"][0]["expires_at"] = "2000-01-01T00:00:00+00:00"
        self.assertEqual(
            "WAIT_AUTH",
            conformance.authorization_status(
                work,
                action,
                charge,
                remaining,
                trusted_now=datetime(2026, 7, 26, tzinfo=timezone.utc),
            ),
        )
        work["authorization"]["grants"][0]["expires_at"] = None
        work["authorization"]["grants"][0]["max_uses"] = 1
        self.assertEqual(
            "WAIT_AUTH",
            conformance.authorization_status(
                work, action, charge, remaining, grant_usage={"GRANT-core-candidate": 1}
            ),
        )

    def test_python_profile_rejects_absolute_escape_and_sandboxes_hardcoded_write(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = pathlib.Path(temporary) / "root"
            root.mkdir()
            outside = root.parent / "outside.txt"
            port = reference_port.ReferencePort(
                root,
                allowed_executables=[sys.executable],
                max_command_seconds=2,
                max_output_bytes=4096,
            )
            with self.assertRaises(reference_port.CommandRejected):
                port.run_command(
                    [
                        sys.executable,
                        "-c",
                        "import pathlib,sys; pathlib.Path(sys.argv[1]).write_text('x')",
                        str(outside),
                    ],
                    timeout_seconds=1,
                )
            receipt = port.run_command(
                [
                    sys.executable,
                    "-c",
                    f"open({str(outside)!r}, 'w').write('x')",
                ],
                timeout_seconds=1,
            )
            self.assertNotEqual(0, receipt.exit_code)
            self.assertFalse(outside.exists())
            self.assertEqual("python-audit-sandbox/v1", receipt.profile)


if __name__ == "__main__":
    unittest.main()
