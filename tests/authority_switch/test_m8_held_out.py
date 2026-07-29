"""Independent M8 held-out tests for the Yuan runtime authority switch."""

from __future__ import annotations

import copy
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
runtime_state = load_module("m8_held_out_runtime", SCRIPTS / "yuan_runtime_state.py")
transaction = load_module(
    "m8_held_out_transaction", SCRIPTS / "yuan_runtime_transaction.py"
)
provenance_history = load_module(
    "m8_held_out_provenance_history", SCRIPTS / "yuan_provenance_history.py"
)


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
        self.assertEqual([1, 2, 3, 4, 5], [item["revision"] for item in history])
        self.assertEqual(
            ["legacy", "core", "legacy", "core", "core"],
            [item["authority"] for item in history],
        )
        self.assertEqual(
            [None, "legacy", "core", "legacy", "core"],
            [item["receipt"]["from"] for item in history],
        )
        self.assertEqual(
            ["legacy", "core", "legacy", "core", "core"],
            [item["receipt"]["to"] for item in history],
        )
        self.assertEqual(
            [
                "41013c2695358479daf8e9756af2654dc867cbf407980f9bc4ff45a84dccf147",
                "55c5a0134ccafd73895619cb0278f618129e2fd81f2e79a5a2ed66c2534953a4",
                "6cceb906f2770460aabe66a83857d79173ec996bd7efe81e8a1d91a30193aa83",
                "9f5b3de9f561fe1ecc16405a7c21dcd24824e1b4735572928cc47aff468b8183",
            ],
            [digest_bytes(authority.canonical(item)) for item in history[:4]],
        )
        self.assertEqual(
            history[3]["previous_record_sha256"],
            "6cceb906f2770460aabe66a83857d79173ec996bd7efe81e8a1d91a30193aa83",
        )
        self.assertEqual(
            history[4]["previous_record_sha256"],
            "9f5b3de9f561fe1ecc16405a7c21dcd24824e1b4735572928cc47aff468b8183",
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
            runtime, _, _ = runtime_state.resolve_runtime_root(repo)
            runtime_before = digest(runtime / "runtime-manifest.json")
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
            runtime, _, _ = runtime_state.resolve_runtime_root(repo)
            self.assertEqual(runtime_before, digest(runtime / "runtime-manifest.json"))
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
        legacy_runtime = ROOT / ".yuan-run"
        contracts = list((legacy_runtime / "contracts").glob("*.json"))
        attempts = list((legacy_runtime / "attempts").glob("*.json"))
        evidence = list((legacy_runtime / "evidence").glob("*.json"))
        self.assertEqual((1, 37, 37), (len(contracts), len(attempts), len(evidence)))
        archive = json_file(
            ROOT
            / ".yuan/authority/runtime-archive"
            / "a803caf92d9db6b74b67ac8ebd7e4cb76b773a46b267d07406a8298d37891fc4"
            / "index.json"
        )
        expected_paths = {
            path.relative_to(legacy_runtime).as_posix()
            for area in ("contracts", "attempts", "evidence")
            for path in (legacy_runtime / area).glob("*.json")
        } | {"run-memory.json", "runtime-manifest.json"}
        self.assertEqual(expected_paths, {item["path"] for item in archive["files"]})
        for item in archive["files"]:
            self.assertEqual(item["sha256"], digest(legacy_runtime / item["path"]))
        with tempfile.TemporaryDirectory(prefix="yuan-r1-legacy-rebuild-") as name:
            historical = pathlib.Path(name)
            shutil.copytree(ROOT / ".yuan/core", historical / ".yuan/core")
            for area in ("contracts", "attempts", "evidence"):
                shutil.copytree(legacy_runtime / area, historical / ".yuan-run" / area)
            shutil.copyfile(
                legacy_runtime / "run-memory.json",
                historical / ".yuan-run/run-memory.json",
            )
            delta = json_file(
                ROOT / ".yuan/authority/core-history/m7-to-m8/index.json"
            )
            for item in delta["entries"]:
                shutil.copyfile(ROOT / item["retained_blob"], historical / item["path"])
            rebuilt = authority.canonical(
                authority.rebuild_runtime_memory(
                    historical, historical / ".yuan-run"
                )
            )
            self.assertEqual(
                (legacy_runtime / "run-memory.json").read_bytes(),
                rebuilt,
                "legacy Memory must rebuild with its retained Core revision",
            )

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

    def test_frozen_m7_registry_and_nine_delta_assertions_replay(self) -> None:
        receipt = provenance_history.verify_frozen_and_delta(ROOT)
        self.assertEqual("PASS", receipt["status"])
        self.assertEqual((2227, 2207, 0), (
            receipt["semantic_records"],
            receipt["source_clauses"],
            receipt["unmapped"],
        ))
        self.assertEqual(9, receipt["delta_assertions"])
        self.assertEqual(
            "a888fdd3eb35d06fdc6ca926b37bc8dfbccddc39",
            receipt["baseline_commit"],
        )


class FailClosedAuthorityBlockerTests(unittest.TestCase):
    def test_active_work_authorizes_and_scopes_remaining_m8_m9_work(self) -> None:
        runtime, _, _ = runtime_state.resolve_runtime_root(ROOT)
        work = json_file(next((runtime / "contracts").glob("*.json")))
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
        for criterion in work["acceptance_criteria"]:
            binding = criterion["verifier_binding"]
            with self.subTest(ac_id=criterion["id"], property="verifier-binding"):
                self.assertEqual(
                    {"id", "revision", "sha256", "trust_root_id"},
                    {"id", "revision", "sha256", "trust_root_id"} & set(binding),
                )
                self.assertRegex(binding["sha256"], r"^[0-9a-f]{64}$")
                self.assertGreater(binding["minimum_assertions"], 0)
                self.assertTrue(binding["environment_ids"])
                self.assertEqual(
                    set(binding["environment_ids"]),
                    set(binding["environment_fingerprints"]),
                )
        self.assertTrue(all(value > 0 for value in work["budget"].values()))
        self.assertFalse(
            any(
                "docs" in grant["scopes"]
                for grant in work["authorization"]["grants"]
            ),
            "tombstone scope must not be pre-authorized",
        )

    def test_continue_result_has_a_legal_next_step(self) -> None:
        runtime, _, _ = runtime_state.resolve_runtime_root(ROOT)
        memory = json_file(runtime / "run-memory.json")
        if memory["last_result"] == "CONTINUE":
            self.assertTrue(
                memory["legal_next_steps"],
                "Core protocol permits CONTINUE only when a legal next step exists",
            )
            self.assertEqual(
                "AC-M9-SELF-MODIFICATION-DOGFOOD",
                memory["legal_next_steps"][0]["ac_id"],
            )
        work = json_file(next((runtime / "contracts").glob("*.json")))
        tombstone = next(
            item
            for item in work["acceptance_criteria"]
            if "TOMBSTONE" in item["id"]
        )
        self.assertEqual("human-judgment", tombstone["type"])
        self.assertFalse(
            any(
                tombstone["artifact_scope"] in grant["scopes"]
                for grant in work["authorization"]["grants"]
            ),
            "tombstone must remain WAIT_AUTH without a human grant",
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
        descriptor = json_file(
            ROOT / ".yuan/authority/activation/yuan-core-0.1.json"
        )
        old_root_manifest = (
            ROOT / ".yuan/authority/activation/evidence/old-root-manifest.json"
        )
        required_bindings = (
            (
                "previous candidate manifest",
                descriptor.get("previous_candidate_manifest_sha256")
                == "20ac1cbb7f2377d5cecadf3347a40d81e14e8469c6c914701f585a49903d9768",
            ),
            (
                "activated candidate manifest",
                descriptor.get("candidate_manifest_sha256")
                == digest(ROOT / ".yuan/core/0.1/candidate-manifest.json"),
            ),
            (
                "old-root suite manifest",
                descriptor.get("older_root_manifest_sha256")
                == digest(old_root_manifest),
            ),
            (
                "protocol",
                descriptor.get("protocol_sha256") == digest(protocol_path),
            ),
        )
        for binding, present in required_bindings:
            with self.subTest(binding=binding):
                self.assertTrue(present, f"activation descriptor does not bind {binding}")

    def test_core_precommit_rejects_every_legacy_state_and_spec_root(self) -> None:
        paths = (
            "docs/PROGRESS.md",
            "docs/work/TASK_BOARD.md",
            "docs/work/SESSION_LOG.md",
            "docs/events/events.jsonl",
            "contracts/tester.md",
            ".yuan/rules/iron-rules.md",
            ".yuan/specs/object-protocol.md",
            ".yuan/docs/TASK_BOARD.schema.md",
            ".yuan/platforms/codex.md",
            ".yuan/skills/role-switch/SKILL.md",
            "protocols/state-machine.md",
            "templates/role-contract.md",
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
        runtime, pointer, active_sha = runtime_state.resolve_runtime_root(ROOT)
        self.assertIsNotNone(pointer)
        self.assertIsNotNone(active_sha)
        with self.assertRaisesRegex(authority.AuthorityError, "transaction"):
            authority.assert_write_allowed(
                ROOT,
                "core",
                (runtime / "evidence/0002.json").relative_to(ROOT),
                None,
            )
        self.assertTrue(callable(transaction.append_runtime_transaction))
        self.assertTrue(callable(transaction.recover_runtime_transaction))


class R1AdversarialBindingTests(unittest.TestCase):
    def copy_runtime_repo(self, target: pathlib.Path) -> None:
        for relative in (".yuan", ".yuan-run", "scripts"):
            shutil.copytree(ROOT / relative, target / relative)

    def test_authority_rejects_tampered_activated_core_and_old_root_manifest(self) -> None:
        targets = (
            ".yuan/core/0.1/runtime_replay.py",
            ".yuan/authority/activation/evidence/old-root-manifest.json",
        )
        for relative in targets:
            with self.subTest(relative=relative):
                with tempfile.TemporaryDirectory(prefix="yuan-r1-activation-") as name:
                    repo = pathlib.Path(name)
                    self.copy_runtime_repo(repo)
                    path = repo / relative
                    path.write_bytes(path.read_bytes() + b"\n")
                    with self.assertRaises(authority.AuthorityError):
                        authority.verify_authority(repo)

    def test_untrusted_m9_evidence_cannot_advance_to_tombstone(self) -> None:
        with tempfile.TemporaryDirectory(prefix="yuan-r1-untrusted-") as name:
            repo = pathlib.Path(name)
            self.copy_runtime_repo(repo)
            runtime, _, active_before = runtime_state.resolve_runtime_root(repo)
            work = json_file(next((runtime / "contracts").glob("*.json")))
            previous_attempt = json_file(next((runtime / "attempts").glob("*.json")))
            previous_evidence = json_file(next((runtime / "evidence").glob("*.json")))
            attempt = copy.deepcopy(previous_attempt)
            attempt.update(
                {
                    "attempt_id": "ATT-UNTRUSTED-M9-0002",
                    "sequence": 2,
                    "evidence_ids": ["EVD-UNTRUSTED-M9-0002"],
                }
            )
            attempt["action"].update(
                {
                    "type": "verify",
                    "mutating": False,
                    "side_effect_class": "none",
                    "scope": ".yuan/core/0.1",
                    "authorization_grant_id": "GRANT-CORE-M8-M9",
                }
            )
            evidence = copy.deepcopy(previous_evidence)
            evidence.update(
                {
                    "evidence_id": "EVD-UNTRUSTED-M9-0002",
                    "sequence": 2,
                    "source_attempt_id": attempt["attempt_id"],
                    "ac_id": "AC-M9-SELF-MODIFICATION-DOGFOOD",
                    "kind": "integration",
                }
            )
            self.assertNotEqual(
                evidence["verifier_binding"],
                next(
                    item["verifier_binding"]
                    for item in work["acceptance_criteria"]
                    if item["id"] == evidence["ac_id"]
                ),
            )
            evidence["immutable_digest"] = transaction.canonical_digest(
                evidence, omitted_paths=(("immutable_digest",),)
            )
            authority_before = digest(repo / ".yuan/authority/current")
            transaction.append_runtime_transaction(
                repo,
                attempt,
                evidence,
                expected_authority_pointer_sha256=authority_before,
                expected_active_run_pointer_sha256=active_before,
            )
            active_runtime, _, _ = runtime_state.resolve_runtime_root(repo)
            memory = json_file(active_runtime / "run-memory.json")
            self.assertEqual(
                "CONTINUE",
                memory["last_result"],
                "untrusted Evidence must not advance the M9 AC",
            )
            self.assertEqual(
                "AC-M9-SELF-MODIFICATION-DOGFOOD",
                memory["legal_next_steps"][0]["ac_id"],
            )


if __name__ == "__main__":
    unittest.main()
