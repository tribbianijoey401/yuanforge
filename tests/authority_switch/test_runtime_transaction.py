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
        evidence = copy.deepcopy(previous_evidence)
        evidence.update(
            {
                "evidence_id": f"EVD-tx-{sequence:04d}",
                "sequence": len(evidence_items) + 1,
                "work_binding": work["revision"],
                "source_attempt_id": attempt["attempt_id"],
                "ac_id": work["acceptance_criteria"][-1]["id"],
                "kind": work["acceptance_criteria"][-1]["type"],
                "verifier_binding": {
                    key: work["acceptance_criteria"][-1]["verifier_binding"][key]
                    for key in ("id", "revision", "sha256", "trust_root_id")
                },
                "harness_binding": work["harness_binding"],
            }
        )
        evidence["immutable_digest"] = transaction.canonical_digest(
            evidence, omitted_paths=(("immutable_digest",),)
        )
        return attempt, evidence

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
        transaction.append_runtime_transaction(
            self.repo,
            first_attempt,
            first_evidence,
            expected_authority_pointer_sha256=authority_before,
            expected_active_run_pointer_sha256=active_before,
        )
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


if __name__ == "__main__":
    unittest.main()
