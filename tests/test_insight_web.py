"""Yuan Insight Phase 5：Dashboard Server 测试。"""

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

from yuan_insight.server import serve  # noqa: E402


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

    def test_index_serves_dashboard(self):
        with urlopen(f"http://127.0.0.1:{self.port}/", timeout=5) as response:
            html = response.read().decode("utf-8")
        self.assertIn("Yuan Insight", html)
        self.assertIn("app.js", html)

    def test_static_app_js_served(self):
        with urlopen(f"http://127.0.0.1:{self.port}/static/app.js", timeout=5) as response:
            js = response.read().decode("utf-8")
        self.assertIn("api/state", js)

    def test_unknown_path_404(self):
        import urllib.error

        with self.assertRaises(urllib.error.HTTPError):
            urlopen(f"http://127.0.0.1:{self.port}/nope", timeout=5)


if __name__ == "__main__":
    unittest.main()
