"""Hard-gate tests for the independent M3 Core verifier."""

from __future__ import annotations

import importlib.util
import pathlib
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[2]
VALIDATOR_PATH = pathlib.Path(__file__).with_name("held_out_validator.py")
SPEC = importlib.util.spec_from_file_location("m3_held_out_validator", VALIDATOR_PATH)
assert SPEC and SPEC.loader
VALIDATOR = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(VALIDATOR)


class CoreCandidateHeldOutTests(unittest.TestCase):
    def test_all_independent_semantic_attacks_pass(self) -> None:
        result = VALIDATOR.run(ROOT / ".yuan" / "core" / "0.1")
        failures = [
            item
            for item in result.get("observations", [])
            if item.get("status") != "PASS"
        ]
        self.assertEqual([], failures, failures)
        self.assertEqual("PASS", result["status"])
        self.assertGreaterEqual(result["assertions"], 25)


if __name__ == "__main__":
    unittest.main()
