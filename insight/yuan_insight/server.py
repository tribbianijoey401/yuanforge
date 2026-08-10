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
import sys
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from .footprint import extract_context_refs
from .history import get_work_summary, list_work_summaries
from .loader import build_snapshot
from .observer import ObservationService
from .registry import load_registry
from .signals.aggregate import compute_signals
from .signals.expected_observed import observed_from_snapshot, observed_from_trace


class InsightHandler(BaseHTTPRequestHandler):
    root: Path = Path(".")
    framework_root: Path = Path(".")
    source_web_dir = Path(__file__).parent.parent / "web"
    web_dir: Path = (
        source_web_dir
        if source_web_dir.is_dir()
        else Path(sys.prefix) / "yuan_insight_web"
    )

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
        observer = getattr(self.server, "observer", None)
        evidence = observer.evidence() if observer else None
        coverage = evidence.coverage if evidence else "UNKNOWN"
        transitions = evidence.transitions if evidence else []
        report = compute_signals(
            snapshot.to_dict(),
            registry,
            coverage=coverage,
            transitions=transitions,
        )
        observed = observed_from_trace(transitions)
        current = observed_from_snapshot(snapshot.to_dict())
        for agent_id in current.observed_ids:
            if agent_id not in observed.observed_ids:
                observed.observed_ids.append(agent_id)
        footprint = extract_context_refs(snapshot.to_dict().get("work", {}), self.root)
        return {
            "observed_at": snapshot.observed_at,
            "snapshot": snapshot.to_dict(),
            "coverage": report.coverage,
            "signals": report.to_dict()["signals"],
            "observation": {
                "session_id": evidence.session_id if evidence else None,
                "mode": evidence.mode if evidence else "unknown",
                "current_work_id": evidence.current_work_id if evidence else None,
                "agents": observed.observed_ids,
                "skills": observed.reported_skills,
                "gaps": evidence.gaps if evidence else [],
            },
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
                "agent_skills": {
                    agent_id: {
                        "required": contract.required_skills,
                        "recommended": contract.recommended_skills,
                        "conditional": contract.conditional_skills,
                    }
                    for agent_id, contract in sorted(registry.agents.items())
                },
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
            web_root = self.web_dir.resolve()
            candidate = (web_root / relative).resolve()
            try:
                candidate.relative_to(web_root)
            except ValueError:
                self.send_error(404)
                return
            self._send_file(candidate)
            return
        self.send_error(404)

    def log_message(self, format: str, *args) -> None:  # noqa: A002
        # 静默访问日志，避免刷屏
        pass


class InsightHTTPServer(ThreadingHTTPServer):
    observer: ObservationService | None = None

    def server_close(self) -> None:
        if self.observer:
            self.observer.stop()
        super().server_close()


def serve(
    project_root: Path,
    port: int = 8765,
    host: str = "127.0.0.1",
    poll_interval: float = 0.1,
    debounce_window: float = 0.05,
    observe: bool = True,
) -> ThreadingHTTPServer:
    """启动 Dashboard Server（阻塞）。"""
    project_root = project_root.resolve()
    framework_root = project_root / ".yuan" / "framework"
    if not framework_root.is_dir():
        framework_root = project_root / "framework"

    InsightHandler.root = project_root
    InsightHandler.framework_root = framework_root
    server = InsightHTTPServer((host, port), InsightHandler)
    if observe:
        server.observer = ObservationService(
            project_root,
            poll_interval=poll_interval,
            debounce_window=debounce_window,
        )
        server.observer.start_background()
    actual_port = server.server_address[1]
    print(f"Yuan Insight Dashboard: http://{host}:{actual_port}")
    print(f"Observing: {project_root}")
    print("Ctrl+C 停止；Dashboard 关闭不影响 Yuan。")
    return server
