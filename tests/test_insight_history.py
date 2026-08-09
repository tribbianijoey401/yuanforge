"""Yuan Insight Phase 6：History 测试。"""

from __future__ import annotations

import json
import sys
import tempfile
import threading
import unittest
from pathlib import Path
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "insight"))

from yuan_insight.history import (  # noqa: E402
    get_work_summary,
    list_work_summaries,
    summarize_trace,
    write_work_summary,
)
from yuan_insight.server import serve  # noqa: E402
from yuan_insight.trace import (  # noqa: E402
    append_transition,
    archive_trace,
    ensure_insight_dir,
    prune_traces,
)


def make_transition(transition_id: str, session: str, work: str, stage: str, agent: str) -> dict:
    return {
        "id": transition_id,
        "session_id": session,
        "observed_at": f"2026-08-09T00:00:{transition_id[-2:]}Z",
        "sources_changed": ["docs/STATUS.md", "docs/WORK.md"],
        "before_hash": "a",
        "after_hash": "b",
        "facts": [
            {"kind": "field_changed", "field": "status.stage", "from": None, "to": stage},
            {"kind": "field_changed", "field": "status.agent.id", "from": None, "to": agent},
            {"kind": "field_changed", "field": "work.latest_result", "from": None, "to": "outcome: completed\nskills_applied:\n- systematic-debugging"},
            {"kind": "files_changed", "sources_changed": ["docs/STATUS.md", "docs/WORK.md"]},
        ],
    }


class HistoryTests(unittest.TestCase):
    def test_summarize_trace_aggregates_work(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            insight_dir = ensure_insight_dir(root)
            trace_path = insight_dir / "traces" / "BUG-100.jsonl"
            trace_path.parent.mkdir(parents=True)
            with trace_path.open("w", encoding="utf-8") as handle:
                handle.write(json.dumps(make_transition("T-0001", "OBS-1", "BUG-100", "implement", "backend-dev"), ensure_ascii=False) + "\n")
                handle.write(json.dumps(make_transition("T-0002", "OBS-1", "BUG-100", "regression", "tester"), ensure_ascii=False) + "\n")
            summary = summarize_trace(trace_path)
            self.assertEqual(summary.work_id, "BUG-100")
            self.assertEqual(summary.transition_count, 2)
            self.assertEqual(summary.stages, ["implement", "regression"])
            self.assertEqual(summary.agents, ["backend-dev", "tester"])
            self.assertEqual(summary.skills, ["systematic-debugging"])
            self.assertIn("docs/STATUS.md", summary.files_changed)
            self.assertEqual(summary.sessions, ["OBS-1"])

    def test_list_and_get_work_summaries(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            insight_dir = ensure_insight_dir(root)
            trace_path = insight_dir / "traces" / "BUG-200.jsonl"
            trace_path.parent.mkdir(parents=True)
            trace_path.write_text(
                json.dumps(make_transition("T-0001", "OBS-2", "BUG-200", "implement", "backend-dev"), ensure_ascii=False)
                + "\n",
                encoding="utf-8",
            )
            works = list_work_summaries(insight_dir)
            self.assertEqual(len(works), 1)
            self.assertEqual(works[0]["work_id"], "BUG-200")
            detail = get_work_summary(insight_dir, "BUG-200")
            self.assertIn("trace", detail)
            self.assertEqual(len(detail["trace"]), 1)
            self.assertIsNone(get_work_summary(insight_dir, "NOPE"))

    def test_completion_transition_keeps_cleared_agent_and_skill(self):
        with tempfile.TemporaryDirectory() as temporary:
            trace_path = Path(temporary) / "BUG-DONE.jsonl"
            trace_path.write_text(
                json.dumps(
                    {
                        "id": "T-0001",
                        "session_id": "OBS-1",
                        "observed_at": "2026-08-09T00:00:00Z",
                        "facts": [
                            {
                                "field": "status.agent.id",
                                "from": "tester",
                                "to": None,
                            },
                            {
                                "field": "work.latest_result",
                                "from": "skills_applied:\n- test-driven-development",
                                "to": None,
                            },
                        ],
                    },
                    ensure_ascii=False,
                )
                + "\n",
                encoding="utf-8",
            )
            summary = summarize_trace(trace_path)
            self.assertEqual(summary.agents, ["tester"])
            self.assertEqual(summary.skills, ["test-driven-development"])


class TraceArchiveTests(unittest.TestCase):
    def test_archive_and_prune(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            insight_dir = ensure_insight_dir(root)
            trace_path = insight_dir / "traces" / "current.jsonl"
            trace_path.parent.mkdir(parents=True)
            trace_path.write_text('{"id":"T-1","facts":[]}\n', encoding="utf-8")
            archived = archive_trace(insight_dir, "BUG-300")
            self.assertIsNotNone(archived)
            self.assertTrue((insight_dir / "traces" / "BUG-300.jsonl").is_file())
            self.assertFalse(trace_path.exists())
            self.assertTrue((insight_dir / "summaries" / "BUG-300.json").is_file())
            # prune 保留 keep 个
            for i in range(5):
                (insight_dir / "traces" / f"W-{i}.jsonl").write_text('{"id":"T"}\n', encoding="utf-8")
            removed = prune_traces(insight_dir, keep=2)
            remaining = list((insight_dir / "traces").glob("*.jsonl"))
            self.assertEqual(len(removed), 4)
            self.assertEqual(len(remaining), 2)
            # Summary 是长期历史，不随 Trace retention 被删除。
            self.assertTrue((insight_dir / "summaries" / "BUG-300.json").is_file())

    def test_summary_remains_readable_after_trace_pruned(self):
        with tempfile.TemporaryDirectory() as temporary:
            insight_dir = ensure_insight_dir(Path(temporary))
            trace_path = insight_dir / "traces" / "BUG-KEEP.jsonl"
            trace_path.parent.mkdir(parents=True)
            trace_path.write_text(
                json.dumps(
                    make_transition("T-0001", "OBS-1", "BUG-KEEP", "review", "tester"),
                    ensure_ascii=False,
                )
                + "\n",
                encoding="utf-8",
            )
            write_work_summary(insight_dir, "BUG-KEEP", trace_path)
            trace_path.unlink()
            summary = get_work_summary(insight_dir, "BUG-KEEP")
            self.assertIsNotNone(summary)
            self.assertFalse(summary["trace_available"])
            self.assertEqual(summary["agents"], ["tester"])

    def test_archive_requires_work_id(self):
        with tempfile.TemporaryDirectory() as temporary:
            insight_dir = ensure_insight_dir(Path(temporary))
            self.assertIsNone(archive_trace(insight_dir, None))


class HistoryApiTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.project = Path(self.temp.name) / "project"
        (self.project / "docs").mkdir(parents=True)
        (self.project / ".yuan" / "insight" / "traces").mkdir(parents=True)
        trace = self.project / ".yuan" / "insight" / "traces" / "BUG-400.jsonl"
        trace.write_text(
            json.dumps(make_transition("T-0001", "OBS-9", "BUG-400", "implement", "backend-dev"), ensure_ascii=False)
            + "\n",
            encoding="utf-8",
        )
        self.server = serve(self.project, port=0)
        self.port = self.server.server_address[1]
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.temp.cleanup()

    def test_history_api(self):
        with urlopen(f"http://127.0.0.1:{self.port}/api/history", timeout=5) as response:
            data = json.loads(response.read().decode("utf-8"))
        self.assertEqual(len(data["works"]), 1)
        self.assertEqual(data["works"][0]["work_id"], "BUG-400")

    def test_work_detail_api(self):
        with urlopen(f"http://127.0.0.1:{self.port}/api/history/BUG-400", timeout=5) as response:
            data = json.loads(response.read().decode("utf-8"))
        self.assertEqual(data["work_id"], "BUG-400")
        self.assertIn("trace", data)


if __name__ == "__main__":
    unittest.main()
