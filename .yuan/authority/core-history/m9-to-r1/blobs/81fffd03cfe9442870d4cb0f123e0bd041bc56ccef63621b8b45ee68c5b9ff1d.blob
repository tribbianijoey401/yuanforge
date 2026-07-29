from __future__ import annotations

import copy
import json
import unittest
from datetime import datetime, timezone

from _load import CORE_ROOT, load_core_module


conformance = load_core_module("conformance")


def fixture(kind: str) -> dict:
    return json.loads(
        (CORE_ROOT / "fixtures" / "valid" / f"{kind}.json").read_text(
            encoding="utf-8"
        )
    )


def committed_core_write(work: dict, attempt: dict, evidence: dict) -> None:
    attempt["work_binding"] = copy.deepcopy(work["revision"])
    receipt = {
        "schema_version": "yuan.tool-receipt/v1",
        "kind": "file-write",
        "operation_id": "OP-author-self-mod",
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
    attempt["side_effect_state"] = "COMMITTED"
    attempt["tool_receipt"] = receipt
    attempt["postcondition"] = {
        "scope": ".yuan/core/0.1",
        "observed_sha256": "2" * 64,
        "satisfied": True,
    }
    attempt["outcome"] = "SUCCEEDED"
    evidence["work_binding"] = copy.deepcopy(work["revision"])
    evidence["immutable_digest"] = conformance.canonical_digest(
        evidence, omitted_paths=(("immutable_digest",),)
    )


class ReplayTrustTests(unittest.TestCase):
    def setUp(self) -> None:
        self.work = fixture("work-contract")
        self.attempt = fixture("attempt")
        self.evidence = fixture("evidence")
        self.kwargs = {
            "current_artifact_sha256": self.evidence["artifact_binding"]["sha256"],
            "environment_id": self.evidence["environment_binding"]["id"],
            "environment_fingerprint": self.evidence["environment_binding"][
                "fingerprint"
            ],
            "trusted_now": datetime(2026, 7, 26, 15, 0, tzinfo=timezone.utc),
        }

    def test_protected_write_requires_replay_authorized_old_root(self) -> None:
        committed_core_write(self.work, self.attempt, self.evidence)
        unproved = conformance.rebuild_run_memory(
            self.work, [self.attempt], [self.evidence], **self.kwargs
        )
        self.assertEqual("BLOCKED", unproved["last_result"])
        self.assertIn("SELF_MODIFICATION_UNAUTHORIZED", unproved["rebuild"]["errors"])

        self_work = copy.deepcopy(self.work)
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
        self_attempt = fixture("attempt")
        self_evidence = fixture("evidence")
        committed_core_write(self_work, self_attempt, self_evidence)
        self_evidence["verifier_binding"] = copy.deepcopy(
            self_work["acceptance_criteria"][0]["verifier_binding"]
        )
        self_evidence["immutable_digest"] = conformance.canonical_digest(
            self_evidence, omitted_paths=(("immutable_digest",),)
        )
        candidate_self = conformance.rebuild_run_memory(
            self_work, [self_attempt], [self_evidence], **self.kwargs
        )
        self.assertEqual("BLOCKED", candidate_self["last_result"])

        verifier = self.work["acceptance_criteria"][0]["verifier_binding"]
        previous = {
            key: verifier[key] for key in ("id", "revision", "sha256")
        }
        change = {
            "target_kind": "core",
            "candidate_binding": {
                "id": "yuan-core",
                "revision": "0.2",
                "sha256": "2" * 64,
            },
            "previous_binding": previous,
            "risk": "R0",
        }
        self.attempt["action"]["self_modification"] = {
            "change": change,
            "proofs": [
                {
                    "kind": "previous-root",
                    "root_binding": previous,
                    "candidate_binding": change["candidate_binding"],
                    "status": "PASS",
                    "assertions": 1,
                }
            ],
        }
        proved = conformance.rebuild_run_memory(
            self.work, [self.attempt], [self.evidence], **self.kwargs
        )
        self.assertEqual("COMPLETE", proved["last_result"])

    def test_blocked_projection_preserves_current_artifact_scope(self) -> None:
        blocked = conformance.rebuild_run_memory(
            self.work,
            [self.attempt],
            [self.evidence],
            expected_attempts_digest="0" * 64,
            **self.kwargs,
        )
        self.assertEqual("BLOCKED", blocked["last_result"])
        self.assertEqual(
            self.evidence["artifact_binding"]["scope"],
            blocked["artifact_binding"]["scope"],
        )


if __name__ == "__main__":
    unittest.main()
