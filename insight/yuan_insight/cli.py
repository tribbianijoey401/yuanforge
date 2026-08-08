"""yuan-observe 入口。

用法：
  yuan-observe <project-root>            # 连续观察（watch 模式，Ctrl+C 退出）
  yuan-observe <project-root> --once     # 一次性生成 Baseline Snapshot 后退出
  yuan-observe <project-root> --diff     # 输出 Baseline 到当前状态的 Facts（不落盘）
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

from .diff import diff_snapshots, to_transition
from .loader import build_snapshot
from .registry import load_registry
from .signals.aggregate import compute_signals
from .trace import (
    append_transition,
    archive_trace,
    ensure_insight_dir,
    prune_traces,
    record_gap,
    start_session,
)
from .watcher import DebouncedWatcher


def _utc_now() -> str:
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _emit(value) -> None:  # type: ignore[no-untyped-def]
    sys.stdout.write(json.dumps(value, ensure_ascii=False) + "\n")


def _run_once(root: Path) -> int:
    baseline = build_snapshot(root, _utc_now())
    _emit({"status": "OBSERVED", "mode": "once", "snapshot": baseline.fingerprint()})
    _emit({"status": "WORK", "work": baseline.work})
    _emit({"status": "STATUS", "status": baseline.status})
    _emit({"status": "WORKFLOW_EXPECTED", "workflow": baseline.workflow})
    return 0


def _run_signals(root: Path) -> int:
    snapshot = build_snapshot(root, _utc_now())
    framework_root = root / ".yuan" / "framework"
    if not framework_root.is_dir():
        framework_root = root / "framework"
    registry = load_registry(framework_root)
    report = compute_signals(snapshot.to_dict(), registry)
    _emit(report.to_dict())
    return 0


def _run_diff(root: Path) -> int:
    before = build_snapshot(root, _utc_now())
    time.sleep(0.1)
    after = build_snapshot(root, _utc_now())
    facts = diff_snapshots(before, after)
    _emit({"status": "FACTS", "count": len(facts), "facts": facts})
    return 0


def _run_watch(root: Path, poll_interval: float, debounce: float) -> int:
    insight_dir = ensure_insight_dir(root)
    baseline = build_snapshot(root, _utc_now())
    insight_dir, session_id = start_session(root, baseline)
    _emit({"status": "OBSERVING", "session_id": session_id, "root": str(root.resolve())})
    _emit({"status": "BASELINE", "fingerprint": baseline.fingerprint()})

    watcher = DebouncedWatcher(root, poll_interval=poll_interval, debounce_window=debounce)
    previous = baseline
    transition_index = 0
    previous_work_id: str | None = None
    try:
        while True:
            event = watcher.tick()
            if event is None:
                time.sleep(poll_interval)
                continue
            # Work 变化时归档当前 Trace（方案 §42/§43）
            current_work_id = (event.snapshot.work or {}).get("has_active_work") and (event.snapshot.status or {}).get("work")
            if current_work_id and current_work_id != previous_work_id:
                archived = archive_trace(insight_dir, previous_work_id)
                if archived:
                    _emit({"status": "ARCHIVED", "work": previous_work_id, "path": str(archived)})
                pruned = prune_traces(insight_dir, keep=50)
                if pruned:
                    _emit({"status": "PRUNED", "removed": pruned})
                previous_work_id = current_work_id
            transition_index += 1
            facts = diff_snapshots(previous, event.snapshot)
            transition = to_transition(
                transition_id=f"T-{transition_index:04d}",
                session_id=session_id,
                observed_at=event.snapshot.observed_at,
                before=previous,
                after=event.snapshot,
                facts=facts,
            )
            trace_path = append_transition(insight_dir, transition)
            _emit({"status": "TRANSITION", "transition": transition})
            _emit({"status": "TRACE", "path": str(trace_path)})
            previous = event.snapshot
    except KeyboardInterrupt:
        _emit({"status": "STOPPED", "session_id": session_id})
        return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Yuan Insight — 只读旁路观察 Yuan 语义状态")
    parser.add_argument("root", type=Path, help="Project 根目录")
    parser.add_argument("--once", action="store_true", help="生成 Baseline Snapshot 后退出")
    parser.add_argument("--diff", action="store_true", help="输出 Baseline 到当前状态的 Facts")
    parser.add_argument("--signals", action="store_true", help="计算并输出 Signals（Expected vs Observed）")
    parser.add_argument("--web", action="store_true", help="启动 Dashboard Server（/api/state + 静态 UI）")
    parser.add_argument("--port", type=int, default=8765, help="Dashboard 端口（默认 8765）")
    parser.add_argument("--poll", type=float, default=0.5, help="轮询间隔秒数（默认 0.5）")
    parser.add_argument("--debounce", type=float, default=0.4, help="debounce 窗口秒数（默认 0.4）")
    args = parser.parse_args(argv)
    try:
        if args.once:
            return _run_once(args.root)
        if args.diff:
            return _run_diff(args.root)
        if args.signals:
            return _run_signals(args.root)
        if args.web:
            from .server import serve

            server = serve(args.root, port=args.port)
            try:
                server.serve_forever()
            except KeyboardInterrupt:
                return 0
        return _run_watch(args.root, args.poll, args.debounce)
    except KeyboardInterrupt:
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
