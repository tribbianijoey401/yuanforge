"""Adversarial tests for generation-based runtime append transactions."""

from __future__ import annotations

import copy
import importlib.util
import json
import pathlib
import shutil
import sys
import tempfile
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "scripts/yuan_runtime_transaction.py"
sys.path.insert(0, str(MODULE_PATH.parent))
spec = importlib.util.spec_from_file_location("yuan_runtime_transaction", MODULE_PATH)
assert spec and spec.loader
transaction = importlib.util.module_from_spec(spec)
spec.loader.exec_module(transaction)
from yuan_successor_run import install_successor_run
from yuan_r2_successor import install as install_r2_successor


class RuntimeTransactionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory(prefix="yuan-r1-tx-")
        self.repo = pathlib.Path(self.temp.name)
        for relative in (
            ".yuan",
            ".yuan-run",
            "scripts",
            "tests/core_01",
        ):
            shutil.copytree(ROOT / relative, self.repo / relative)
        if not (self.repo / ".yuan-run/active-run.json").is_file():
            install_successor_run(self.repo)
        if transaction.load_current(self.repo)["record"]["revision"] < 6:
            install_r2_successor(self.repo)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def proposed_records(self) -> tuple[dict, dict]:
        runtime, _, _ = transaction.resolve_runtime_root(self.repo)
        work = json.loads(next((runtime / "contracts").glob("*.json")).read_text())
        attempts = sorted((runtime / "attempts").glob("*.json"))
        evidence_items = sorted((runtime / "evidence").glob("*.json"))
        previous_evidence = json.loads(evidence_items[-1].read_text())
        sequence = len(attempts) + 1
        attempt = json.loads(attempts[-1].read_text())
        attempt.update(
            {
                "attempt_id": f"ATT-tx-{sequence:04d}",
                "sequence": sequence,
                "work_binding": work["revision"],
                "protocol_binding": work["protocol_binding"],
                "harness_binding": work["harness_binding"],
                "evidence_ids": [f"EVD-tx-{sequence:04d}"],
            }
        )
        ac = next(
            item
            for item in work["acceptance_criteria"]
            if item["id"] == "AC-M9-SELF-MODIFICATION-DOGFOOD"
        )
        attempt["action"].update(
            {
                "type": "verify",
                "mutating": False,
                "side_effect_class": "none",
                "scope": ac["artifact_scope"],
                "authorization_grant_id": "GRANT-CORE-M8-M9",
                "high_impact": False,
                "self_modification": None,
            }
        )
        evidence = copy.deepcopy(previous_evidence)
        artifact_sha = transaction.artifact_binding_sha256(
            self.repo, ac["artifact_scope"]
        )
        environment_id = ac["verifier_binding"]["environment_ids"][0]
        evidence.update(
            {
                "evidence_id": f"EVD-tx-{sequence:04d}",
                "sequence": len(evidence_items) + 1,
                "work_binding": work["revision"],
                "source_attempt_id": attempt["attempt_id"],
                "ac_id": ac["id"],
                "kind": ac["type"],
                "verifier_binding": {
                    key: ac["verifier_binding"][key]
                    for key in ("id", "revision", "sha256", "trust_root_id")
                },
                "artifact_binding": {
                    "scope": ac["artifact_scope"],
                    "sha256": artifact_sha,
                },
                "environment_binding": {
                    "id": environment_id,
                    "fingerprint": ac["verifier_binding"][
                        "environment_fingerprints"
                    ][environment_id],
                },
                "harness_binding": work["harness_binding"],
                "status": "PASS",
                "assertions": ac["verifier_binding"]["minimum_assertions"],
                "checks": [
                    {
                        "id": f"M9-CHECK-{index:02d}",
                        "status": "PASS",
                        "observation": "independent held-out assertion passed",
                    }
                    for index in range(ac["verifier_binding"]["minimum_assertions"])
                ],
                "freshness": {
                    "observed_artifact_sha256": artifact_sha,
                    "not_after": None,
                },
                "independence": {
                    "independent": True,
                    "method": "held-out",
                    "author_identity": "backend-dev-task-011-r2",
                    "verifier_identity": "independent-tester-task-011-r1",
                },
            }
        )
        evidence["immutable_digest"] = transaction.canonical_digest(
            evidence, omitted_paths=(("immutable_digest",),)
        )
        return attempt, evidence

    def repository_state(self) -> dict[str, str]:
        result = {}
        for root in (self.repo / ".yuan-run", self.repo / ".yuan/authority"):
            for path in sorted(root.rglob("*")):
                if path.is_file():
                    result[path.relative_to(self.repo).as_posix()] = (
                        transaction.file_sha256(path)
                    )
        return result

    def test_half_write_fails_closed_and_recovers(self) -> None:
        attempt, evidence = self.proposed_records()
        authority_before = transaction.file_sha256(
            self.repo / ".yuan/authority/current"
        )
        active_before = transaction.file_sha256(
            self.repo / ".yuan-run/active-run.json"
        )
        with self.assertRaises(transaction.InjectedCrash) as caught:
            transaction.append_runtime_transaction(
                self.repo,
                attempt,
                evidence,
                expected_authority_pointer_sha256=authority_before,
                expected_active_run_pointer_sha256=active_before,
                failure_after="active-pointer",
            )
        with self.assertRaises(transaction.AuthorityError):
            transaction.verify_authority(self.repo)
        receipt = transaction.recover_runtime_transaction(
            self.repo, caught.exception.transaction_id
        )
        self.assertEqual("COMMITTED", receipt["state"])
        self.assertEqual("PASS", transaction.verify_authority(self.repo)["status"])

    def test_stale_concurrent_cas_and_tampered_generation_are_rejected(self) -> None:
        first_attempt, first_evidence = self.proposed_records()
        authority_before = transaction.file_sha256(
            self.repo / ".yuan/authority/current"
        )
        active_before = transaction.file_sha256(
            self.repo / ".yuan-run/active-run.json"
        )
        committed = transaction.append_runtime_transaction(
            self.repo,
            first_attempt,
            first_evidence,
            expected_authority_pointer_sha256=authority_before,
            expected_active_run_pointer_sha256=active_before,
        )
        self.assertEqual("COMMITTED", committed["state"])
        second_attempt, second_evidence = self.proposed_records()
        with self.assertRaises(transaction.AuthorityError):
            transaction.append_runtime_transaction(
                self.repo,
                second_attempt,
                second_evidence,
                expected_authority_pointer_sha256=authority_before,
                expected_active_run_pointer_sha256=active_before,
            )

        authority_now = transaction.file_sha256(
            self.repo / ".yuan/authority/current"
        )
        active_now = transaction.file_sha256(
            self.repo / ".yuan-run/active-run.json"
        )
        with self.assertRaises(transaction.InjectedCrash) as caught:
            transaction.append_runtime_transaction(
                self.repo,
                second_attempt,
                second_evidence,
                expected_authority_pointer_sha256=authority_now,
                expected_active_run_pointer_sha256=active_now,
                failure_after="generation",
            )
        journal = json.loads(
            (
                self.repo
                / ".yuan/authority/transactions"
                / f"{caught.exception.transaction_id}.json"
            ).read_text()
        )
        generation = self.repo / journal["runtime_root"]
        next((generation / "evidence").glob("*.json")).write_text("{}\n")
        with self.assertRaises(transaction.AuthorityError):
            transaction.recover_runtime_transaction(
                self.repo, caught.exception.transaction_id
            )

    def test_forged_evidence_combinations_write_nothing(self) -> None:
        mutations = {
            "verifier": lambda a, e: e["verifier_binding"].update(id="forged"),
            "artifact": lambda a, e: e["artifact_binding"].update(sha256="0" * 64),
            "environment": lambda a, e: e["environment_binding"].update(
                fingerprint="0" * 64
            ),
            "harness": lambda a, e: e["harness_binding"].update(sha256="0" * 64),
            "work": lambda a, e: e["work_binding"].update(sha256="0" * 64),
            "independence": lambda a, e: e["independence"].update(
                independent=False
            ),
            "freshness": lambda a, e: e["freshness"].update(
                not_after="2000-01-01T00:00:00+00:00"
            ),
            "attempt-reference": lambda a, e: e.update(
                source_attempt_id="ATT-missing"
            ),
            "duplicate-check": lambda a, e: e["checks"].__setitem__(
                1, copy.deepcopy(e["checks"][0])
            ),
            "failed-check": lambda a, e: e["checks"][0].update(status="FAIL"),
        }
        authority_before = transaction.file_sha256(
            self.repo / ".yuan/authority/current"
        )
        active_before = transaction.file_sha256(
            self.repo / ".yuan-run/active-run.json"
        )
        for name, mutate in mutations.items():
            with self.subTest(name=name):
                attempt, evidence = self.proposed_records()
                mutate(attempt, evidence)
                evidence["immutable_digest"] = transaction.canonical_digest(
                    evidence, omitted_paths=(("immutable_digest",),)
                )
                before = self.repository_state()
                receipt = transaction.append_runtime_transaction(
                    self.repo,
                    attempt,
                    evidence,
                    expected_authority_pointer_sha256=authority_before,
                    expected_active_run_pointer_sha256=active_before,
                )
                self.assertEqual("REJECTED", receipt["state"])
                self.assertEqual(before, self.repository_state())


if __name__ == "__main__":
    unittest.main()
