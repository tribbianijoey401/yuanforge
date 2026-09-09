"""Observation Session / Coverage / Gap 与 JSONL Trace 落盘。

方案 §30：yuan observe 启动时生成 Baseline Snapshot，明确启动前历史 not observed；
中途挂掉再启动记录 observation gap；Trace 只保存 What Changed。
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

from .loader import Snapshot


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def ensure_insight_dir(root: Path) -> Path:
    """创建 .yuan/insight/ 目录（Observation Data，不属于 Yuan Authority）。"""
    directory = root / ".yuan" / "insight"
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def start_session(root: Path, baseline: Snapshot) -> tuple[Path, str]:
    """创建 Observation Session，写入 Baseline Snapshot。"""
    insight_dir = ensure_insight_dir(root)
    session_id = (
        f"OBS-{_utc_now()[:19].replace('-', '').replace(':', '')}-"
        f"{uuid.uuid4().hex[:8]}"
    )
    session_path = insight_dir / "sessions"
    session_path.mkdir(parents=True, exist_ok=True)
    record = {
        "session_id": session_id,
        "started_at": baseline.observed_at,
        "baseline_fingerprint": baseline.fingerprint(),
        "status": "active",
    }
    (session_path / f"{session_id}.json").write_text(
        json.dumps(record, ensure_ascii=False, indent=1), encoding="utf-8"
    )
    return insight_dir, session_id


def update_session(
    insight_dir: Path,
    session_id: str,
    **changes: object,
) -> None:
    """更新 Observation Session metadata，不触碰 Yuan Authority。"""
    path = insight_dir / "sessions" / f"{session_id}.json"
    try:
        record = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        record = {"session_id": session_id}
    record.update(changes)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(record, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def append_transition(
    insight_dir: Path,
    transition: dict,
) -> Path:
    """把 Transition 追加到当前 focused Work 的 JSONL Trace。"""
    traces = insight_dir / "traces"
    traces.mkdir(parents=True, exist_ok=True)
    trace_path = traces / "current.jsonl"
    with trace_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(transition, ensure_ascii=False) + "\n")
    return trace_path


def archive_trace(
    insight_dir: Path,
    work_id: str | None,
    coverage: str = "UNKNOWN",
    gaps: list[dict] | None = None,
    summarize: bool = True,
) -> Path | None:
    """把 current.jsonl 旋转到 traces/<work>.jsonl。

    Multi-Work 下 focus switch 只是执行上下文切换，不代表 Work completion；调用方
    此时传 ``summarize=False``，只保存该 Work 已观察到的 Trace。只有 canonical Work
    被 Distill/移除时才 ``summarize=True`` 并写长期 Work Summary。

    返回归档路径；无当前 Trace 或 work_id 为空时返回 None。
    """
    if not work_id:
        return None
    traces = insight_dir / "traces"
    current = traces / "current.jsonl"
    if not current.is_file() or current.stat().st_size == 0:
        return None
    archive_path = traces / f"{work_id}.jsonl"
    if archive_path.exists():
        with archive_path.open("ab") as destination, current.open("rb") as source:
            destination.write(source.read())
        current.unlink()
    else:
        current.rename(archive_path)

    if summarize:
        from .history import write_work_summary

        write_work_summary(
            insight_dir,
            work_id,
            archive_path,
            coverage=coverage,
            gaps=gaps,
        )
    return archive_path


def prune_traces(insight_dir: Path, keep: int = 50) -> list[str]:
    """Trace retention：只保留最近 N 个 Work 的归档 Trace（方案 §42.1）。"""
    traces = insight_dir / "traces"
    if not traces.is_dir():
        return []
    archived = sorted(
        (path for path in traces.glob("*.jsonl") if path.name != "current.jsonl"),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )
    removed: list[str] = []
    for stale in archived[keep:]:
        stale.unlink()
        removed.append(stale.name)
    return removed


def record_gap(insight_dir: Path, session_id: str, gap_start: str, gap_end: str) -> Path:
    """记录 Observation Gap（Sidecar 中断再恢复）。"""
    gaps = insight_dir / "gaps"
    gaps.mkdir(parents=True, exist_ok=True)
    gap_path = gaps / f"{session_id}.jsonl"
    with gap_path.open("a", encoding="utf-8") as handle:
        handle.write(
            json.dumps(
                {"session_id": session_id, "gap_start": gap_start, "gap_end": gap_end},
                ensure_ascii=False,
            )
            + "\n"
        )
    return gap_path
