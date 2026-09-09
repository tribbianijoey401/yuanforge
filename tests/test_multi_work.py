"""Multi-Work Phase 1 persisted-state contract tests."""

from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FRAMEWORK = ROOT / "framework"
GUARD_PATH = FRAMEWORK / "tools" / "state_guard.py"


def load_guard():
    spec = importlib.util.spec_from_file_location("yuan_multi_work_guard", GUARD_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load {GUARD_PATH}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def work_payload(
    work_id: str,
    *,
    state: str,
    workflow: str = "complex-bug",
    stage: str = "implement",
    agent_id: str = "backend-dev",
    agent_state: str = "active",
    current_task: bool = False,
    next_action: bool = False,
    blocker: bool = False,
) -> str:
    current = "\n## Current Task\n\n- Agent: backend-dev\n- Done: focused change verified\n" if current_task else ""
    next_section = "\n## Next Action\n\n继续 focused verification。\n" if next_action else ""
    blocker_section = "\n## Blocker\n\n等待外部 Authority。\n" if blocker else ""
    return f"""---
id: {work_id}
state: {state}
workflow: {workflow}
stage: {stage}
agent:
  id: {agent_id}
  state: {agent_state}
quality:
  test: pending
  review: pending
---

# Active Work

## Goal

完成 {work_id}。

## Scope

只修改当前 Work。
{current}{next_section}{blocker_section}
"""


def status_payload(
    focus: str | None,
    *,
    work_state: str = "idle",
    workflow: str | None = None,
    stage: str | None = None,
    agent_id: str | None = None,
    agent_state: str | None = None,
) -> str:
    null = "null"
    focus_text = focus if focus is not None else null
    work_text = focus if focus is not None else null
    workflow_text = workflow if workflow is not None else null
    stage_text = stage if stage is not None else null
    agent_id_text = agent_id if agent_id is not None else null
    agent_state_text = agent_state if agent_state is not None else null
    return f"""---
focus: {focus_text}
work: {work_text}
work_state: {work_state}
workflow: {workflow_text}
stage: {stage_text}
agent:
  id: {agent_id_text}
  instance: null
  state: {agent_state_text}
quality:
  test: pending
  review: pending
---

# Project Recovery Index
"""


class MultiWorkStateTests(unittest.TestCase):
    def setUp(self) -> None:
        self.guard = load_guard()
        self.temp = tempfile.TemporaryDirectory(prefix="yuan-multi-work-")
        self.root = Path(self.temp.name) / "project"
        (self.root / "docs" / "works").mkdir(parents=True)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def write_work(self, work_id: str, payload: str) -> None:
        (self.root / "docs" / "works" / f"{work_id}.md").write_text(payload, encoding="utf-8")

    def write_status(self, payload: str) -> None:
        (self.root / "docs" / "STATUS.md").write_text(payload, encoding="utf-8")

    def test_allows_multiple_persisted_works_with_only_one_active(self):
        self.write_work(
            "W-101",
            work_payload("W-101", state="active", agent_state="active", current_task=True),
        )
        self.write_work(
            "W-102",
            work_payload("W-102", state="paused", agent_state="paused", next_action=True),
        )
        self.write_status(
            status_payload(
                "W-101",
                work_state="active",
                workflow="complex-bug",
                stage="implement",
                agent_id="backend-dev",
                agent_state="active",
            )
        )

        issues = self.guard.validate_project_state(self.root, FRAMEWORK)

        self.assertEqual([], issues)

    def test_rejects_two_active_works_without_inventing_scheduler_semantics(self):
        for work_id in ("W-101", "W-102"):
            self.write_work(
                work_id,
                work_payload(work_id, state="active", agent_state="active", current_task=True),
            )
        self.write_status(
            status_payload(
                "W-101",
                work_state="active",
                workflow="complex-bug",
                stage="implement",
                agent_id="backend-dev",
                agent_state="active",
            )
        )

        issues = self.guard.validate_project_state(self.root, FRAMEWORK)

        self.assertIn("STATE_MULTIPLE_ACTIVE_WORKS", {issue.code for issue in issues})

    def test_rejects_status_projection_that_diverges_from_focused_work(self):
        self.write_work(
            "W-101",
            work_payload("W-101", state="active", agent_state="active", current_task=True),
        )
        self.write_status(
            status_payload(
                "W-101",
                work_state="paused",
                workflow="complex-bug",
                stage="implement",
                agent_id="backend-dev",
                agent_state="paused",
            )
        )

        issues = self.guard.validate_project_state(self.root, FRAMEWORK)

        self.assertIn("STATE_FOCUS_PROJECTION_MISMATCH", {issue.code for issue in issues})

    def test_only_active_work_must_be_the_focus(self):
        self.write_work(
            "W-101",
            work_payload("W-101", state="active", agent_state="active", current_task=True),
        )
        self.write_work(
            "W-102",
            work_payload("W-102", state="paused", agent_state="paused", next_action=True),
        )
        self.write_status(
            status_payload(
                "W-102",
                work_state="paused",
                workflow="complex-bug",
                stage="implement",
                agent_id="backend-dev",
                agent_state="paused",
            )
        )

        issues = self.guard.validate_project_state(self.root, FRAMEWORK)

        self.assertIn("STATE_ACTIVE_WORK_NOT_FOCUSED", {issue.code for issue in issues})

    def test_new_project_can_be_idle_without_creating_empty_work_files(self):
        self.write_status(status_payload(None))

        issues = self.guard.validate_project_state(self.root, FRAMEWORK)

        self.assertEqual([], issues)

    def test_contract_keeps_work_as_isolation_boundary_not_scheduler(self):
        contract = (FRAMEWORK / "policies" / "state-contract.md").read_text(encoding="utf-8")
        documents = (FRAMEWORK / "policies" / "documents.md").read_text(encoding="utf-8")
        conductor = (FRAMEWORK / "agents" / "conductor.md").read_text(encoding="utf-8")
        status_template = (FRAMEWORK / "templates" / "project" / "STATUS.md").read_text(encoding="utf-8")

        for text in (contract, documents, conductor):
            self.assertIn("docs/works/", text)
            self.assertIn("Phase 1", text)
            self.assertIn("最多一个", text)
        self.assertIn("Work 本身作为执行隔离边界", contract)
        self.assertIn("STATUS.focus", contract)
        self.assertIn("Legacy", contract)
        self.assertIn("不引入并行 Work Scheduler", conductor)
        self.assertIn("focus: null", status_template)


if __name__ == "__main__":
    unittest.main()
