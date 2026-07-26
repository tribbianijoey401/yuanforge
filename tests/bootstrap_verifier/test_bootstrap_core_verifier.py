from __future__ import annotations

import hashlib
import json
import pathlib
import shutil
import subprocess
import sys
import tempfile
import unittest


REPOSITORY_ROOT = pathlib.Path(__file__).resolve().parents[2]
VERIFIER = REPOSITORY_ROOT / "scripts" / "bootstrap-core-verifier.py"
VISIBLE_SUITE = (
    pathlib.Path(__file__).parent / "fixtures" / "author-visible"
)


def sha256(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class BootstrapCoreVerifierCliTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.suite = pathlib.Path(self.temp_dir.name) / "suite"
        shutil.copytree(VISIBLE_SUITE, self.suite)
        self.manifest = self.suite / "manifest.json"
        self.receipt = pathlib.Path(self.temp_dir.name) / "receipt.json"

    def run_verifier(
        self,
        *,
        manifest_hash: str | None = None,
        manifest: pathlib.Path | None = None,
    ) -> subprocess.CompletedProcess[str]:
        selected_manifest = manifest or self.manifest
        return subprocess.run(
            [
                sys.executable,
                str(VERIFIER),
                "--manifest",
                str(selected_manifest),
                "--manifest-sha256",
                manifest_hash or sha256(selected_manifest),
                "--receipt",
                str(self.receipt),
            ],
            cwd=REPOSITORY_ROOT,
            text=True,
            encoding="utf-8",
            capture_output=True,
            timeout=15,
            check=False,
        )

    def test_author_visible_suite_exercises_all_required_rejections(self) -> None:
        result = self.run_verifier()

        self.assertEqual(result.returncode, 0, result.stderr or result.stdout)
        receipt = json.loads(self.receipt.read_text(encoding="utf-8"))
        self.assertEqual(receipt["status"], "PASS")
        observed = {
            case["negative_class"]: set(case["reason_codes"])
            for case in receipt["cases"]
            if case["negative_class"] is not None
        }
        self.assertIn("EMPTY_CANDIDATE", observed["empty_candidate"])
        self.assertIn("CHECK_FAILED", observed["known_bad"])
        self.assertIn("ZERO_ASSERTIONS", observed["zero_assertions"])
        self.assertIn("VALIDATOR_ERROR", observed["validator_error"])
        self.assertIn("RESULT_PARSE_ERROR", observed["parse_error"])
        self.assertGreater(receipt["checks_executed"], 0)

    def test_candidate_tamper_fails_closed_with_hash_mismatch(self) -> None:
        target = self.suite / "candidates" / "valid" / "protocol.md"
        target.write_text("tampered", encoding="utf-8")

        result = self.run_verifier()

        self.assertNotEqual(result.returncode, 0)
        receipt = json.loads(self.receipt.read_text(encoding="utf-8"))
        valid_case = next(
            case for case in receipt["cases"] if case["id"] == "valid"
        )
        self.assertIn("HASH_MISMATCH", valid_case["reason_codes"])
        self.assertEqual(receipt["status"], "FAIL")

    def test_untrusted_manifest_hash_is_rejected_with_receipt(self) -> None:
        result = self.run_verifier(manifest_hash="0" * 64)

        self.assertNotEqual(result.returncode, 0)
        receipt = json.loads(self.receipt.read_text(encoding="utf-8"))
        self.assertEqual(receipt["status"], "FAIL")
        self.assertIn("MANIFEST_HASH_MISMATCH", receipt["reason_codes"])

    def test_malformed_manifest_is_rejected_with_receipt(self) -> None:
        malformed = self.suite / "malformed.json"
        malformed.write_text("{not-json", encoding="utf-8")

        result = self.run_verifier(
            manifest=malformed,
            manifest_hash=sha256(malformed),
        )

        self.assertNotEqual(result.returncode, 0)
        receipt = json.loads(self.receipt.read_text(encoding="utf-8"))
        self.assertEqual(receipt["status"], "FAIL")
        self.assertIn("MANIFEST_PARSE_ERROR", receipt["reason_codes"])

    def test_unexpected_validator_error_returns_nonzero(self) -> None:
        data = json.loads(self.manifest.read_text(encoding="utf-8"))
        valid_case = next(case for case in data["cases"] if case["id"] == "valid")
        valid_case["validator"] = {
            "command": [
                "{python}",
                "validators/error_validator.py",
                "{candidate}",
            ],
            "timeout_seconds": 5,
            "trusted_files": [
                {
                    "path": "validators/error_validator.py",
                    "sha256": sha256(
                        self.suite / "validators" / "error_validator.py"
                    ),
                }
            ],
        }
        self.manifest.write_text(
            json.dumps(data, indent=2) + "\n",
            encoding="utf-8",
        )

        result = self.run_verifier()

        self.assertNotEqual(result.returncode, 0)
        receipt = json.loads(self.receipt.read_text(encoding="utf-8"))
        self.assertEqual(receipt["status"], "FAIL")
        valid_receipt = next(
            case for case in receipt["cases"] if case["id"] == "valid"
        )
        self.assertIn("VALIDATOR_ERROR", valid_receipt["reason_codes"])

    def test_unexpected_validator_timeout_returns_nonzero(self) -> None:
        data = json.loads(self.manifest.read_text(encoding="utf-8"))
        valid_case = next(case for case in data["cases"] if case["id"] == "valid")
        valid_case["validator"] = {
            "command": [
                "{python}",
                "validators/slow_validator.py",
                "{candidate}",
            ],
            "timeout_seconds": 0.05,
            "trusted_files": [
                {
                    "path": "validators/slow_validator.py",
                    "sha256": sha256(
                        self.suite / "validators" / "slow_validator.py"
                    ),
                }
            ],
        }
        self.manifest.write_text(
            json.dumps(data, indent=2) + "\n",
            encoding="utf-8",
        )

        result = self.run_verifier()

        self.assertNotEqual(result.returncode, 0)
        receipt = json.loads(self.receipt.read_text(encoding="utf-8"))
        valid_receipt = next(
            case for case in receipt["cases"] if case["id"] == "valid"
        )
        self.assertIn("VALIDATOR_TIMEOUT", valid_receipt["reason_codes"])

    def test_manifest_path_traversal_is_rejected_before_execution(self) -> None:
        data = json.loads(self.manifest.read_text(encoding="utf-8"))
        valid_case = next(case for case in data["cases"] if case["id"] == "valid")
        valid_case["candidate"] = "../../outside-suite"
        self.manifest.write_text(
            json.dumps(data, indent=2) + "\n",
            encoding="utf-8",
        )

        result = self.run_verifier()

        self.assertNotEqual(result.returncode, 0)
        receipt = json.loads(self.receipt.read_text(encoding="utf-8"))
        self.assertIn("MANIFEST_SCHEMA_ERROR", receipt["reason_codes"])

    def test_missing_required_negative_class_is_rejected(self) -> None:
        data = json.loads(self.manifest.read_text(encoding="utf-8"))
        data["cases"] = [
            case for case in data["cases"] if case["negative_class"] != "parse_error"
        ]
        self.manifest.write_text(
            json.dumps(data, indent=2) + "\n",
            encoding="utf-8",
        )

        result = self.run_verifier()

        self.assertNotEqual(result.returncode, 0)
        receipt = json.loads(self.receipt.read_text(encoding="utf-8"))
        self.assertIn("MANIFEST_SCHEMA_ERROR", receipt["reason_codes"])

    def test_help_is_available_without_loading_a_manifest(self) -> None:
        result = subprocess.run(
            [sys.executable, str(VERIFIER), "--help"],
            cwd=REPOSITORY_ROOT,
            text=True,
            encoding="utf-8",
            capture_output=True,
            timeout=10,
            check=False,
        )

        self.assertEqual(result.returncode, 0)
        self.assertIn("--manifest", result.stdout)


if __name__ == "__main__":
    unittest.main()
