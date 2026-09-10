"""Multi-Work Phase 2 persisted-state contract tests."""

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
    agent_instance: str | None = None,
    execution_mode: str | None = None,
    execution_workspace: str | None = None,
    current_task: bool = False,
    next_action: bool = False,
    blocker: bool = False,
) -> str:
    current = "\n## Current Task\n\n- Agent: backend-dev\n- Done: focused change verified\n" if current_task else ""
    next_section = "\n## Next Action\n\n继续 focused verification。\n" if next_action else ""
    blocker_section = "\n## Blocker\n\n等待外部 Authority。\n" if blocker else ""
    instance = f"  instance: {agent_instance}\n" if agent_instance is not None else ""
    execution = (
        f"execution:\n  mode: {execution_mode}\n  workspace: {execution_workspace}\n"
        if execution_mode is not None or execution_workspace is not None
        else ""
    )
    return f"""---
id: {work_id}
state: {state}
workflow: {workflow}
stage: {stage}
agent:
  id: {agent_id}
{instance}  state: {agent_state}
{execution}quality:
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
    agent_instance: str | None = None,
    agent_state: str | None = None,
) -> str:
    null = "null"
    focus_text = focus if focus is not None else null
    work_text = focus if focus is not None else null
    workflow_text = workflow if workflow is not None else null
    stage_text = stage if stage is not None else null
    agent_id_text = agent_id if agent_id is not None else null
    agent_instance_text = agent_instance if agent_instance is not None else null
    agent_state_text = agent_state if agent_state is not None else null
    return f"""---
focus: {focus_text}
work: {work_text}
work_state: {work_state}
workflow: {workflow_text}
stage: {stage_text}
agent:
  id: {agent_id_text}
  instance: {agent_instance_text}
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

    def test_allows_two_active_works_with_independent_isolated_execution(self):
        for work_id, workspace, instance in (
            ("W-101", "platform://workspace/one", "subagent-one"),
            ("W-102", "platform://workspace/two", "subagent-two"),
        ):
            self.write_work(work_id, work_payload(
                work_id, state="active", agent_state="active", current_task=True,
                agent_instance=instance, execution_mode="isolated", execution_workspace=workspace,
            ))
        self.write_status(status_payload("W-101", work_state="active", workflow="complex-bug", stage="implement", agent_id="backend-dev", agent_instance="subagent-one", agent_state="active"))
        self.assertEqual([], self.guard.validate_project_state(self.root, FRAMEWORK))

    def test_rejects_concurrent_active_works_without_execution_identity(self):
        for work_id in ("W-101", "W-102"):
            self.write_work(work_id, work_payload(work_id, state="active", agent_state="active", current_task=True, agent_instance=f"subagent-{work_id}"))
        self.write_status(status_payload("W-101", work_state="active", workflow="complex-bug", stage="implement", agent_id="backend-dev", agent_state="active"))
        codes = {issue.code for issue in self.guard.validate_project_state(self.root, FRAMEWORK)}
        self.assertIn("STATE_ACTIVE_WORK_ISOLATION_REQUIRED", codes)
        self.assertIn("STATE_ACTIVE_WORKSPACE_MISSING", codes)

    def test_rejects_concurrent_active_works_with_same_workspace(self):
        for work_id, instance in (("W-101", "subagent-one"), ("W-102", "subagent-two")):
            self.write_work(work_id, work_payload(work_id, state="active", agent_state="active", current_task=True, agent_instance=instance, execution_mode="isolated", execution_workspace="platform://workspace/shared"))
        self.write_status(status_payload("W-101", work_state="active", workflow="complex-bug", stage="implement", agent_id="backend-dev", agent_state="active"))
        codes = {issue.code for issue in self.guard.validate_project_state(self.root, FRAMEWORK)}
        self.assertIn("STATE_ACTIVE_WORKSPACE_CONFLICT", codes)

    def test_rejects_concurrent_active_works_with_same_agent_instance(self):
        for work_id, workspace in (("W-101", "platform://workspace/one"), ("W-102", "platform://workspace/two")):
            self.write_work(work_id, work_payload(work_id, state="active", agent_state="active", current_task=True, agent_instance="subagent-one", execution_mode="isolated", execution_workspace=workspace))
        self.write_status(status_payload("W-101", work_state="active", workflow="complex-bug", stage="implement", agent_id="backend-dev", agent_state="active"))
        codes = {issue.code for issue in self.guard.validate_project_state(self.root, FRAMEWORK)}
        self.assertIn("STATE_ACTIVE_AGENT_INSTANCE_CONFLICT", codes)

    def test_rejects_persona_degraded_as_concurrent_execution(self):
        for work_id, workspace in (("W-101", "platform://workspace/one"), ("W-102", "platform://workspace/two")):
            self.write_work(work_id, work_payload(work_id, state="active", agent_state="active", current_task=True, agent_instance="persona-degraded", execution_mode="isolated", execution_workspace=workspace))
        self.write_status(status_payload("W-101", work_state="active", workflow="complex-bug", stage="implement", agent_id="backend-dev", agent_state="active"))
        self.assertIn("STATE_PARALLEL_EXECUTION_UNAVAILABLE", {issue.code for issue in self.guard.validate_project_state(self.root, FRAMEWORK)})

    def test_allows_focus_switch_between_isolated_active_works(self):
        for work_id, workspace, instance in (
            ("W-101", "platform://workspace/one", "subagent-one"),
            ("W-102", "platform://workspace/two", "subagent-two"),
        ):
            self.write_work(work_id, work_payload(work_id, state="active", agent_state="active", current_task=True, agent_instance=instance, execution_mode="isolated", execution_workspace=workspace))
        self.write_status(status_payload("W-101", work_state="active", workflow="complex-bug", stage="implement", agent_id="backend-dev", agent_instance="subagent-one", agent_state="active"))
        self.assertEqual([], self.guard.validate_project_state(self.root, FRAMEWORK))
        self.write_status(status_payload("W-102", work_state="active", workflow="complex-bug", stage="implement", agent_id="backend-dev", agent_instance="subagent-two", agent_state="active"))
        self.assertEqual([], self.guard.validate_project_state(self.root, FRAMEWORK))

    def test_allows_ready_nonfocused_work_while_another_work_is_active(self):
        self.write_work(
            "W-101",
            work_payload("W-101", state="active", agent_state="active", current_task=True),
        )
        self.write_work(
            "W-102",
            work_payload("W-102", state="ready", agent_state="idle"),
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

        self.assertEqual([], self.guard.validate_project_state(self.root, FRAMEWORK))

    def test_allows_blocked_nonfocused_work_while_another_work_is_active(self):
        self.write_work(
            "W-101",
            work_payload("W-101", state="active", agent_state="active", current_task=True),
        )
        self.write_work(
            "W-102",
            work_payload("W-102", state="blocked", agent_state="blocked", blocker=True),
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

        self.assertEqual([], self.guard.validate_project_state(self.root, FRAMEWORK))

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
            self.assertIn("Phase 2", text)
            self.assertIn("isolated", text)
        self.assertIn("Work 本身作为执行隔离边界", contract)
        self.assertIn("STATUS.focus", contract)
        self.assertIn("Legacy", contract)
        self.assertIn("不引入并行 Work Scheduler", conductor)
        self.assertIn("focus: null", status_template)


if __name__ == "__main__":
    unittest.main()
