from __future__ import annotations

import hashlib
import json
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime, timezone


REPOSITORY_ROOT = pathlib.Path(__file__).resolve().parents[2]
VERIFIER = REPOSITORY_ROOT / "scripts" / "bootstrap-core-verifier.py"
VISIBLE_SUITE = pathlib.Path(__file__).parent / "fixtures" / "author-visible"


def sha256(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class BootstrapCoreVerifierHeldOutTests(unittest.TestCase):
    """Independent adversarial cases not available to the task-003 implementer."""

    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.root = pathlib.Path(self.temp_dir.name)
        self.suite = self.root / "suite"
        shutil.copytree(VISIBLE_SUITE, self.suite)
        self.manifest = self.suite / "manifest.json"
        self.receipt = self.root / "receipt.json"

    def read_manifest(self) -> dict:
        return json.loads(self.manifest.read_text(encoding="utf-8"))

    def write_manifest(self, value: dict) -> None:
        self.manifest.write_text(
            json.dumps(value, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
            newline="\n",
        )

    def run_verifier(
        self,
        *,
        manifest_hash: str | None = None,
        receipt: pathlib.Path | None = None,
    ) -> subprocess.CompletedProcess[str]:
        selected_receipt = receipt or self.receipt
        return subprocess.run(
            [
                sys.executable,
                str(VERIFIER),
                "--manifest",
                str(self.manifest),
                "--manifest-sha256",
                manifest_hash or sha256(self.manifest),
                "--receipt",
                str(selected_receipt),
            ],
            cwd=REPOSITORY_ROOT,
            text=True,
            encoding="utf-8",
            errors="strict",
            capture_output=True,
            timeout=15,
            check=False,
        )

    def valid_case(self, manifest: dict) -> dict:
        return next(case for case in manifest["cases"] if case["id"] == "valid")

    def test_baseline_receipt_has_complete_bound_fields(self) -> None:
        result = self.run_verifier()

        self.assertEqual(result.returncode, 0, result.stderr or result.stdout)
        receipt = json.loads(self.receipt.read_text(encoding="utf-8"))
        self.assertEqual(receipt["schema_version"], "yuan.bootstrap-receipt/v1")
        self.assertEqual(receipt["verifier_revision"], "yuan.bootstrap-verifier/1")
        self.assertEqual(receipt["manifest_sha256"], sha256(self.manifest))
        self.assertEqual(receipt["status"], "PASS")
        self.assertEqual(receipt["reason_codes"], [])
        self.assertGreater(receipt["checks_executed"], 0)
        self.assertTrue(receipt["cases"])
        created_at = datetime.fromisoformat(receipt["created_at"])
        self.assertIsNotNone(created_at.tzinfo)
        self.assertEqual(created_at.utcoffset(), timezone.utc.utcoffset(created_at))
        observed_negative = {
            case["negative_class"]: case["reason_codes"]
            for case in receipt["cases"]
            if case["negative_class"] is not None
        }
        self.assertEqual(
            observed_negative,
            {
                "empty_candidate": ["EMPTY_CANDIDATE"],
                "known_bad": ["CHECK_FAILED"],
                "zero_assertions": ["ZERO_ASSERTIONS"],
                "validator_error": ["VALIDATOR_ERROR"],
                "parse_error": ["RESULT_PARSE_ERROR"],
            },
        )
        for case in receipt["cases"]:
            self.assertIn(case["observed"], {"ACCEPT", "REJECT"})
            self.assertIsInstance(case["matched"], bool)
            self.assertIn("candidate_sha256", case)
            self.assertIn("validator", case)
            self.assertIn("assertions", case["validator"])
            self.assertIn("exit_code", case["validator"])

    def test_candidate_and_validator_tamper_are_not_reason_clean(self) -> None:
        candidate = self.suite / "candidates" / "known-bad" / "protocol.md"
        candidate.write_text("tampered", encoding="utf-8")
        validator = self.suite / "validators" / "pass_validator.py"
        validator.write_text("print('tampered')", encoding="utf-8")

        result = self.run_verifier()

        self.assertNotEqual(result.returncode, 0)
        receipt = json.loads(self.receipt.read_text(encoding="utf-8"))
        self.assertEqual(receipt["status"], "FAIL")
        cases = {case["id"]: case for case in receipt["cases"]}
        self.assertIn("HASH_MISMATCH", cases["known-bad"]["reason_codes"])
        self.assertIn("UNTRUSTED_VALIDATOR", cases["valid"]["reason_codes"])
        self.assertFalse(cases["known-bad"]["matched"])
        self.assertFalse(cases["valid"]["matched"])

    def test_manifest_tamper_is_rejected_before_suite_execution(self) -> None:
        frozen_hash = sha256(self.manifest)
        with self.manifest.open("a", encoding="utf-8", newline="\n") as stream:
            stream.write(" \n")

        result = self.run_verifier(manifest_hash=frozen_hash)

        self.assertNotEqual(result.returncode, 0)
        receipt = json.loads(self.receipt.read_text(encoding="utf-8"))
        self.assertEqual(receipt["status"], "FAIL")
        self.assertEqual(receipt["reason_codes"], ["MANIFEST_HASH_MISMATCH"])
        self.assertEqual(receipt["cases"], [])
        self.assertEqual(receipt["checks_executed"], 0)

    def test_timeout_and_parse_error_remain_distinct_fail_closed_results(self) -> None:
        manifest = self.read_manifest()
        case = self.valid_case(manifest)
        case["validator"] = {
            "command": ["{python}", "validators/slow_validator.py"],
            "timeout_seconds": 0.02,
            "trusted_files": [
                {
                    "path": "validators/slow_validator.py",
                    "sha256": sha256(self.suite / "validators" / "slow_validator.py"),
                }
            ],
        }
        self.write_manifest(manifest)

        result = self.run_verifier()

        self.assertNotEqual(result.returncode, 0)
        receipt = json.loads(self.receipt.read_text(encoding="utf-8"))
        valid = next(case for case in receipt["cases"] if case["id"] == "valid")
        self.assertEqual(valid["reason_codes"], ["VALIDATOR_TIMEOUT"])
        self.assertEqual(valid["validator"]["assertions"], 0)
        self.assertIsNone(valid["validator"]["exit_code"])

    def test_missing_negative_class_fails_even_when_remaining_cases_match(self) -> None:
        manifest = self.read_manifest()
        manifest["cases"] = [
            case
            for case in manifest["cases"]
            if case.get("negative_class") != "known_bad"
        ]
        self.write_manifest(manifest)

        result = self.run_verifier()

        self.assertNotEqual(result.returncode, 0)
        receipt = json.loads(self.receipt.read_text(encoding="utf-8"))
        self.assertEqual(receipt["status"], "FAIL")
        self.assertIn("MANIFEST_SCHEMA_ERROR", receipt["reason_codes"])
        self.assertIn("known_bad", receipt["error"])

    def test_expected_reason_is_not_allowed_to_hide_extra_faults(self) -> None:
        target = self.suite / "candidates" / "known-bad" / "protocol.md"
        target.write_text("KNOWN_BAD plus unbound tamper", encoding="utf-8")

        result = self.run_verifier()

        self.assertNotEqual(result.returncode, 0)
        receipt = json.loads(self.receipt.read_text(encoding="utf-8"))
        case = next(case for case in receipt["cases"] if case["id"] == "known-bad")
        self.assertEqual(case["reason_codes"], ["HASH_MISMATCH"])
        self.assertFalse(case["matched"])

    def test_utf8_manifest_candidate_and_receipt_round_trip(self) -> None:
        manifest = self.read_manifest()
        manifest["suite_id"] = "留出集-验证"
        case = self.valid_case(manifest)
        case["id"] = "有效候选"
        candidate = self.suite / "candidates" / "valid"
        unicode_file = candidate / "说明.md"
        unicode_file.write_text("证据必须失败关闭。\n", encoding="utf-8", newline="\n")
        case["required_files"].append(
            {"path": "说明.md", "sha256": sha256(unicode_file)}
        )
        self.write_manifest(manifest)

        result = self.run_verifier()

        self.assertEqual(result.returncode, 0, result.stderr or result.stdout)
        raw = self.receipt.read_text(encoding="utf-8")
        self.assertIn("留出集-验证", raw)
        self.assertIn("有效候选", raw)
        receipt = json.loads(raw)
        self.assertEqual(receipt["suite_id"], "留出集-验证")

    def test_nested_receipt_is_atomic_and_leaves_no_temporary_file(self) -> None:
        receipt = self.root / "nested" / "evidence" / "receipt.json"

        result = self.run_verifier(receipt=receipt)

        self.assertEqual(result.returncode, 0, result.stderr or result.stdout)
        self.assertEqual(json.loads(receipt.read_text(encoding="utf-8"))["status"], "PASS")
        self.assertEqual(list(receipt.parent.glob(".receipt.json.*.tmp")), [])

    def test_receipt_in_prefix_similar_sibling_of_suite_root_is_allowed(self) -> None:
        receipt = self.root / "suite-sibling" / "receipt.json"

        result = self.run_verifier(receipt=receipt)

        self.assertEqual(result.returncode, 0, result.stderr or result.stdout)
        self.assertEqual(json.loads(receipt.read_text(encoding="utf-8"))["status"], "PASS")

    def test_atomic_receipt_parent_file_failure_preserves_existing_path(self) -> None:
        parent_file = self.root / "not-a-directory"
        parent_file.write_text("keep-me", encoding="utf-8")
        receipt = parent_file / "receipt.json"

        result = self.run_verifier(receipt=receipt)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("unable to write receipt", result.stderr)
        self.assertEqual(parent_file.read_text(encoding="utf-8"), "keep-me")
        self.assertFalse(receipt.exists())

    def test_junction_or_symlink_cannot_escape_validator_trust_root(self) -> None:
        outside = self.root / "outside-validator"
        outside.mkdir()
        marker = self.root / "executed.marker"
        validator = outside / "escape.py"
        validator.write_text(
            "import json, pathlib, sys\n"
            f"pathlib.Path({str(marker)!r}).write_text('executed')\n"
            "print(json.dumps({"
            "'schema_version':'yuan.validator-result/v1',"
            "'status':'PASS','assertions':1,"
            "'checks':[{'id':'escape','status':'PASS'}]}))\n",
            encoding="utf-8",
            newline="\n",
        )
        link = self.suite / "validators-link"
        if os.name == "nt":
            created = subprocess.run(
                ["cmd", "/c", "mklink", "/J", str(link), str(outside)],
                capture_output=True,
                check=False,
            )
            self.assertEqual(created.returncode, 0, created.stderr)
            self.addCleanup(lambda: os.rmdir(link) if link.exists() else None)
        else:
            link.symlink_to(outside, target_is_directory=True)
            self.addCleanup(lambda: link.unlink(missing_ok=True))

        manifest = self.read_manifest()
        case = self.valid_case(manifest)
        case["validator"] = {
            "command": [
                "{python}",
                "validators-link/escape.py",
                "{candidate}",
            ],
            "timeout_seconds": 5,
            "trusted_files": [
                {
                    "path": "validators-link/escape.py",
                    "sha256": sha256(validator),
                }
            ],
        }
        self.write_manifest(manifest)

        result = self.run_verifier()

        self.assertNotEqual(result.returncode, 0)
        receipt = json.loads(self.receipt.read_text(encoding="utf-8"))
        self.assertEqual(receipt["status"], "FAIL")
        self.assertIn("MANIFEST_SCHEMA_ERROR", receipt["reason_codes"])
        self.assertFalse(marker.exists(), "escaped validator was executed")

    def test_unbound_validator_command_path_traversal_must_be_rejected(self) -> None:
        """A decorative trusted_files hash must not authorize another program."""
        outside = self.root / "outside_validator.py"
        outside.write_text(
            "import json\n"
            "print(json.dumps({"
            "'schema_version':'yuan.validator-result/v1',"
            "'status':'PASS','assertions':1,"
            "'checks':[{'id':'outside','status':'PASS'}]}))\n",
            encoding="utf-8",
            newline="\n",
        )
        manifest = self.read_manifest()
        case = self.valid_case(manifest)
        case["validator"]["command"] = [
            "{python}",
            "../outside_validator.py",
            "{candidate}",
        ]
        # The declared trusted file is intentionally left unchanged and unrelated.
        self.write_manifest(manifest)

        result = self.run_verifier()

        self.assertNotEqual(
            result.returncode,
            0,
            "verifier executed an out-of-root validator not bound by trusted_files",
        )
        receipt = json.loads(self.receipt.read_text(encoding="utf-8"))
        self.assertEqual(receipt["status"], "FAIL")

    def test_receipt_must_not_overwrite_a_verified_candidate(self) -> None:
        """A PASS receipt cannot be written on top of the artifact it just proved."""
        candidate = self.suite / "candidates" / "valid" / "protocol.md"
        original = candidate.read_bytes()

        result = self.run_verifier(receipt=candidate)

        self.assertNotEqual(
            result.returncode,
            0,
            "verifier returned PASS while using a verified candidate as receipt path",
        )
        self.assertEqual(candidate.read_bytes(), original)

    def test_receipt_must_not_be_created_inside_candidate_tree(self) -> None:
        """Creating a new receipt inside a candidate also makes evidence stale."""
        receipt = self.suite / "candidates" / "valid" / "receipt.json"

        result = self.run_verifier(receipt=receipt)

        self.assertNotEqual(
            result.returncode,
            0,
            "verifier returned PASS then added an unbound file to the candidate tree",
        )
        self.assertFalse(receipt.exists())

    def test_receipt_must_not_overwrite_manifest_or_validator(self) -> None:
        for target in (
            self.manifest,
            self.suite / "validators" / "pass_validator.py",
        ):
            with self.subTest(target=target.name):
                original = target.read_bytes()

                result = self.run_verifier(receipt=target)

                self.assertNotEqual(result.returncode, 0)
                self.assertEqual(target.read_bytes(), original)

    def test_receipt_collision_protection_cannot_depend_on_manifest_hash(self) -> None:
        """Rejecting an untrusted manifest must still leave suite inputs untouched."""
        frozen_hash = sha256(self.manifest)
        candidate = self.suite / "candidates" / "valid" / "protocol.md"
        original_candidate = candidate.read_bytes()
        with self.manifest.open("a", encoding="utf-8", newline="\n") as stream:
            stream.write(" \n")

        result = self.run_verifier(
            manifest_hash=frozen_hash,
            receipt=candidate,
        )

        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(
            candidate.read_bytes(),
            original_candidate,
            "FAIL receipt overwrote a suite input before manifest trust was established",
        )

    def test_duplicate_check_ids_are_not_distinct_assertions(self) -> None:
        validator = self.suite / "validators" / "duplicate_checks.py"
        validator.write_text(
            "import json\n"
            "print(json.dumps({"
            "'schema_version':'yuan.validator-result/v1',"
            "'status':'PASS','assertions':2,"
            "'checks':["
            "{'id':'same-check','status':'PASS'},"
            "{'id':'same-check','status':'PASS'}]}))\n",
            encoding="utf-8",
            newline="\n",
        )
        manifest = self.read_manifest()
        case = self.valid_case(manifest)
        case["validator"] = {
            "command": ["{python}", "validators/duplicate_checks.py", "{candidate}"],
            "timeout_seconds": 5,
            "trusted_files": [
                {
                    "path": "validators/duplicate_checks.py",
                    "sha256": sha256(validator),
                }
            ],
        }
        self.write_manifest(manifest)

        result = self.run_verifier()

        self.assertNotEqual(
            result.returncode,
            0,
            "duplicate check ids were counted as independent assertions",
        )
        receipt = json.loads(self.receipt.read_text(encoding="utf-8"))
        self.assertEqual(receipt["status"], "FAIL")


if __name__ == "__main__":
    unittest.main()
