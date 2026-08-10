"""Yuan Insight Headless Collector 测试。"""

from __future__ import annotations

import json
import sys
import tempfile
import time
import unittest
from unittest.mock import patch
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "insight"))

from yuan_insight.diff import diff_snapshots, to_transition  # noqa: E402
from yuan_insight.loader import Snapshot, build_snapshot  # noqa: E402
from yuan_insight.observer import ObservationService  # noqa: E402
from yuan_insight.registry import AgentContract, Registry  # noqa: E402
from yuan_insight.signals.aggregate import compute_signals  # noqa: E402
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
activity: specialist_execution
agent:
  id: backend-dev
  instance: frontend-fixer
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
        self.assertFalse(hasattr(state, "activity"))
        self.assertEqual(state.agent_id, "backend-dev")
        self.assertEqual(state.agent_instance, "frontend-fixer")
        self.assertEqual(state.agent_state, "active")
        self.assertEqual(state.quality_test, "pending")
        self.assertIn("token race", state.situation or "")

    def test_snapshot_does_not_project_legacy_activity(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = make_project(Path(temporary))
            write_status(root, "BUG-activity", "implement", "backend-dev", "active")
            status_path = root / "docs" / "STATUS.md"
            status_path.write_text(
                status_path.read_text(encoding="utf-8").replace(
                    "stage: implement\n",
                    "stage: implement\nactivity: legacy_execution_label\n",
                ),
                encoding="utf-8",
            )

            snapshot = build_snapshot(root, "1.0").to_dict()

            self.assertNotIn("activity", snapshot["status"])

    def test_missing_frontmatter_is_unknown(self):
        state = parse_status("# Status\n\n无 frontmatter")
        self.assertIsNone(state.work)
        self.assertIsNone(state.workflow)


class WorkParserTests(unittest.TestCase):
    def test_empty_work_template_does_not_expose_html_guidance_as_state(self):
        template = (
            ROOT / "framework" / "templates" / "project" / "WORK.md"
        ).read_text(encoding="utf-8")

        state = parse_work(template)

        self.assertFalse(state.has_active_work)
        self.assertIsNone(state.current_task)
        self.assertIsNone(state.latest_result)
        self.assertEqual([], state.open_findings)

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
            watcher = DebouncedWatcher(
                root,
                poll_interval=0.01,
                debounce_window=0.05,
                prefer_native=False,
            )
            # 第一次 tick 建立 baseline，不产出事件
            self.assertIsNone(watcher.tick())
            # 快速连续修改 STATUS 两次（模拟 Conductor 一次语义更新写多个文件）
            write_status(root, "BUG-1", "regression", "tester", "active")
            self.assertIsNone(watcher.tick())
            write_status(root, "BUG-1", "review", "spec-reviewer", "active")
            self.assertIsNone(watcher.tick())
            # debounce 窗口内继续安静，产出合并后的一个事件
            time.sleep(0.15)
            event = watcher.tick()
            self.assertIsNotNone(event)
            self.assertEqual(event.changed, ["docs/STATUS.md"])  # type: ignore[union-attr]
            self.assertEqual(event.snapshot.status["stage"], "review")  # type: ignore[union-attr]
            # 第二次稳定后不应再产出（pending 已清空）
            self.assertIsNone(watcher.tick())

    def test_native_source_observes_separate_persisted_transitions(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = make_project(Path(temporary))
            write_status(root, "BUG-NATIVE", "implement", "backend-dev", "active")
            watcher = DebouncedWatcher(root, poll_interval=0.02, debounce_window=0.02)
            self.addCleanup(watcher.close)
            if not watcher.native:
                self.skipTest("Native file events are unavailable on this platform")
            self.assertTrue(watcher.mode.startswith("native-"))
            baseline = build_snapshot(root, "baseline")
            # Simulate a write racing with ObservationService baseline setup.
            write_status(root, "BUG-NATIVE", "regression", "tester", "active")
            watcher.wait()
            watcher.prime(baseline.files)
            first = self._wait_for_event(watcher)
            second = self._write_and_wait(
                watcher,
                lambda: write_status(root, "BUG-NATIVE", "review", "spec-reviewer", "active"),
            )
            self.assertEqual(first.snapshot.status["stage"], "regression")
            self.assertEqual(second.snapshot.status["stage"], "review")

    @staticmethod
    def _write_and_wait(watcher: DebouncedWatcher, write) -> object:
        write()
        return WatcherTests._wait_for_event(watcher)

    @staticmethod
    def _wait_for_event(watcher: DebouncedWatcher) -> object:
        deadline = time.time() + 2
        while time.time() < deadline:
            watcher.wait()
            event = watcher.tick()
            if event is not None:
                return event
        raise AssertionError("Native watcher did not emit a persisted transition")


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
    def test_missing_required_state_files_make_coverage_unknown(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = make_project(Path(temporary))
            (root / "docs" / "WORK.md").unlink(missing_ok=True)
            (root / "docs" / "STATUS.md").unlink(missing_ok=True)
            service = ObservationService(root, poll_interval=0.01, debounce_window=0.01)
            service.start()
            try:
                self.assertEqual("UNKNOWN", service.evidence().coverage)
                self.assertIsNotNone(service.latest_snapshot)
                snapshot = service.latest_snapshot.to_dict()
                self.assertEqual("MISSING", snapshot["sources"]["docs/WORK.md"])
                self.assertEqual("MISSING", snapshot["sources"]["docs/STATUS.md"])
            finally:
                service.stop()

    def test_polling_fallback_is_explicit_and_partial(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = make_project(Path(temporary))
            write_idle_status(root)
            (root / "docs" / "WORK.md").write_text(
                "# Active Work\n\nNo active work.\n",
                encoding="utf-8",
            )
            with patch("yuan_insight.watcher.create_event_source", return_value=None):
                service = ObservationService(root, poll_interval=0.01, debounce_window=0.01)
                service.start()
                self.assertEqual(service.evidence().mode, "polling-fallback")
                self.assertEqual(service.evidence().coverage, "PARTIAL")
                write_status(root, "BUG-FALLBACK", "orient", "backend-dev", "active")
                update = wait_for_update(service)
                service.stop()
            self.assertIsNotNone(update)

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


class StateConsistencySignalTests(unittest.TestCase):
    def test_snapshot_and_signal_use_vendored_state_guard_codes(self):
        import shutil

        with tempfile.TemporaryDirectory(prefix="yuan-insight-state-contract-") as parent:
            root = Path(parent) / "project"
            (root / "docs").mkdir(parents=True)
            shutil.copytree(ROOT / "framework", root / ".yuan" / "framework")
            write_status(
                root,
                "BUG-contract",
                "specialist_execution",
                "frontend-fixer",
                "running",
            )
            (root / "docs" / "WORK.md").write_text(
                "# Active Work\n\n## Goal\n\n修复状态。\n\n"
                "## Current Task\n\n执行实现。\n",
                encoding="utf-8",
            )

            snapshot = build_snapshot(root, "1.0").to_dict()
            codes = {issue["code"] for issue in snapshot["state_validation"]}
            registry = Registry(
                agents={"conductor": AgentContract("conductor")},
                workflows=["complex-bug"],
            )
            report = compute_signals(snapshot, registry)
            divergence = next(
                signal for signal in report.signals
                if signal.signal_id == "STATE_DIVERGENCE"
            )

            self.assertIn("STATE_STAGE_UNKNOWN", codes)
            self.assertIn("STATE_AGENT_UNKNOWN", codes)
            self.assertIn("STATE_AGENT_STATE_UNKNOWN", codes)
            self.assertIn("STATE_STAGE_UNKNOWN", divergence.summary)
            self.assertIn("STATE_AGENT_UNKNOWN", divergence.summary)

    def test_missing_work_and_status_are_not_reported_as_idle(self):
        registry = Registry(
            agents={"conductor": AgentContract("conductor")},
            workflows=["complex-bug"],
        )
        snapshot = {
            "sources": {
                "docs/WORK.md": "MISSING",
                "docs/STATUS.md": "MISSING",
            },
            "status": {"work_state": None},
            "work": {"has_active_work": False},
            "workflow": {"workflow_id": "unknown", "stages": []},
        }

        signals = compute_signals(snapshot, registry).signals

        self.assertEqual("STATE_FILES_MISSING", signals[0].signal_id)
        self.assertEqual("MISSING", signals[0].level)

    def test_active_work_with_idle_status_reports_state_divergence(self):
        registry = Registry(
            agents={"conductor": AgentContract("conductor")},
            workflows=["complex-bug"],
        )
        report = compute_signals(
            {
                "status": {
                    "work": None,
                    "work_state": "idle",
                    "workflow": None,
                    "stage": None,
                    "agent": {"id": None, "state": None},
                },
                "work": {"has_active_work": True, "goal": "fix it"},
                "workflow": {"workflow_id": "unknown", "stages": []},
            },
            registry,
        )
        signals = {signal.signal_id: signal for signal in report.signals}
        self.assertIn("STATE_DIVERGENCE", signals)
        self.assertEqual(signals["STATE_DIVERGENCE"].level, "INCONSISTENT")


if __name__ == "__main__":
    unittest.main()
