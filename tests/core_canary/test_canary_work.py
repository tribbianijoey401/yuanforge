"""M5 Hard Gate over the persisted, real reference-Port canary Work."""

from __future__ import annotations

import importlib.util
import pathlib
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[2]
RUN_ROOT = (
    ROOT
    / "docs"
    / "20260726-yuan-core-01-upgrade"
    / "evidence"
    / "m5"
    / "canary-run"
)
VERIFIER_PATH = pathlib.Path(__file__).with_name("verify_canary.py")
SPEC = importlib.util.spec_from_file_location("m5_canary_verifier", VERIFIER_PATH)
assert SPEC and SPEC.loader
VERIFIER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VERIFIER)


class CanaryWorkTests(unittest.TestCase):
    def test_real_canary_and_all_fail_closed_recovery_checks_pass(self) -> None:
        result = VERIFIER.verify(RUN_ROOT, persist=False)
        failures = [item for item in result["checks"] if item["status"] != "PASS"]
        self.assertEqual([], failures, failures)
        self.assertEqual("PASS", result["status"])
        self.assertGreaterEqual(result["assertions"], 13)


if __name__ == "__main__":
    unittest.main()
