"""Yuan Insight Headless Collector 测试。"""

from __future__ import annotations

import json
import sys
import tempfile
import time
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "insight"))

from yuan_insight.diff import diff_snapshots, to_transition  # noqa: E402
from yuan_insight.loader import Snapshot, build_snapshot  # noqa: E402
from yuan_insight.observer import ObservationService  # noqa: E402
from yuan_insight.parsers.status import parse_status  # noqa: E402
from yuan_insight.parsers.work import parse_work  # noqa: E402
from yuan_insight.trace import append_transition, ensure_insight_dir, start_session  # noqa: E402
from yuan_insight.watcher import DebouncedWatcher  # noqa: E402


def make_project(tmp: Path) -> Path:
    root = tmp / "project"
    (root / "docs").mkdir(parents=True)
    (root / "framework" / "workflows").mkdir(parents=True)
    return root


def write_status(root: Path, work: str, stage: str, agent: str, agent_state: str) -> None:
    (root / "docs" / "STATUS.md").write_text(
        f"""---
work: {work}
work_state: active
workflow: complex-bug
stage: {stage}
agent:
  id: {agent}
  state: {agent_state}
quality:
  test: pending
  review: pending
---

# Current Situation
调试中
""",
        encoding="utf-8",
    )


def write_idle_status(root: Path) -> None:
    (root / "docs" / "STATUS.md").write_text(
        """---
work: null
work_state: idle
workflow: null
stage: null
agent:
  id: null
  state: null
quality:
  test: pending
  review: pending
---

# Current Situation
无 Active Work
""",
        encoding="utf-8",
    )


def wait_for_update(service: ObservationService, timeout: float = 2.0):
    deadline = time.time() + timeout
    while time.time() < deadline:
        update = service.poll_once()
        if update is not None:
            return update
        time.sleep(0.02)
    return None


class StatusParserTests(unittest.TestCase):
    def test_parses_frontmatter_and_sections(self):
        state = parse_status(
            """---
work: BUG-001
work_state: active
workflow: complex-bug
stage: implement
agent:
  id: backend-dev
  state: active
quality:
  test: pending
  review: pending
---

# Current Situation
调试 token race
"""
        )
        self.assertEqual(state.work, "BUG-001")
        self.assertEqual(state.workflow, "complex-bug")
        self.assertEqual(state.stage, "implement")
        self.assertEqual(state.agent_id, "backend-dev")
        self.assertEqual(state.agent_state, "active")
        self.assertEqual(state.quality_test, "pending")
        self.assertIn("token race", state.situation or "")

    def test_missing_frontmatter_is_unknown(self):
        state = parse_status("# Status\n\n无 frontmatter")
        self.assertIsNone(state.work)
        self.assertIsNone(state.workflow)


class WorkParserTests(unittest.TestCase):
    def test_parses_contract_and_workspace(self):
        state = parse_work(
            """# Active Work

## Goal

修 bug

## Active Workspace

## Current Task

修 token race

## Latest Result

outcome: partial

## Open Findings

- [ ] 补回归测试

## Work Learnings

- cache 不是根因
"""
        )
        self.assertTrue(state.has_active_work)
        self.assertEqual(state.goal, "修 bug")
        self.assertEqual(state.current_task, "修 token race")
        self.assertEqual(state.open_findings, ["[ ] 补回归测试"])
        self.assertEqual(state.work_learnings, ["cache 不是根因"])

    def test_empty_findings_is_empty_list(self):
        state = parse_work(
            """# Active Work

## Goal

x

## Active Workspace

## Open Findings

无
"""
        )
        self.assertEqual(state.open_findings, [])


class DiffTests(unittest.TestCase):
    def test_snapshot_diff_produces_facts_and_transition(self):
        before = Snapshot(
            observed_at="t0",
            files={"docs/STATUS.md": "hash-a", "docs/WORK.md": "hash-a"},
            status={"stage": "implement", "agent": {"id": "backend-dev", "state": "active"}},
            work={"has_active_work": True, "current_task": "task-1"},
            workflow={"workflow_id": "complex-bug", "required_agents": ["tester"]},
        )
        after = Snapshot(
            observed_at="t1",
            files={"docs/STATUS.md": "hash-b", "docs/WORK.md": "hash-a"},
            status={"stage": "regression", "agent": {"id": "tester", "state": "active"}},
            work={"has_active_work": True, "current_task": "task-1"},
            workflow={"workflow_id": "complex-bug", "required_agents": ["tester"]},
        )
        facts = diff_snapshots(before, after)
        kinds = {fact["kind"] for fact in facts}
        self.assertIn("files_changed", kinds)
        self.assertIn("field_changed", kinds)
        transition = to_transition("T-0001", "OBS-1", "t1", before, after, facts)
        self.assertEqual(transition["id"], "T-0001")
        self.assertEqual(transition["sources_changed"], ["docs/STATUS.md"])
        self.assertNotEqual(transition["before_hash"], transition["after_hash"])


class WatcherTests(unittest.TestCase):
    def test_debounce_merges_rapid_changes(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = make_project(Path(temporary))
            write_status(root, "BUG-1", "implement", "backend-dev", "active")
            watcher = DebouncedWatcher(root, poll_interval=0.01, debounce_window=0.05)
            # 第一次 tick 建立 baseline，不产出事件
            self.assertIsNone(watcher.tick())
            # 快速连续修改 STATUS 两次（模拟 Conductor 一次语义更新写多个文件）
            write_status(root, "BUG-1", "regression", "tester", "active")
            self.assertIsNone(watcher.tick())
            write_status(root, "BUG-1", "review", "spec-reviewer", "active")
            self.assertIsNone(watcher.tick())
            # debounce 窗口内继续安静，产出合并后的一个事件
            import time

            time.sleep(0.15)
            event = watcher.tick()
            self.assertIsNotNone(event)
            self.assertEqual(event.changed, ["docs/STATUS.md"])  # type: ignore[union-attr]
            self.assertEqual(event.snapshot.status["stage"], "review")  # type: ignore[union-attr]
            # 第二次稳定后不应再产出（pending 已清空）
            self.assertIsNone(watcher.tick())


class TraceTests(unittest.TestCase):
    def test_append_transition_writes_jsonl(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            insight_dir = ensure_insight_dir(root)
            session_id = "OBS-TEST"
            baseline = build_snapshot(root, "t0")
            insight_dir, session_id = start_session(root, baseline)
            trace_path = append_transition(
                insight_dir,
                {"id": "T-0001", "session_id": session_id, "facts": []},
            )
            self.assertTrue(trace_path.is_file())
            line = trace_path.read_text(encoding="utf-8").strip()
            record = json.loads(line)
            self.assertEqual(record["id"], "T-0001")


class ObservationServiceTests(unittest.TestCase):
    def test_work_completion_archives_trace_and_writes_summary(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = make_project(Path(temporary))
            write_status(root, "BUG-9", "distill", "tester", "completed")
            (root / "docs" / "WORK.md").write_text(
                "# Active Work\n\n## Goal\n\n修复 BUG-9\n",
                encoding="utf-8",
            )
            service = ObservationService(root, poll_interval=0.01, debounce_window=0.02)
            service.start()
            write_idle_status(root)
            (root / "docs" / "WORK.md").write_text(
                "# Active Work\n\nNo active work.\n",
                encoding="utf-8",
            )
            update = wait_for_update(service)
            service.stop()
            self.assertIsNotNone(update)
            self.assertTrue((root / ".yuan" / "insight" / "traces" / "BUG-9.jsonl").is_file())
            self.assertTrue((root / ".yuan" / "insight" / "summaries" / "BUG-9.json").is_file())
            self.assertFalse((root / ".yuan" / "insight" / "traces" / "current.jsonl").exists())

    def test_restart_records_gap_and_active_work_is_partial(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = make_project(Path(temporary))
            write_status(root, "BUG-10", "implement", "backend-dev", "active")
            (root / "docs" / "WORK.md").write_text(
                "# Active Work\n\n## Goal\n\n修复 BUG-10\n",
                encoding="utf-8",
            )
            first = ObservationService(root, poll_interval=0.01, debounce_window=0.02)
            first.start()
            first.stop()
            time.sleep(0.01)
            second = ObservationService(root, poll_interval=0.01, debounce_window=0.02)
            second.start()
            evidence = second.evidence()
            second.stop()
            self.assertEqual(evidence.coverage, "PARTIAL")
            self.assertEqual(len(evidence.gaps), 1)
            self.assertLess(evidence.gaps[0]["gap_start"], evidence.gaps[0]["gap_end"])

    def test_work_started_while_observing_has_full_coverage(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = make_project(Path(temporary))
            write_idle_status(root)
            (root / "docs" / "WORK.md").write_text(
                "# Active Work\n\nNo active work.\n",
                encoding="utf-8",
            )
            service = ObservationService(root, poll_interval=0.01, debounce_window=0.02)
            service.start()
            write_status(root, "BUG-11", "orient", "backend-dev", "active")
            (root / "docs" / "WORK.md").write_text(
                "# Active Work\n\n## Goal\n\n修复 BUG-11\n",
                encoding="utf-8",
            )
            update = wait_for_update(service)
            evidence = service.evidence()
            service.stop()
            self.assertIsNotNone(update)
            self.assertEqual(evidence.coverage, "FULL")
            self.assertTrue(evidence.transitions)


if __name__ == "__main__":
    unittest.main()
