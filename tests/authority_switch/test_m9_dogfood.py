"""Author-side M9 live-Core self-modification dogfood tests."""

from __future__ import annotations

import json
import pathlib
import shutil
import sys
import tempfile
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from yuan_authority import AuthorityError, verify_authority
from yuan_m9_dogfood import (
    MutationCrash,
    build_candidate_manifest,
    build_protocol,
    install,
    recover_mutation,
    verify_dogfood,
)
from yuan_runtime_state import resolve_runtime_root
from yuan_runtime_state import atomic_write, canonical, file_sha256
from yuan_runtime_transaction import InjectedCrash, recover_runtime_transaction


class M9DogfoodTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory(prefix="yuan-m9-dogfood-")
        self.repo = pathlib.Path(self.temp.name)
        for relative in (".yuan", ".yuan-run", "scripts", "tests"):
            shutil.copytree(ROOT / relative, self.repo / relative)
        current = json.loads(
            (self.repo / ".yuan/authority/current").read_text(encoding="utf-8")
        )
        record = json.loads(
            (
                self.repo
                / ".yuan/authority/records"
                / f"{current['record_sha256']}.json"
            ).read_text(encoding="utf-8")
        )
        if record["revision"] == 7:
            self._restore_revision_six(record)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def _restore_revision_six(self, revision_seven: dict) -> None:
        atomic_write(
            self.repo / ".yuan/authority/current",
            canonical(
                {
                    "schema_version": "yuan.authority-current/v1",
                    "record_sha256": revision_seven["previous_record_sha256"],
                }
            ),
            file_sha256(self.repo / ".yuan/authority/current"),
        )
        run_id = "WORK-yuan-m8-m9-successor-r2-398b8aefe078"
        atomic_write(
            self.repo / ".yuan-run/active-run.json",
            canonical(
                {
                    "schema_version": "yuan.active-run/v1",
                    "run_id": run_id,
                    "runtime_root": f".yuan-run/runs/{run_id}",
                    "manifest_sha256": (
                        "e2bc36fc5d0213912e46073bf4ca2a8aa52091311e7870e34c1f1987a3b64abe"
                    ),
                }
            ),
            file_sha256(self.repo / ".yuan-run/active-run.json"),
        )
        history = self.repo / ".yuan/authority/core-history/r2-to-m9/blobs"
        protocol = self.repo / ".yuan/core/0.1/protocol.md"
        manifest = self.repo / ".yuan/core/0.1/candidate-manifest.json"
        protocol.write_bytes(
            (
                history
                / "b61422bd4f76033234908fb89c149cccc0ebffd5b502e21eea5e26cd82a9c3c3.blob"
            ).read_bytes()
        )
        manifest.write_bytes(
            (
                history
                / "57a2acad6ba92d879785139e35548bdd20cd1edcafa3d7e8b554321504ec8b5e.blob"
            ).read_bytes()
        )
        descriptor = self.repo / ".yuan/authority/activation/yuan-core-0.1.json"
        descriptor.write_bytes(
            (
                self.repo
                / ".yuan/authority/activation/history"
                / "6f08c7e10bcd433e2341471bef463e0d37fe6b6c7356f400988868a1b129afe8.blob"
            ).read_bytes()
        )
        for name in (
            "WORK-yuan-m8-m9-successor-g0002-80c48920a4b0",
            "WORK-yuan-m8-m9-successor-r3-24820e1e41b7",
        ):
            shutil.rmtree(self.repo / ".yuan-run/runs" / name)
        shutil.rmtree(self.repo / ".yuan/authority/self-modification")
        for name in (
            "old-root-manifest-m9.json",
            "old-root-receipt-m9.json",
            "old-root-manifest-m9-work3.json",
            "old-root-receipt-m9-work3.json",
        ):
            (self.repo / ".yuan/authority/self-modification/evidence" / name).unlink(
                missing_ok=True
            )
        (
            self.repo
            / ".yuan/authority/transactions"
            / "c62e75b40584a24de0eadd1beb64d3747735c70d6b3a069836717cd7da99878f.json"
        ).unlink()

    def test_planned_protocol_and_manifest_are_external_activation_only(self) -> None:
        protocol = build_protocol(
            (self.repo / ".yuan/core/0.1/protocol.md").read_bytes()
        ).decode("utf-8")
        self.assertIn("Revision: `yuan.core.protocol/0.1.0`", protocol)
        self.assertIn("Status: stable protocol; default inert.", protocol)
        self.assertIn("External-activation rule", protocol)
        self.assertNotIn("Status: inert candidate", protocol)
        previous = json.loads(
            (self.repo / ".yuan/core/0.1/candidate-manifest.json").read_text(
                encoding="utf-8"
            )
        )
        manifest = build_candidate_manifest(self.repo, previous, protocol.encode())
        self.assertEqual("yuan.core/0.1.0", manifest["candidate_revision"])
        self.assertEqual("yuan.core.protocol/0.1.0", manifest["protocol_revision"])
        self.assertEqual("inert-by-default", manifest["authority"])
        self.assertFalse(manifest["self_trust"])
        self.assertEqual(
            "external-content-addressed-authority",
            manifest["activation"]["mode"],
        )

    def test_live_dogfood_advances_to_wait_auth_and_revision_seven(self) -> None:
        result = install(self.repo)
        verified = verify_authority(self.repo)
        runtime, _, _ = resolve_runtime_root(self.repo)
        memory = json.loads((runtime / "run-memory.json").read_text(encoding="utf-8"))
        work = json.loads(next((runtime / "contracts").glob("*.json")).read_text())
        self.assertEqual("PASS", result["status"])
        self.assertEqual(7, verified["revision"])
        self.assertEqual(7, verified["history_length"])
        self.assertEqual("3", work["revision"]["revision"])
        self.assertEqual("WAIT_AUTH", memory["last_result"])
        self.assertEqual(
            "AC-M9-LEGACY-TOMBSTONE-WAIT-AUTH",
            memory["legal_next_steps"][0]["ac_id"],
        )
        receipt = verify_dogfood(self.repo)
        self.assertEqual(2, receipt["attempts"])
        self.assertEqual(2, receipt["evidence"])
        self.assertEqual(
            ["PREPARED", "EXECUTING", "OBSERVED", "COMMITTED"],
            receipt["journal_states"],
        )
        self.assertGreaterEqual(receipt["independent_assertions"], 30)

    def test_rev7_pointer_crash_is_blocked_and_recoverable(self) -> None:
        with self.assertRaises(InjectedCrash) as caught:
            install(self.repo, failure_after="active-pointer")
        with self.assertRaises(AuthorityError):
            verify_authority(self.repo)
        first = recover_runtime_transaction(
            self.repo, caught.exception.transaction_id
        )
        second = recover_runtime_transaction(
            self.repo, caught.exception.transaction_id
        )
        self.assertEqual("COMMITTED", first["state"])
        self.assertEqual(first, second)
        self.assertEqual(7, verify_authority(self.repo)["revision"])

    def test_wrong_root_or_candidate_proof_is_rejected(self) -> None:
        with self.assertRaises(AuthorityError):
            install(self.repo, proof_attack="wrong-root")
        self.assertEqual(6, verify_authority(self.repo)["revision"])
        with self.assertRaises(AuthorityError):
            install(self.repo, proof_attack="wrong-candidate")
        self.assertEqual(6, verify_authority(self.repo)["revision"])

    def test_interrupted_mutation_rolls_back_without_new_core_trust(self) -> None:
        protocol = self.repo / ".yuan/core/0.1/protocol.md"
        manifest = self.repo / ".yuan/core/0.1/candidate-manifest.json"
        before = (protocol.read_bytes(), manifest.read_bytes())
        with self.assertRaises(MutationCrash) as caught:
            install(self.repo, mutation_failure_after="protocol")
        with self.assertRaises(Exception):
            verify_authority(self.repo)
        first = recover_mutation(self.repo, caught.exception.transaction_id)
        second = recover_mutation(self.repo, caught.exception.transaction_id)
        self.assertEqual("ROLLED_BACK", first["state"])
        self.assertEqual(first, second)
        self.assertEqual(before, (protocol.read_bytes(), manifest.read_bytes()))
        self.assertEqual(6, verify_authority(self.repo)["revision"])


if __name__ == "__main__":
    unittest.main()
