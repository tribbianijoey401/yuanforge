from __future__ import annotations

import hashlib
import pathlib
import shutil
import subprocess
import sys
import tempfile
import unittest


REPOSITORY_ROOT = pathlib.Path(__file__).resolve().parents[2]
VERIFIER = REPOSITORY_ROOT / "scripts" / "bootstrap-core-verifier.py"
VISIBLE_SUITE = pathlib.Path(__file__).parent / "fixtures" / "author-visible"


def sha256(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class BootstrapReceiptIsolationTests(unittest.TestCase):
    def test_untrusted_manifest_cannot_write_receipt_inside_suite_root(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            suite = pathlib.Path(temporary) / "suite"
            shutil.copytree(VISIBLE_SUITE, suite)
            manifest = suite / "manifest.json"
            frozen_hash = sha256(manifest)
            candidate = suite / "candidates" / "valid" / "protocol.md"
            original_candidate = candidate.read_bytes()
            with manifest.open("a", encoding="utf-8", newline="\n") as stream:
                stream.write(" \n")

            result = subprocess.run(
                [
                    sys.executable,
                    str(VERIFIER),
                    "--manifest",
                    str(manifest),
                    "--manifest-sha256",
                    frozen_hash,
                    "--receipt",
                    str(candidate),
                ],
                cwd=REPOSITORY_ROOT,
                text=True,
                encoding="utf-8",
                capture_output=True,
                timeout=15,
                check=False,
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(candidate.read_bytes(), original_candidate)
            self.assertIn("RECEIPT_PATH_CONFLICT", result.stdout)


if __name__ == "__main__":
    unittest.main()
