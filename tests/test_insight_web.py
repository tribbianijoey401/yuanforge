"""Yuan Insight Phase 5：Dashboard Server 测试。"""

from __future__ import annotations

import json
import sys
import tempfile
import threading
import time
import unittest
from unittest.mock import patch
from pathlib import Path
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "insight"))

from yuan_insight.server import serve  # noqa: E402
from yuan_insight.cli import main as insight_main  # noqa: E402


def make_project(tmp: Path) -> Path:
    root = tmp / "project"
    (root / "docs").mkdir(parents=True)
    # 复用真实 Framework（agents/skills/workflows 完整）
    import shutil

    shutil.copytree(ROOT / "framework", root / "framework")
    (root / "docs" / "STATUS.md").write_text(
        """---
work: BUG-010
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
修复中
""",
        encoding="utf-8",
    )
    (root / "docs" / "WORK.md").write_text(
        """# Active Work

## Goal

修复 BUG-010
""",
        encoding="utf-8",
    )
    return root


class ServerTests(unittest.TestCase):
    def test_missing_state_is_rendered_as_unavailable_not_idle(self):
        app = (ROOT / "insight" / "web" / "app.js").read_text(encoding="utf-8")
        self.assertIn("STATE UNAVAILABLE", app)
        self.assertIn('class="state unknown">UNAVAILABLE', app)

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.project = make_project(Path(self.temp.name))
        self.server = serve(self.project, port=0)  # port 0 = 随机端口
        self.port = self.server.server_address[1]
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    def tearDown(self):
        self.server.shutdown()
        self.server.server_close()
        self.temp.cleanup()

    def test_api_state_returns_snapshot_and_signals(self):
        with urlopen(f"http://127.0.0.1:{self.port}/api/state", timeout=5) as response:
            data = json.loads(response.read().decode("utf-8"))
        self.assertIn("snapshot", data)
        self.assertIn("signals", data)
        self.assertIn("footprint", data)
        self.assertIn("registry", data)
        self.assertEqual(data["snapshot"]["status"]["work"], "BUG-010")
        self.assertIn("backend-dev", data["registry"]["agents"])
        self.assertEqual(data["coverage"], "PARTIAL")
        self.assertTrue(data["observation"]["mode"].startswith("native-") or data["observation"]["mode"] == "polling-fallback")

    def test_dashboard_observer_records_transition(self):
        (self.project / "docs" / "STATUS.md").write_text(
            """---
work: BUG-010
work_state: active
workflow: complex-bug
stage: regression
agent:
  id: tester
  state: active
quality:
  test: active
  review: pending
---

# Current Situation
回归中
""",
            encoding="utf-8",
        )
        deadline = time.time() + 3
        trace = self.project / ".yuan" / "insight" / "traces" / "current.jsonl"
        while time.time() < deadline and not trace.is_file():
            time.sleep(0.05)
        self.assertTrue(trace.is_file())
        self.assertIn("status.agent.id", trace.read_text(encoding="utf-8"))

    def test_index_serves_dashboard(self):
        with urlopen(f"http://127.0.0.1:{self.port}/", timeout=5) as response:
            html = response.read().decode("utf-8")
        self.assertIn("Yuan Insight", html)
        self.assertIn("app.js", html)

    def test_static_app_js_served(self):
        with urlopen(f"http://127.0.0.1:{self.port}/static/app.js", timeout=5) as response:
            js = response.read().decode("utf-8")
        self.assertIn("api/state", js)

    def test_dashboard_exposes_work_fallback_for_incomplete_status(self):
        with urlopen(f"http://127.0.0.1:{self.port}/", timeout=5) as response:
            html = response.read().decode("utf-8")
        with urlopen(f"http://127.0.0.1:{self.port}/static/app.js", timeout=5) as response:
            js = response.read().decode("utf-8")

        self.assertIn('id="work-warning"', html)
        self.assertIn('id="work-details"', html)
        self.assertIn("work.goal", js)
        self.assertIn("STATUS checkpoint incomplete", js)
        self.assertIn("Current Agent: UNKNOWN", js)

    def test_unknown_path_404(self):
        import urllib.error

        with self.assertRaises(urllib.error.HTTPError):
            urlopen(f"http://127.0.0.1:{self.port}/nope", timeout=5)

    def test_static_path_cannot_escape_web_root(self):
        import urllib.error

        with self.assertRaises(urllib.error.HTTPError) as raised:
            urlopen(
                f"http://127.0.0.1:{self.port}/static/../../README.md",
                timeout=5,
            )
        self.assertEqual(raised.exception.code, 404)


class WebCliTests(unittest.TestCase):
    def test_web_command_always_closes_server(self):
        class FakeServer:
            closed = False

            def serve_forever(self):
                return None

            def server_close(self):
                self.closed = True

        server = FakeServer()
        with patch("yuan_insight.server.serve", return_value=server):
            result = insight_main([".", "--web"])
        self.assertEqual(result, 0)
        self.assertTrue(server.closed)


if __name__ == "__main__":
    unittest.main()
