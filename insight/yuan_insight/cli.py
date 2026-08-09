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

from .diff import diff_snapshots
from .loader import build_snapshot
from .observer import ObservationService, load_observation_evidence
from .registry import load_registry
from .signals.aggregate import compute_signals


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
    evidence = load_observation_evidence(root)
    report = compute_signals(
        snapshot.to_dict(),
        registry,
        coverage=evidence.coverage,
        transitions=evidence.transitions,
    )
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
    observer = ObservationService(
        root,
        poll_interval=poll_interval,
        debounce_window=debounce,
    )
    baseline = observer.start()
    _emit(
        {
            "status": "OBSERVING",
            "session_id": observer.session_id,
            "coverage": observer.coverage,
            "root": str(root.resolve()),
        }
    )
    _emit({"status": "BASELINE", "fingerprint": baseline.fingerprint()})
    try:
        while True:
            update = observer.poll_once()
            if update is None:
                time.sleep(poll_interval)
                continue
            if update.transition:
                _emit({"status": "TRANSITION", "transition": update.transition})
            if update.trace_path:
                _emit({"status": "TRACE", "path": str(update.trace_path)})
            if update.archived_path:
                _emit({"status": "ARCHIVED", "path": str(update.archived_path)})
            if update.pruned:
                _emit({"status": "PRUNED", "removed": update.pruned})
    except KeyboardInterrupt:
        observer.stop()
        _emit({"status": "STOPPED", "session_id": observer.session_id})
        return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Yuan Insight — 只读旁路观察 Yuan 语义状态")
    parser.add_argument("root", nargs="?", type=Path, default=Path("."), help="Project 根目录")
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

            server = serve(
                args.root,
                port=args.port,
                poll_interval=args.poll,
                debounce_window=args.debounce,
            )
            try:
                server.serve_forever()
            except KeyboardInterrupt:
                return 0
            finally:
                server.server_close()
            return 0
        return _run_watch(args.root, args.poll, args.debounce)
    except KeyboardInterrupt:
        return 0


def yuan_main(argv: list[str] | None = None) -> int:
    """`yuan observe` 兼容入口；不建立 Yuan Core Runtime。"""
    values = list(sys.argv[1:] if argv is None else argv)
    if not values or values[0] != "observe":
        sys.stderr.write("usage: yuan observe [project-root] [--web|--once|--signals]\n")
        return 2
    return main(values[1:])


if __name__ == "__main__":
    raise SystemExit(main())
