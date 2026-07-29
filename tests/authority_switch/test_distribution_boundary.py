"""Distribution boundary tests for the Core initializer."""

from __future__ import annotations

import pathlib
import subprocess
import sys
import tempfile
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[2]
INIT = ROOT / "bin" / "yuanforge-init"


class DistributionBoundaryTests(unittest.TestCase):
    def run_init(self, target: pathlib.Path, *extra: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, "-B", str(INIT), str(target), *extra],
            cwd=ROOT,
            text=True,
            encoding="utf-8",
            capture_output=True,
            check=False,
        )

    def test_default_copies_only_bootstrap_core_and_adapters(self) -> None:
        with tempfile.TemporaryDirectory(prefix="yuan-m8-dist-") as name:
            target = pathlib.Path(name) / "project"
            result = self.run_init(target)
            self.assertEqual(0, result.returncode, result.stderr)
            self.assertEqual(
                (ROOT / ".yuan/VERSION").read_bytes(),
                (target / ".yuan/VERSION").read_bytes(),
            )
            self.assertTrue((target / "AGENTS.md").is_file())
            self.assertTrue((target / ".yuan/core").is_dir())
            self.assertTrue((target / ".yuan/adapters").is_dir())
            self.assertFalse((target / ".yuan/rules").exists())
            self.assertFalse((target / ".yuan/specs").exists())
            self.assertFalse((target / "contracts").exists())
            self.assertFalse((target / "docs").exists())
            self.assertEqual([], list((target / ".yuan/extensions").glob("*.md")))

    def test_extensions_are_explicit_and_version_is_not_hardcoded(self) -> None:
        with tempfile.TemporaryDirectory(prefix="yuan-m8-ext-") as name:
            target = pathlib.Path(name) / "project"
            result = self.run_init(target, "--extension", "testing")
            self.assertEqual(0, result.returncode, result.stderr)
            self.assertTrue((target / ".yuan/extensions/testing.md").is_file())
            self.assertFalse((target / ".yuan/extensions/ui.md").exists())
        source = INIT.read_text(encoding="utf-8")
        self.assertNotIn('FRAMEWORK_VERSION = "3.0.0"', source)
        self.assertIn('".yuan/VERSION"', source)

    def test_different_existing_file_requires_explicit_update(self) -> None:
        with tempfile.TemporaryDirectory(prefix="yuan-m8-cas-") as name:
            target = pathlib.Path(name) / "project"
            self.assertEqual(0, self.run_init(target).returncode)
            (target / "AGENTS.md").write_text("local\n", encoding="utf-8")
            blocked = self.run_init(target)
            self.assertNotEqual(0, blocked.returncode)
            self.assertEqual("local\n", (target / "AGENTS.md").read_text(encoding="utf-8"))
            updated = self.run_init(target, "--update")
            self.assertEqual(0, updated.returncode, updated.stderr)
            self.assertEqual(
                (ROOT / "AGENTS.md").read_bytes(),
                (target / "AGENTS.md").read_bytes(),
            )


if __name__ == "__main__":
    unittest.main()
