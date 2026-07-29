"""Author TDD for the M8 single-authority switch."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import pathlib
import shutil
import sys
import tempfile
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "scripts" / "yuan_authority.py"
sys.path.insert(0, str(MODULE_PATH.parent))
spec = importlib.util.spec_from_file_location("yuan_authority", MODULE_PATH)
assert spec and spec.loader
authority = importlib.util.module_from_spec(spec)
spec.loader.exec_module(authority)

M7_HASH = "4e8d974409bf0ad2bd66df17039c8dee12b6fca03a0e2860ed5ac865615823d4"


def digest(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class AuthoritySwitchTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory(prefix="yuan-m8-author-")
        self.repo = pathlib.Path(self.temp.name)
        shutil.copytree(ROOT / ".yuan/core", self.repo / ".yuan/core")
        (self.repo / "docs").mkdir()
        (self.repo / "docs" / "PROGRESS.md").write_text("legacy\n", encoding="utf-8")
        self.run = self.repo / ".yuan-run"
        for relative in ("contracts", "attempts", "evidence"):
            (self.run / relative).mkdir(parents=True)
        fixtures = ROOT / ".yuan/core/0.1/fixtures/valid"
        shutil.copyfile(fixtures / "work-contract.json", self.run / "contracts/work.json")
        shutil.copyfile(fixtures / "attempt.json", self.run / "attempts/0001.json")
        shutil.copyfile(fixtures / "evidence.json", self.run / "evidence/0001.json")
        (self.run / "run-memory.json").write_bytes(
            authority.canonical(authority.rebuild_runtime_memory(self.repo))
        )
        authority.seal_runtime(
            self.repo,
            self.run,
            legacy_snapshot_sha256="1" * 64,
            source_projection_sha256="2" * 64,
        )
        self.approval = self.repo / "M7-APPROVAL.json"
        self.approval.write_text(
            json.dumps(
                {
                    "verdict": "PASS",
                    "approved_semantic_registry_sha256": M7_HASH,
                    "approved_implementation_revision": "619eef9875c50c312c043f7bdf12c7331a336c04",
                    "m8_requirements": {
                        "authority_receipt_must_bind_semantic_registry_sha256": True
                    },
                }
            ),
            encoding="utf-8",
        )

    def tearDown(self) -> None:
        self.temp.cleanup()

    def initialize(self) -> str:
        return authority.initialize_authority(
            self.repo,
            legacy_snapshot_sha256="1" * 64,
            m7_approval=self.approval,
            expected_m7_sha256=M7_HASH,
        )

    def switch(self, target: str, expected_pointer: str) -> dict:
        return authority.switch_authority(
            self.repo,
            target=target,
            expected_pointer_sha256=expected_pointer,
            m7_approval=self.approval,
            expected_m7_sha256=M7_HASH,
        )

    def test_initialize_creates_content_addressed_legacy_record(self) -> None:
        pointer_hash = self.initialize()
        pointer = authority.load_current(self.repo)
        self.assertEqual(pointer_hash, digest(self.repo / ".yuan/authority/current"))
        self.assertEqual("legacy", pointer["record"]["authority"])
        self.assertIsNone(pointer["record"]["previous_record_sha256"])
        self.assertEqual(M7_HASH, pointer["record"]["m7_semantic_registry_sha256"])
        self.assertTrue(pointer["record_path"].is_file())

    def test_drill_legacy_core_legacy_core_preserves_hash_chain(self) -> None:
        pointer_hash = self.initialize()
        first = self.switch("core", pointer_hash)
        second = self.switch("legacy", first["pointer_after_sha256"])
        final = self.switch("core", second["pointer_after_sha256"])
        verified = authority.verify_authority(self.repo)
        self.assertEqual("PASS", verified["status"])
        self.assertEqual("core", verified["authority"])
        self.assertEqual(4, verified["revision"])
        self.assertEqual(4, verified["history_length"])
        self.assertEqual(M7_HASH, final["m7_semantic_registry_sha256"])

    def test_stale_pointer_cas_is_rejected(self) -> None:
        pointer_hash = self.initialize()
        first = self.switch("core", pointer_hash)
        with self.assertRaisesRegex(authority.AuthorityError, "CAS"):
            self.switch("legacy", pointer_hash)
        self.assertEqual(
            first["pointer_after_sha256"],
            digest(self.repo / ".yuan/authority/current"),
        )

    def test_wrong_or_unapproved_m7_hash_is_rejected(self) -> None:
        pointer_hash = self.initialize()
        with self.assertRaisesRegex(authority.AuthorityError, "M7"):
            authority.switch_authority(
                self.repo,
                target="core",
                expected_pointer_sha256=pointer_hash,
                m7_approval=self.approval,
                expected_m7_sha256="0" * 64,
            )
        payload = json.loads(self.approval.read_text(encoding="utf-8"))
        payload["verdict"] = "FAIL"
        self.approval.write_text(json.dumps(payload), encoding="utf-8")
        with self.assertRaisesRegex(authority.AuthorityError, "M7"):
            self.switch("core", pointer_hash)

    def test_core_guard_rejects_legacy_and_existing_immutable_writes(self) -> None:
        pointer_hash = self.initialize()
        self.switch("core", pointer_hash)
        with self.assertRaisesRegex(authority.AuthorityError, "inactive"):
            authority.assert_write_allowed(
                self.repo, "legacy", "docs/PROGRESS.md", digest(self.repo / "docs/PROGRESS.md")
            )
        with self.assertRaisesRegex(authority.AuthorityError, "immutable"):
            authority.assert_write_allowed(
                self.repo, "core", ".yuan-run/attempts/0001.json", digest(self.run / "attempts/0001.json")
            )
        target = authority.assert_write_allowed(
            self.repo, "core", ".yuan-run/evidence/0002.json", None
        )
        self.assertEqual(self.run / "evidence" / "0002.json", target)

    def test_run_memory_requires_cas_and_tamper_blocks_switch(self) -> None:
        pointer_hash = self.initialize()
        self.switch("core", pointer_hash)
        with self.assertRaisesRegex(authority.AuthorityError, "CAS"):
            authority.assert_write_allowed(
                self.repo, "core", ".yuan-run/run-memory.json", None
            )
        (self.run / "contracts" / "work.json").write_text("tampered\n", encoding="utf-8")
        current = digest(self.repo / ".yuan/authority/current")
        with self.assertRaisesRegex(authority.AuthorityError, "runtime"):
            self.switch("legacy", current)

    def test_record_tamper_breaks_history_verification(self) -> None:
        pointer_hash = self.initialize()
        self.switch("core", pointer_hash)
        current = authority.load_current(self.repo)
        current["record_path"].write_text("{}\n", encoding="utf-8")
        with self.assertRaisesRegex(authority.AuthorityError, "record"):
            authority.verify_authority(self.repo)


class AgentBindingTests(unittest.TestCase):
    def test_legacy_agents_binding_is_exact_and_recoverable(self) -> None:
        binding = json.loads(
            (ROOT / ".yuan/authority/legacy-bindings/AGENTS.json").read_text(
                encoding="utf-8"
            )
        )
        registry = json.loads(
            (ROOT / ".yuan/extensions/provenance/semantic-registry.json").read_text(
                encoding="utf-8"
            )
        )
        records = [item for item in registry["records"] if item["source"] == "AGENTS.md"]
        self.assertEqual(
            binding["source_sha256"],
            "d282f61862b19ab42fe4933584fa4dd5b893650c38776ba2e9a3c97fb8d45d7a",
        )
        self.assertEqual(
            binding["semantic_record_keys"],
            [item["record_key"] for item in records],
        )
        for record in records:
            self.assertTrue((ROOT / record["destination"]["path"]).is_file())


if __name__ == "__main__":
    unittest.main()
