"""Acceptance tests for the M8/M9 successor runtime generation."""

from __future__ import annotations

import json
import pathlib
import sys
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))

from yuan_authority import load_current, verify_authority
from yuan_runtime_state import file_sha256, resolve_runtime_root, verify_runtime
from yuan_successor_run import verify_runtime_archive


class SuccessorRunTests(unittest.TestCase):
    def test_old_runtime_is_recoverable_but_not_active(self) -> None:
        archive = verify_runtime_archive(
            ROOT,
            "a803caf92d9db6b74b67ac8ebd7e4cb76b773a46b267d07406a8298d37891fc4",
        )
        self.assertEqual({"work": 1, "attempt": 37, "evidence": 37}, archive["counts"])
        runtime, pointer, _ = resolve_runtime_root(ROOT)
        self.assertIsNotNone(pointer)
        self.assertNotEqual(ROOT / ".yuan-run", runtime)
        self.assertTrue(verify_runtime(ROOT)["memory_rebuildable"])

    def test_successor_is_bounded_and_has_a_legal_step(self) -> None:
        runtime, _, _ = resolve_runtime_root(ROOT)
        work = json.loads(next((runtime / "contracts").glob("*.json")).read_text())
        memory = json.loads((runtime / "run-memory.json").read_text())
        criteria = {item["id"]: item for item in work["acceptance_criteria"]}
        self.assertEqual(
            {
                "AC-M8-AUTHORITY-SWITCH",
                "AC-M9-SELF-MODIFICATION-DOGFOOD",
                "AC-M9-LEGACY-TOMBSTONE-WAIT-AUTH",
            },
            set(criteria),
        )
        self.assertEqual("human-judgment", criteria[
            "AC-M9-LEGACY-TOMBSTONE-WAIT-AUTH"
        ]["type"])
        self.assertIn(".yuan/authority", work["scope"]["allowed_paths"])
        self.assertIn(".yuan-run", work["scope"]["allowed_paths"])
        self.assertNotIn("docs", work["authorization"]["grants"][0]["scopes"])
        self.assertTrue(all(value > 0 for value in work["budget"].values()))
        self.assertEqual("CONTINUE", memory["last_result"])
        self.assertEqual(
            "AC-M9-SELF-MODIFICATION-DOGFOOD",
            memory["legal_next_steps"][0]["ac_id"],
        )

    def test_current_authority_binds_runtime_and_old_root_activation(self) -> None:
        verified = verify_authority(ROOT)
        current = load_current(ROOT)["record"]
        runtime, _, active_sha = resolve_runtime_root(ROOT)
        activation = current["protocol_activation"]
        self.assertEqual(6, verified["revision"])
        self.assertEqual(runtime.relative_to(ROOT).as_posix(), current["runtime_root"])
        self.assertEqual(active_sha, current["runtime_pointer_sha256"])
        self.assertEqual(
            file_sha256(ROOT / ".yuan/core/0.1/protocol.md"),
            activation["protocol_sha256"],
        )
        self.assertEqual("legacy", activation["accepted_by_authority"])
        self.assertEqual(80, activation["assertions"])


if __name__ == "__main__":
    unittest.main()
