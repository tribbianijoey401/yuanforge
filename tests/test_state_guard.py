"""Canonical Yuan State Commit contract tests."""

from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
GUARD_PATH = ROOT / "framework" / "tools" / "state_guard.py"


def load_guard():
    spec = importlib.util.spec_from_file_location("yuan_state_guard", GUARD_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load {GUARD_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def write_work(root: Path, *, next_action: bool = False) -> None:
    suffix = "\n## Next Action\n\n继续验证。\n" if next_action else ""
    (root / "docs" / "WORK.md").write_text(
        "# Active Work\n\n## Goal\n\n修复状态提交。\n\n"
        "## Current Task\n\n- Agent: backend-dev\n" + suffix,
        encoding="utf-8",
    )


def write_status(
    root: Path,
    *,
    stage: str = "implement",
    agent_id: str = "backend-dev",
    work_state: str = "active",
    agent_state: str = "active",
    extras: str = "",
) -> None:
    (root / "docs" / "STATUS.md").write_text(
        f"""---
work: BUG-state-contract
work_state: {work_state}
workflow: complex-bug
stage: {stage}
activity: specialist_execution
agent:
  id: {agent_id}
  instance: frontend-fixer
  state: {agent_state}
{extras}---

# Current Situation

验证状态契约。
""",
        encoding="utf-8",
    )


class StateGuardTests(unittest.TestCase):
    def setUp(self) -> None:
        self.guard = load_guard()
        self.temp = tempfile.TemporaryDirectory(prefix="yuan-state-guard-")
        self.root = Path(self.temp.name) / "project"
        (self.root / "docs").mkdir(parents=True)
        self.framework = ROOT / "framework"

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_ignores_legacy_activity_while_accepting_canonical_state(self):
        write_work(self.root)
        write_status(self.root)

        issues = self.guard.validate_project_state(self.root, self.framework)

        self.assertEqual([], issues)

    def test_rejects_freeform_stage_and_agent_id_with_deterministic_repairs(self):
        write_work(self.root)
        write_status(
            self.root,
            stage="specialist_execution",
            agent_id="frontend-fixer",
        )

        issues = self.guard.validate_project_state(self.root, self.framework)
        by_field = {issue.field: issue for issue in issues}

        self.assertEqual("STATE_STAGE_UNKNOWN", by_field["stage"].code)
        self.assertNotIn("activity", by_field["stage"].repair)
        self.assertEqual("STATE_AGENT_UNKNOWN", by_field["agent.id"].code)
        self.assertIn("agent.instance", by_field["agent.id"].repair)

    def test_paused_work_requires_paused_agent_and_next_action(self):
        write_work(self.root)
        write_status(self.root, work_state="paused", agent_state="active")

        issues = self.guard.validate_project_state(self.root, self.framework)
        codes = {issue.code for issue in issues}

        self.assertIn("STATE_AGENT_STATE_MISMATCH", codes)
        self.assertIn("STATE_NEXT_ACTION_MISSING", codes)

    def test_catalog_comes_from_framework_files(self):
        catalog = self.guard.build_catalog(self.framework, "complex-bug")

        self.assertIn("frontend-dev", catalog["agents"])
        self.assertIn("implement", catalog["stages"])
        self.assertIn("frontend-dev", catalog["workflow_agents"])
        self.assertNotIn("doc-engineer", catalog["workflow_agents"])
        self.assertEqual(["idle", "active", "paused"], catalog["work_states"])

    def test_rejects_registered_agent_not_declared_by_workflow(self):
        write_work(self.root)
        write_status(self.root, agent_id="doc-engineer")

        issues = self.guard.validate_project_state(self.root, self.framework)

        self.assertIn("STATE_AGENT_NOT_ALLOWED", {issue.code for issue in issues})


if __name__ == "__main__":
    unittest.main()
