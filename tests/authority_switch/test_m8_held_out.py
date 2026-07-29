"""Independent M8 held-out tests for the Yuan runtime authority switch."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import pathlib
import shutil
import subprocess
import sys
import tempfile
import types
import unittest
from unittest import mock


ROOT = pathlib.Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "scripts"
M7_HASH = "4e8d974409bf0ad2bd66df17039c8dee12b6fca03a0e2860ed5ac865615823d4"
M0_AGENTS_HASH = "d282f61862b19ab42fe4933584fa4dd5b893650c38776ba2e9a3c97fb8d45d7a"


def load_module(name: str, path: pathlib.Path):
    sys.path.insert(0, str(path.parent))
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


authority = load_module("m8_held_out_authority", SCRIPTS / "yuan_authority.py")
precommit = load_module("m8_held_out_precommit", SCRIPTS / "yuan_precommit.py")


def digest_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def digest(path: pathlib.Path) -> str:
    return digest_bytes(path.read_bytes())


def json_file(path: pathlib.Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


class IndependentAuthorityEvidenceTests(unittest.TestCase):
    def test_current_pointer_and_complete_history_are_content_addressed(self) -> None:
        pointer_path = ROOT / ".yuan/authority/current"
        pointer_bytes = pointer_path.read_bytes()
        pointer = json.loads(pointer_bytes)
        record_sha = pointer["record_sha256"]
        history = []
        while record_sha is not None:
            path = ROOT / ".yuan/authority/records" / f"{record_sha}.json"
            payload = path.read_bytes()
            self.assertEqual(record_sha, digest_bytes(payload))
            record = json.loads(payload)
            history.append(record)
            record_sha = record["previous_record_sha256"]

        history.reverse()
        self.assertEqual([1, 2, 3, 4], [item["revision"] for item in history])
        self.assertEqual(
            ["legacy", "core", "legacy", "core"],
            [item["authority"] for item in history],
        )
        self.assertEqual(
            [None, "legacy", "core", "legacy"],
            [item["receipt"]["from"] for item in history],
        )
        self.assertEqual(
            ["legacy", "core", "legacy", "core"],
            [item["receipt"]["to"] for item in history],
        )
        self.assertTrue(all(item["receipt"]["single_writable_authority"] for item in history))
        self.assertTrue(all(not item["receipt"]["dual_write"] for item in history))
        self.assertEqual(M7_HASH, history[-1]["m7_semantic_registry_sha256"])
        self.assertEqual(digest(pointer_path), digest_bytes(pointer_bytes))
        self.assertEqual("PASS", authority.verify_authority(ROOT)["status"])

    def test_rollback_drill_preserves_both_state_planes_and_writer_exclusion(self) -> None:
        with tempfile.TemporaryDirectory(prefix="yuan-m8-held-rollback-") as name:
            repo = pathlib.Path(name)
            for source in (".yuan/core", ".yuan/authority", ".yuan-run"):
                shutil.copytree(ROOT / source, repo / source)
            approval = pathlib.Path(
                "docs/20260726-yuan-core-01-upgrade/evidence/m7-review/M7-APPROVAL.json"
            )
            (repo / approval).parent.mkdir(parents=True)
            shutil.copyfile(ROOT / approval, repo / approval)
            (repo / "docs").mkdir(exist_ok=True)
            (repo / "docs/PROGRESS.md").write_text("legacy-state\n", encoding="utf-8")

            legacy_before = digest(repo / "docs/PROGRESS.md")
            runtime_before = digest(repo / ".yuan-run/runtime-manifest.json")
            pointer_before = digest(repo / ".yuan/authority/current")
            rolled = authority.switch_authority(
                repo,
                target="legacy",
                expected_pointer_sha256=pointer_before,
                m7_approval=repo / approval,
                expected_m7_sha256=M7_HASH,
            )
            with self.assertRaisesRegex(authority.AuthorityError, "inactive"):
                authority.assert_write_allowed(
                    repo, "core", ".yuan-run/evidence/new.json", None
                )
            authority.assert_write_allowed(
                repo, "legacy", "docs/PROGRESS.md", legacy_before
            )
            with self.assertRaisesRegex(authority.AuthorityError, "CAS"):
                authority.switch_authority(
                    repo,
                    target="core",
                    expected_pointer_sha256=pointer_before,
                    m7_approval=repo / approval,
                    expected_m7_sha256=M7_HASH,
                )
            final = authority.switch_authority(
                repo,
                target="core",
                expected_pointer_sha256=rolled["pointer_after_sha256"],
                m7_approval=repo / approval,
                expected_m7_sha256=M7_HASH,
            )
            self.assertEqual("core", authority.verify_authority(repo)["authority"])
            self.assertEqual(legacy_before, digest(repo / "docs/PROGRESS.md"))
            self.assertEqual(runtime_before, digest(repo / ".yuan-run/runtime-manifest.json"))
            self.assertEqual("core", final["to"])

    def test_m0_dirty_files_and_m7_agents_binding_are_byte_recoverable(self) -> None:
        tracked = {}
        for row in (
            ROOT
            / "docs/20260726-yuan-core-01-upgrade/evidence/m0a/tracked-dirty.tsv"
        ).read_text(encoding="utf-8").splitlines()[1:]:
            path, sha256, *_ = row.split("\t")
            tracked[path] = sha256
        untracked = {}
        for row in (
            ROOT
            / "docs/20260726-yuan-core-01-upgrade/evidence/m0a/untracked-files.tsv"
        ).read_text(encoding="utf-8").splitlines()[1:]:
            path, sha256, *_ = row.split("\t")
            untracked[path] = sha256
        for path, expected in {**tracked, **untracked}.items():
            if path != "AGENTS.md":
                self.assertEqual(expected, digest(ROOT / path), path)

        binding = json_file(ROOT / ".yuan/authority/legacy-bindings/AGENTS.json")
        registry = json_file(ROOT / ".yuan/extensions/provenance/semantic-registry.json")
        records = [item for item in registry["records"] if item["source"] == "AGENTS.md"]
        records.sort(key=lambda item: item["byte_start"])
        recovered = bytearray()
        expected_start = 0
        for item in records:
            self.assertEqual(expected_start, item["byte_start"])
            clause = (ROOT / item["destination"]["path"]).read_bytes()
            self.assertEqual(item["clause_sha256"], digest_bytes(clause))
            self.assertEqual(item["byte_end"] - item["byte_start"], len(clause))
            recovered.extend(clause)
            expected_start = item["byte_end"]
        self.assertEqual(M0_AGENTS_HASH, digest_bytes(bytes(recovered)))
        self.assertEqual(M0_AGENTS_HASH, binding["source_sha256"])
        self.assertEqual(M7_HASH, binding["semantic_registry_sha256"])
        self.assertEqual(
            binding["semantic_record_keys"],
            [item["record_key"] for item in records],
        )

    def test_one_work_and_37_histories_rebuild_memory_byte_for_byte(self) -> None:
        contracts = list((ROOT / ".yuan-run/contracts").glob("*.json"))
        attempts = list((ROOT / ".yuan-run/attempts").glob("*.json"))
        evidence = list((ROOT / ".yuan-run/evidence").glob("*.json"))
        self.assertEqual((1, 37, 37), (len(contracts), len(attempts), len(evidence)))
        rebuilt = authority.canonical(authority.rebuild_runtime_memory(ROOT))
        self.assertEqual((ROOT / ".yuan-run/run-memory.json").read_bytes(), rebuilt)

    def test_clean_checkout_bootstraps_and_verifies_authority(self) -> None:
        with tempfile.TemporaryDirectory(prefix="yuan-m8-clean-") as name:
            clone = pathlib.Path(name) / "repo"
            cloned = subprocess.run(
                ["git", "clone", "--quiet", "--no-hardlinks", str(ROOT), str(clone)],
                text=True,
                encoding="utf-8",
                capture_output=True,
                check=False,
            )
            self.assertEqual(0, cloned.returncode, cloned.stderr)
            for command in (
                [sys.executable, "-B", "scripts/yuan-authority.py", "verify"],
                [sys.executable, "-B", "scripts/pre-commit"],
            ):
                result = subprocess.run(
                    command,
                    cwd=clone,
                    text=True,
                    encoding="utf-8",
                    capture_output=True,
                    check=False,
                )
                self.assertEqual(0, result.returncode, result.stderr)


class FailClosedAuthorityBlockerTests(unittest.TestCase):
    def test_active_work_authorizes_and_scopes_remaining_m8_m9_work(self) -> None:
        work = json_file(next((ROOT / ".yuan-run/contracts").glob("*.json")))
        criteria = json.dumps(work["acceptance_criteria"], ensure_ascii=False).lower()
        allowed = work["scope"]["allowed_paths"]
        requirements = (
            ("M8 authority-switch AC", "authority" in criteria),
            ("M9 self-modification dogfood AC", "dogfood" in criteria or "self-mod" in criteria),
            ("M9 legacy tombstone AC", "tombstone" in criteria or "cleanup" in criteria),
            ("world-changing authorization grant", bool(work["authorization"]["grants"])),
            (
                ".yuan/authority write scope",
                any(path.startswith(".yuan/authority") for path in allowed),
            ),
            (".yuan-run write scope", any(path.startswith(".yuan-run") for path in allowed)),
            (
                "declared side effects",
                work["scope"]["side_effect_classes"] != ["none"],
            ),
        )
        for requirement, present in requirements:
            with self.subTest(requirement=requirement):
                self.assertTrue(present, f"active Work lacks {requirement}")

    def test_continue_result_has_a_legal_next_step(self) -> None:
        memory = json_file(ROOT / ".yuan-run/run-memory.json")
        if memory["last_result"] == "CONTINUE":
            self.assertTrue(
                memory["legal_next_steps"],
                "Core protocol permits CONTINUE only when a legal next step exists",
            )

    def test_core_activation_is_not_self_contradictory(self) -> None:
        protocol_path = ROOT / ".yuan/core/0.1/protocol.md"
        protocol = protocol_path.read_text(encoding="utf-8").lower()
        current = authority.load_current(ROOT)["record"]
        activation = current.get("protocol_activation", {})
        independently_bound = (
            activation.get("protocol_sha256") == digest(protocol_path)
            and activation.get("accepted_by_authority") == "legacy"
            and isinstance(activation.get("independent_evidence_sha256"), str)
            and len(activation["independent_evidence_sha256"]) == 64
        )
        self.assertTrue(
            "status: inert candidate" not in protocol or independently_bound,
            "active Core still declares itself inert and the authority record "
            "does not bind an older-root independent activation proof",
        )

    def test_core_precommit_rejects_every_legacy_state_and_spec_root(self) -> None:
        paths = (
            "docs/PROGRESS.md",
            "docs/work/TASK_BOARD.md",
            "docs/work/SESSION_LOG.md",
            "docs/events/events.jsonl",
            "contracts/tester.md",
            ".yuan/rules/iron-rules.md",
            ".yuan/specs/object-protocol.md",
        )
        for path in paths:
            with self.subTest(path=path):
                with self.assertRaises(precommit.GateError):
                    precommit.check_staged_paths("core", [path])

    def test_zero_check_provenance_receipt_is_rejected(self) -> None:
        fake = types.SimpleNamespace(
            returncode=0,
            stdout=json.dumps(
                {
                    "status": "PASS",
                    "registry_sha256": M7_HASH,
                    "semantic_records": 0,
                    "source_clauses": 0,
                    "unmapped": 0,
                }
            ),
        )
        with mock.patch.object(precommit.subprocess, "run", return_value=fake):
            with self.assertRaises(precommit.GateError):
                precommit._verify_provenance(ROOT)

    def test_core_has_a_legal_cas_path_to_reseal_after_new_evidence(self) -> None:
        manifest = ROOT / ".yuan-run/runtime-manifest.json"
        try:
            target = authority.assert_write_allowed(
                ROOT,
                "core",
                ".yuan-run/runtime-manifest.json",
                digest(manifest),
            )
        except authority.AuthorityError as error:
            self.fail(f"new immutable Evidence cannot be legally resealed: {error}")
        self.assertEqual(manifest, target)


if __name__ == "__main__":
    unittest.main()
