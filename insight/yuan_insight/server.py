"""Dashboard HTTP Server — 标准库实现，零第三方依赖。

提供：
- GET /api/state  → { snapshot, signals, footprint, coverage, observed_at }
- GET /          → 静态 Dashboard（web/ 目录）
- GET /static/*  → 静态资源

方案 §44.2：轻量 /api/state polling（不需要 WebSocket）；前端技术栈不成为
Yuan Core 依赖。Insight 是可选 Sidecar，server 关闭不影响 Yuan。
"""

from __future__ import annotations

import json
import mimetypes
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from .footprint import extract_context_refs
from .history import get_work_summary, list_work_summaries
from .loader import build_snapshot
from .registry import load_registry
from .signals.aggregate import compute_signals


class InsightHandler(BaseHTTPRequestHandler):
    root: Path = Path(".")
    framework_root: Path = Path(".")
    web_dir: Path = Path(__file__).parent.parent / "web"

    def _send_json(self, value: dict) -> None:
        payload = json.dumps(value, ensure_ascii=False).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(payload)

    def _send_file(self, path: Path) -> None:
        if not path.is_file():
            self.send_error(404)
            return
        payload = path.read_bytes()
        content_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def _current_state(self) -> dict:
        snapshot = build_snapshot(self.root, f"{time.time():.3f}")
        registry = load_registry(self.framework_root)
        report = compute_signals(snapshot.to_dict(), registry)
        footprint = extract_context_refs(snapshot.to_dict().get("work", {}), self.root)
        return {
            "observed_at": snapshot.observed_at,
            "snapshot": snapshot.to_dict(),
            "coverage": report.coverage,
            "signals": report.to_dict()["signals"],
            "footprint": {
                "references": footprint.references,
                "documents": footprint.documents,
                "sections": footprint.sections,
                "characters": footprint.characters,
                "bytes": footprint.bytes,
                "memory_refs": footprint.memory_refs,
                "coverage": footprint.coverage,
                "per_document": footprint.per_document,
            },
            "registry": {
                "agents": sorted(registry.agents),
                "skills": sorted(registry.skills),
                "workflows": sorted(registry.workflows),
            },
        }

    def do_GET(self) -> None:  # noqa: N802
        if self.path == "/api/state":
            try:
                self._send_json(self._current_state())
            except Exception as exc:  # Insight 失败不阻塞 Dashboard 显示错误
                self._send_json({"error": str(exc)})
            return
        if self.path == "/api/history":
            insight_dir = self.root / ".yuan" / "insight"
            self._send_json({"works": list_work_summaries(insight_dir)})
            return
        if self.path.startswith("/api/history/"):
            work_id = self.path.removeprefix("/api/history/")
            insight_dir = self.root / ".yuan" / "insight"
            summary = get_work_summary(insight_dir, work_id)
            if summary is None:
                self.send_error(404)
                return
            self._send_json(summary)
            return
        if self.path == "/" or self.path == "/index.html":
            self._send_file(self.web_dir / "index.html")
            return
        if self.path.startswith("/static/"):
            relative = self.path.removeprefix("/static/")
            self._send_file((self.web_dir / relative).resolve())
            return
        self.send_error(404)

    def log_message(self, format: str, *args) -> None:  # noqa: A002
        # 静默访问日志，避免刷屏
        pass


def serve(project_root: Path, port: int = 8765, host: str = "127.0.0.1") -> ThreadingHTTPServer:
    """启动 Dashboard Server（阻塞）。"""
    project_root = project_root.resolve()
    framework_root = project_root / ".yuan" / "framework"
    if not framework_root.is_dir():
        framework_root = project_root / "framework"

    InsightHandler.root = project_root
    InsightHandler.framework_root = framework_root
    server = ThreadingHTTPServer((host, port), InsightHandler)
    print(f"Yuan Insight Dashboard: http://{host}:{port}")
    print(f"Observing: {project_root}")
    print("Ctrl+C 停止；Dashboard 关闭不影响 Yuan。")
    return server
