"""Insight regression tests for Multi-Work focus switching and completion."""

from __future__ import annotations

import shutil
import sys
import tempfile
import time
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "insight"))

from yuan_insight.observer import ObservationService  # noqa: E402


def write_work(root: Path, work_id: str, state: str, *, instance: str | None = None, workspace: str | None = None) -> None:
    if state == "active":
        agent_state = "active"
        extra = "\n## Current Task\n\n完成当前实现。\n"
    elif state == "paused":
        agent_state = "paused"
        extra = "\n## Next Action\n\n从当前断点继续。\n"
    else:
        raise ValueError(state)

    execution = (
        f"execution:\n  mode: isolated\n  workspace: {workspace}\n"
        if workspace else ""
    )

    path = root / "docs" / "works" / f"{work_id}.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        f"""---
id: {work_id}
state: {state}
workflow: complex-bug
stage: implement
agent:
  id: backend-dev
  instance: {instance or 'null'}
  state: {agent_state}
{execution}quality:
  test: pending
  review: pending
---

# Active Work

## Goal

完成 {work_id}。

## Scope

只处理当前 Work。
{extra}
""",
        encoding="utf-8",
    )


def write_status(root: Path, focus: str | None, state: str = "idle", instance: str | None = None) -> None:
    if focus is None:
        payload = """---
focus: null
work: null
work_state: idle
workflow: null
stage: null
agent:
  id: null
  instance: {instance or 'null'}
  state: null
quality:
  test: pending
  review: pending
---

# Project Recovery Index
"""
    else:
        agent_state = "paused" if state == "paused" else "active"
        payload = f"""---
focus: {focus}
work: {focus}
work_state: {state}
workflow: complex-bug
stage: implement
agent:
  id: backend-dev
  instance: null
  state: {agent_state}
quality:
  test: pending
  review: pending
---

# Project Recovery Index
"""
    (root / "docs" / "STATUS.md").write_text(payload, encoding="utf-8")


def wait_for_update(service: ObservationService, timeout: float = 3.0):
    deadline = time.time() + timeout
    while time.time() < deadline:
        update = service.poll_once()
        if update is not None:
            return update
        time.sleep(0.02)
    return None


class InsightMultiWorkTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory(prefix="yuan-insight-multi-work-")
        self.root = Path(self.temp.name) / "project"
        (self.root / "docs" / "works").mkdir(parents=True)
        shutil.copytree(ROOT / "framework", self.root / "framework")

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_focus_switch_rotates_trace_without_false_completion_summary(self):
        write_work(self.root, "W-101", "active")
        write_status(self.root, "W-101", "active")
        service = ObservationService(self.root, poll_interval=0.01, debounce_window=0.01)
        service.start()
        try:
            write_work(self.root, "W-101", "paused")
            write_work(self.root, "W-102", "active")
            write_status(self.root, "W-102", "active")

            update = wait_for_update(service)
            self.assertIsNotNone(update)
            self.assertTrue((self.root / ".yuan" / "insight" / "traces" / "W-101.jsonl").is_file())
            self.assertFalse((self.root / ".yuan" / "insight" / "summaries" / "W-101.json").exists())
            self.assertEqual("W-102", service.current_work_id)
        finally:
            service.stop()

    def test_removing_canonical_work_after_distill_creates_summary(self):
        write_work(self.root, "W-201", "active")
        write_status(self.root, "W-201", "active")
        service = ObservationService(self.root, poll_interval=0.01, debounce_window=0.01)
        service.start()
        try:
            (self.root / "docs" / "works" / "W-201.md").unlink()
            write_status(self.root, None)

            update = wait_for_update(service)
            self.assertIsNotNone(update)
            self.assertTrue((self.root / ".yuan" / "insight" / "traces" / "W-201.jsonl").is_file())
            self.assertTrue((self.root / ".yuan" / "insight" / "summaries" / "W-201.json").is_file())
            self.assertIsNone(service.current_work_id)
        finally:
            service.stop()

    def test_focus_null_does_not_require_legacy_work_file_for_coverage(self):
        write_work(self.root, "W-301", "paused")
        write_status(self.root, None)
        legacy = self.root / "docs" / "WORK.md"
        legacy.unlink(missing_ok=True)

        service = ObservationService(self.root, poll_interval=0.01, debounce_window=0.01)
        service.start()
        try:
            self.assertNotEqual("UNKNOWN", service.coverage)
            self.assertIsNone(service.current_work_id)
        finally:
            service.stop()

    def test_nonfocused_isolated_active_work_writes_its_own_trace(self):
        write_work(self.root, "W-401", "active", instance="subagent-one", workspace="platform://workspace/one")
        write_work(self.root, "W-402", "active", instance="subagent-two", workspace="platform://workspace/two")
        write_status(self.root, "W-401", "active", instance="subagent-one")
        service = ObservationService(self.root, poll_interval=0.01, debounce_window=0.01)
        service.start()
        try:
            write_work(self.root, "W-402", "active", instance="subagent-two", workspace="platform://workspace/two")
            work = self.root / "docs" / "works" / "W-402.md"
            work.write_text(work.read_text(encoding="utf-8") + "\n## Latest Result\n\nW-402 advanced independently.\n", encoding="utf-8")
            update = wait_for_update(service)
            self.assertIsNotNone(update)
            w2_trace = self.root / ".yuan" / "insight" / "traces" / "W-402.jsonl"
            self.assertTrue(w2_trace.is_file())
            self.assertIn('"work_id": "W-402"', w2_trace.read_text(encoding="utf-8"))
            self.assertFalse((self.root / ".yuan" / "insight" / "traces" / "W-401.jsonl").exists())
        finally:
            service.stop()


if __name__ == "__main__":
    unittest.main()
