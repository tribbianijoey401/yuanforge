"""Fail-closed staging boundary tests."""

from __future__ import annotations

import importlib.util
import pathlib
import sys
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "scripts/yuan_precommit.py"


class PrecommitGateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        sys.path.insert(0, str(MODULE_PATH.parent))
        spec = importlib.util.spec_from_file_location("yuan_precommit", MODULE_PATH)
        assert spec and spec.loader
        cls.module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.module)

    def test_core_rejects_legacy_shadow_and_projection_staging(self) -> None:
        for path in (
            "docs/PROGRESS.md",
            "contracts/backend-dev.md",
            ".yuan/rules/iron-rules.md",
            ".yuan-shadow/report.json",
            ".yuan-m8-projection/report.json",
        ):
            with self.subTest(path=path):
                with self.assertRaises(self.module.GateError):
                    self.module.check_staged_paths("core", [path])

    def test_declared_core_distribution_paths_are_accepted(self) -> None:
        self.module.check_staged_paths(
            "core",
            [
                "AGENTS.md",
                ".yuan/VERSION",
                ".yuan/authority/current",
                ".yuan-run/contracts/work.json",
                "scripts/yuan_authority.py",
                "tests/authority_switch/test_authority_switch.py",
            ],
        )

    def test_real_repository_gate_passes_without_using_git_status_as_truth(self) -> None:
        receipt = self.module.verify_gate(ROOT, staged_paths=[])
        self.assertEqual("PASS", receipt["status"])
        self.assertEqual("core", receipt["authority"])
        self.assertEqual(4, receipt["revision"])


if __name__ == "__main__":
    unittest.main()
