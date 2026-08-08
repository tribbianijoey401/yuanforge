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
    session_id = f"OBS-{_utc_now()[:19].replace('-', '').replace(':', '')}"
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


def append_transition(
    insight_dir: Path,
    transition: dict,
) -> Path:
    """把 Transition 追加到当前 Work 的 JSONL Trace。"""
    traces = insight_dir / "traces"
    traces.mkdir(parents=True, exist_ok=True)
    trace_path = traces / "current.jsonl"
    with trace_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(transition, ensure_ascii=False) + "\n")
    return trace_path


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
