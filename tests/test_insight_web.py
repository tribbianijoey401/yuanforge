"""Yuan Insight Phase 5：Dashboard Server 测试。"""

from __future__ import annotations

import json
import re
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


def css_token(css: str, name: str) -> str:
    match = re.search(rf"{re.escape(name)}:\s*(#[0-9a-fA-F]{{6}})\s*;", css)
    if not match:
        raise AssertionError(f"missing six-digit color token: {name}")
    return match.group(1)


def contrast_ratio(foreground: str, background: str) -> float:
    def luminance(value: str) -> float:
        channels = [int(value[index : index + 2], 16) / 255 for index in (1, 3, 5)]
        linear = [
            channel / 12.92
            if channel <= 0.04045
            else ((channel + 0.055) / 1.055) ** 2.4
            for channel in channels
        ]
        return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2]

    lighter, darker = sorted(
        (luminance(foreground), luminance(background)), reverse=True
    )
    return (lighter + 0.05) / (darker + 0.05)


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
    def test_dashboard_living_canvas_places_operational_facts_first(self):
        html = (ROOT / "insight" / "web" / "index.html").read_text(encoding="utf-8")
        self.assertIn('name="color-scheme" content="light"', html)
        self.assertIn('class="status-ribbon"', html)
        self.assertIn('id="ribbon-work-state"', html)
        self.assertIn('id="ribbon-agent"', html)
        self.assertIn('id="ribbon-coverage"', html)
        self.assertIn('id="ribbon-source-health"', html)
        self.assertIn('class="above-fold"', html)
        self.assertIn('class="primary-grid"', html)
        self.assertIn('class="operational-grid"', html)
        self.assertIn('id="critical-signals"', html)
        self.assertLess(html.index('id="execution-rail"'), html.index('id="work-focus"'))
        self.assertLess(html.index('id="agent-matrix-panel"'), html.index('id="work-focus"'))
        self.assertLess(html.index('id="skill-matrix-panel"'), html.index('id="work-focus"'))
        self.assertLess(html.index('id="execution-rail"'), html.index('id="agent-matrix-panel"'))
        self.assertLess(html.index('id="agent-matrix-panel"'), html.index('id="skill-matrix-panel"'))
        self.assertLess(html.index('id="skill-matrix-panel"'), html.index('id="critical-signal-panel"'))
        self.assertLess(html.index('id="critical-signal-panel"'), html.index('id="work-focus"'))

    def test_dashboard_workflow_and_nodes_expose_state_semantics(self):
        app = (ROOT / "insight" / "web" / "app.js").read_text(encoding="utf-8")
        self.assertIn('"aria-current": "step"', app)
        self.assertIn('className: "stage-state"', app)
        self.assertIn("sortAgentEntries", app)
        self.assertIn("sortSkillEntries", app)
        self.assertIn("summary-tile", app)
        self.assertIn("critical-signals", app)
        self.assertIn("MAX_VISIBLE_AGENTS", app)
        self.assertIn("MAX_VISIBLE_SKILLS", app)

    def test_dashboard_motion_is_change_driven_and_reduced_motion_safe(self):
        app = (ROOT / "insight" / "web" / "app.js").read_text(encoding="utf-8")
        styles = (ROOT / "insight" / "web" / "styles.css").read_text(encoding="utf-8")
        self.assertIn("entitySignatures", app)
        self.assertIn("animateEntityTransition", app)
        self.assertIn("stage-progressed", app)
        self.assertIn("just-loaded", app)
        self.assertIn("risk-entered", app)
        self.assertIn("prefers-reduced-motion: reduce", styles)
        self.assertIn("animation: none", styles)
        self.assertNotRegex(styles, r"(?i)\b(?:bounce|elastic)\b")
        self.assertNotIn("infinite", styles)
        self.assertNotIn("current-breathe", styles)
        self.assertIn(".stage-row.stage-progressed .stage.current .stage-node", styles)
        self.assertIn("stage-node-pulse", styles)

    def test_light_canvas_tokens_meet_small_text_contrast(self):
        tokens = (ROOT / "insight" / "web" / "tokens.css").read_text(encoding="utf-8")
        styles = (ROOT / "insight" / "web" / "styles.css").read_text(encoding="utf-8")
        self.assertEqual(css_token(tokens, "--color-canvas"), "#f7f7f3")
        contrast_pairs = [
            ("--color-text-faint", "--color-surface"),
            ("--color-active", "--color-active-subtle"),
            ("--color-completed", "--color-completed-subtle"),
            ("--color-waiting", "--color-waiting-subtle"),
            ("--color-partial", "--color-partial-subtle"),
            ("--color-risk", "--color-risk-subtle"),
            ("--color-unknown", "--color-unknown-subtle"),
        ]
        for foreground, background in contrast_pairs:
            with self.subTest(foreground=foreground, background=background):
                self.assertGreaterEqual(
                    contrast_ratio(css_token(tokens, foreground), css_token(tokens, background)),
                    4.5,
                )
        self.assertNotIn("0.5625rem", styles)

    def test_dashboard_has_required_responsive_breakpoints_and_no_page_overflow(self):
        styles = (ROOT / "insight" / "web" / "styles.css").read_text(encoding="utf-8")
        self.assertIn("@media (max-width: 73.6875rem)", styles)
        self.assertIn("@media (min-width: 45rem) and (max-width: 56.1875rem)", styles)
        self.assertIn("@media (max-width: 44.9375rem)", styles)
        self.assertIn("overflow-x: clip", styles)
        self.assertIn("grid-template-columns: repeat(8, minmax(0, 1fr))", styles)

    def test_all_non_monochrome_color_literals_live_in_tokens(self):
        tokens = (ROOT / "insight" / "web" / "tokens.css").read_text(encoding="utf-8")
        styles = (ROOT / "insight" / "web" / "styles.css").read_text(encoding="utf-8")
        self.assertIn("--color-active", tokens)
        self.assertIn("--color-completed", tokens)
        self.assertIn("--color-waiting", tokens)
        self.assertIn("--color-partial", tokens)
        self.assertIn("--color-risk", tokens)
        self.assertIn("--color-unknown", tokens)
        self.assertNotRegex(styles, r"#[0-9a-fA-F]{3,8}|rgba?\(|hsla?\(|oklch\(")

    def test_dashboard_uses_tokenized_control_room_assets(self):
        html = (ROOT / "insight" / "web" / "index.html").read_text(encoding="utf-8")
        css = (ROOT / "insight" / "web" / "tokens.css").read_text(encoding="utf-8")
        styles = (ROOT / "insight" / "web" / "styles.css").read_text(encoding="utf-8")
        self.assertIn('rel="stylesheet" href="/static/tokens.css"', html)
        self.assertIn('rel="stylesheet" href="/static/styles.css"', html)
        self.assertIn('href="#main-content"', html)
        self.assertIn('id="work-focus"', html)
        self.assertIn('id="signal-inbox"', html)
        self.assertIn('--color-', css)
        self.assertNotIn("<style>", html)
        self.assertNotRegex(styles, r"#[0-9a-fA-F]{3,8}")
        self.assertIn(".connection-error[hidden]", styles)
        self.assertRegex(
            styles,
            r"\.connection-error\[hidden\]\s*\{\s*display:\s*none",
        )

    def test_dashboard_signal_and_failure_recovery_are_accessible(self):
        app = (ROOT / "insight" / "web" / "app.js").read_text(encoding="utf-8")
        html = (ROOT / "insight" / "web" / "index.html").read_text(encoding="utf-8")
        self.assertIn('document.createElement("button")', app)
        self.assertIn('aria-expanded', app)
        self.assertIn("lastSuccessfulSnapshot", app)
        self.assertIn("retry-button", app)
        self.assertIn('role="alert"', html)
        self.assertIn("highlightChanged", app)

    def test_dashboard_preserves_signal_disclosure_and_allows_narrow_viewports(self):
        app = (ROOT / "insight" / "web" / "app.js").read_text(encoding="utf-8")
        styles = (ROOT / "insight" / "web" / "styles.css").read_text(encoding="utf-8")
        self.assertIn("expandedSignalIds", app)
        self.assertIn("signal.signal_id", app)
        self.assertIn("focusedSignalId", app)
        self.assertIn("restoredToggle.focus()", app)
        self.assertNotIn("min-width: 20rem", styles)
        self.assertNotIn("0.625rem", styles)

    def test_dashboard_polls_every_half_second(self):
        app = (ROOT / "insight" / "web" / "app.js").read_text(encoding="utf-8")
        self.assertIn("const POLL_MS = 500", app)
        self.assertIn("每 0.5s 刷新", app)

    def test_missing_state_is_rendered_as_unavailable_not_idle(self):
        app = (ROOT / "insight" / "web" / "app.js").read_text(encoding="utf-8")
        self.assertIn("STATE UNAVAILABLE", app)
        self.assertIn('class="state unknown">UNAVAILABLE', app)

    def test_unknown_stage_and_agent_remain_visible(self):
        app = (ROOT / "insight" / "web" / "app.js").read_text(encoding="utf-8")
        self.assertIn("UNKNOWN STAGE", app)
        self.assertIn("UNREGISTERED ACTOR", app)
        self.assertIn("agent.instance", app)

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
        self.assertEqual(data["snapshot"]["status"]["activity"], "specialist_execution")
        self.assertEqual(
            data["snapshot"]["status"]["agent"]["instance"], "frontend-fixer"
        )
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
