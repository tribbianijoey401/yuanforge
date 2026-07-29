"""Crash-window and activation closure tests for task-011-r2."""

from __future__ import annotations

import hashlib
import json
import pathlib
import shutil
import sys
import tempfile
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from yuan_authority import AuthorityError, verify_authority
from yuan_activation import verify_activation_descriptor
from yuan_r2_successor import install
from yuan_runtime_state import atomic_write, canonical, file_sha256
from yuan_runtime_transaction import (
    InjectedCrash,
    recover_runtime_transaction,
)


class R2SuccessorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory(prefix="yuan-r2-successor-")
        self.repo = pathlib.Path(self.temp.name)
        for relative in (".yuan", ".yuan-run", "scripts"):
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
        (self.repo / ".yuan/core/0.1/protocol.md").write_bytes(
            (
                history
                / "b61422bd4f76033234908fb89c149cccc0ebffd5b502e21eea5e26cd82a9c3c3.blob"
            ).read_bytes()
        )
        (self.repo / ".yuan/core/0.1/candidate-manifest.json").write_bytes(
            (
                history
                / "57a2acad6ba92d879785139e35548bdd20cd1edcafa3d7e8b554321504ec8b5e.blob"
            ).read_bytes()
        )
        (
            self.repo / ".yuan/authority/activation/yuan-core-0.1.json"
        ).write_bytes(
            (
                self.repo
                / ".yuan/authority/activation/history"
                / "6f08c7e10bcd433e2341471bef463e0d37fe6b6c7356f400988868a1b129afe8.blob"
            ).read_bytes()
        )

    def _restore_r1_activation_point(self) -> None:
        current = json.loads(
            (self.repo / ".yuan/authority/current").read_text(encoding="utf-8")
        )
        revision_six = json.loads(
            (
                self.repo
                / ".yuan/authority/records"
                / f"{current['record_sha256']}.json"
            ).read_text(encoding="utf-8")
        )
        atomic_write(
            self.repo / ".yuan/authority/current",
            canonical(
                {
                    "schema_version": "yuan.authority-current/v1",
                    "record_sha256": revision_six["previous_record_sha256"],
                }
            ),
            file_sha256(self.repo / ".yuan/authority/current"),
        )
        r1_run_id = "WORK-yuan-m8-m9-successor-g0001-867cca673431"
        atomic_write(
            self.repo / ".yuan-run/active-run.json",
            canonical(
                {
                    "schema_version": "yuan.active-run/v1",
                    "run_id": r1_run_id,
                    "runtime_root": f".yuan-run/runs/{r1_run_id}",
                    "manifest_sha256": (
                        "14481ac160b7d42440ab52fa5c533159f683d598fa9025dc824043dee4fff4de"
                    ),
                }
            ),
            file_sha256(self.repo / ".yuan-run/active-run.json"),
        )
        shutil.rmtree(
            self.repo
            / ".yuan-run/runs/WORK-yuan-m8-m9-successor-r2-398b8aefe078"
        )
        (
            self.repo
            / ".yuan/authority/transactions"
            / "7560a2e5b9e6ab0022cf92a8abdb46e8d47b5687a29ac7f4154c27cc33562881.json"
        ).unlink()

    def test_active_pointer_crash_fails_closed_and_recovers_idempotently(self) -> None:
        self._restore_r1_activation_point()
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
        verified = verify_authority(self.repo)
        self.assertEqual(6, verified["revision"])
        self.assertEqual("PASS", verified["status"])

    def test_authority_rejects_every_tampered_activation_dependency(self) -> None:
        targets = (
            ".yuan/core/0.1/runtime_replay.py",
            ".yuan/core/0.1/candidate-manifest.json",
            ".yuan/authority/activation/evidence/old-root-manifest.json",
            ".yuan/authority/activation/evidence/old-root-manifest-r2.json",
            ".yuan/authority/activation/evidence/old-root-receipt-r2.json",
            ".yuan/authority/activation/yuan-core-0.1.json",
            (
                ".yuan/authority/activation/verifiers/"
                "7154a335c742a39fe44c4d1d8c3e803330d75c807ef2fed39c58855d95e1d103.blob"
            ),
            (
                ".yuan/authority/core-history/m7-to-m8/blobs/"
                "20ac1cbb7f2377d5cecadf3347a40d81e14e8469c6c914701f585a49903d9768.blob"
            ),
            (
                ".yuan/authority/core-history/m8-r1-to-r2/blobs/"
                "53b47a9803965be4f81f81ad4081023571af24917c132c38fa777b6d73fc91e1.blob"
            ),
            (
                ".yuan/authority/activation/history/"
                "b590944715e515b6533371e461bfb4afdd87d6d89ba4a75e196336d4d1cb36dd.blob"
            ),
        )
        for relative in targets:
            with self.subTest(relative=relative):
                path = self.repo / relative
                original = path.read_bytes()
                path.write_bytes(original + b"\nTAMPER")
                try:
                    with self.assertRaises(AuthorityError):
                        verify_authority(self.repo)
                finally:
                    path.write_bytes(original)

    def test_manifest_replacement_and_path_attacks_fail_mechanically(self) -> None:
        manifest_path = self.repo / ".yuan/core/0.1/candidate-manifest.json"
        descriptor_path = (
            self.repo / ".yuan/authority/activation/yuan-core-0.1.json"
        )
        original_manifest = manifest_path.read_bytes()
        original_descriptor = descriptor_path.read_bytes()
        manifest = json.loads(original_manifest)
        attacks = (
            {},
            {
                **manifest,
                "files": [
                    {**manifest["files"][0], "path": "../outside"},
                    *manifest["files"][1:],
                ],
            },
            {
                **manifest,
                "files": [
                    {**manifest["files"][0], "sha256": "0" * 64},
                    *manifest["files"][1:],
                ],
            },
        )
        for attack in attacks:
            with self.subTest(attack=attack.get("files", "replacement")):
                encoded = canonical(attack)
                manifest_path.write_bytes(encoded)
                descriptor = json.loads(original_descriptor)
                manifest_sha = hashlib.sha256(encoded).hexdigest()
                descriptor["activated_candidate_manifest_sha256"] = manifest_sha
                descriptor["candidate_manifest_sha256"] = manifest_sha
                descriptor_path.write_bytes(canonical(descriptor))
                try:
                    with self.assertRaises(AuthorityError):
                        verify_activation_descriptor(self.repo)
                finally:
                    manifest_path.write_bytes(original_manifest)
                    descriptor_path.write_bytes(original_descriptor)

    def test_manifest_missing_file_fails_authority_verification(self) -> None:
        target = self.repo / ".yuan/core/0.1/completion_semantics.py"
        target.unlink()
        with self.assertRaises(AuthorityError):
            verify_authority(self.repo)


if __name__ == "__main__":
    unittest.main()
