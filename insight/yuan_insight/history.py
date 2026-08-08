"""History：按 Work 组织，聚合 Work Observation Summary（方案 §42）。

Work Summary 由 Insight 生成，不属于 Yuan。Summary 长期保留；详细 Trace
默认保留最近 N 个 Work（可配置）。Compare Works 有价值但不是首批 MVP。
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class WorkSummary:
    work_id: str
    transition_count: int = 0
    first_observed_at: str | None = None
    last_observed_at: str | None = None
    stages: list[str] = field(default_factory=list)
    agents: list[str] = field(default_factory=list)
    skills: list[str] = field(default_factory=list)
    files_changed: list[str] = field(default_factory=list)
    sessions: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "work_id": self.work_id,
            "transition_count": self.transition_count,
            "first_observed_at": self.first_observed_at,
            "last_observed_at": self.last_observed_at,
            "stages": self.stages,
            "agents": self.agents,
            "skills": self.skills,
            "files_changed": self.files_changed,
            "sessions": self.sessions,
        }


def _iter_transitions(trace_path: Path) -> list[dict[str, Any]]:
    transitions: list[dict[str, Any]] = []
    try:
        for line in trace_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                transitions.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    except (OSError, UnicodeError):
        return []
    return transitions


def summarize_trace(trace_path: Path) -> WorkSummary:
    """从单个 Work 的 JSONL Trace 聚合 Summary。"""
    work_id = trace_path.stem
    transitions = _iter_transitions(trace_path)
    summary = WorkSummary(work_id=work_id, transition_count=len(transitions))

    stages: list[str] = []
    agents: list[str] = []
    skills: list[str] = []
    files: list[str] = []
    sessions: list[str] = []

    for transition in transitions:
        observed_at = transition.get("observed_at")
        if observed_at:
            if summary.first_observed_at is None or observed_at < summary.first_observed_at:
                summary.first_observed_at = observed_at
            if summary.last_observed_at is None or observed_at > summary.last_observed_at:
                summary.last_observed_at = observed_at
        session_id = transition.get("session_id")
        if session_id and session_id not in sessions:
            sessions.append(session_id)
        for fact in transition.get("facts", []):
            field = fact.get("field", "")
            if field == "status.stage" and fact.get("to"):
                if fact["to"] not in stages:
                    stages.append(fact["to"])
            elif field == "status.agent.id" and fact.get("to"):
                if fact["to"] not in agents:
                    agents.append(fact["to"])
            elif field == "work.latest_result":
                # skills_applied 在 latest_result 文本里
                text = str(fact.get("to") or "")
                for line in text.splitlines():
                    stripped = line.strip()
                    if stripped.startswith("-"):
                        skills.append(stripped.lstrip("- ").strip())
            elif fact.get("kind") == "files_changed":
                files.extend(fact.get("sources_changed", []))

    summary.stages = stages
    summary.agents = agents
    summary.skills = sorted(set(skills))
    summary.files_changed = sorted(set(files))
    summary.sessions = sessions
    return summary


def list_work_summaries(insight_dir: Path, limit: int = 50) -> list[dict[str, Any]]:
    """列出全部归档 Work 的 Summary，按最后观察时间倒序。"""
    traces = insight_dir / "traces"
    if not traces.is_dir():
        return []
    archived = sorted(
        (path for path in traces.glob("*.jsonl") if path.name != "current.jsonl"),
        key=lambda path: path.stat().st_mtime,
        reverse=True,
    )
    summaries = [summarize_trace(path) for path in archived[:limit]]
    return [summary.to_dict() for summary in summaries]


def get_work_summary(insight_dir: Path, work_id: str) -> dict[str, Any] | None:
    """获取单个 Work 的 Summary（含完整 Trace）。"""
    traces = insight_dir / "traces"
    trace_path = traces / f"{work_id}.jsonl"
    if not trace_path.is_file():
        return None
    summary = summarize_trace(trace_path)
    result = summary.to_dict()
    result["trace"] = _iter_transitions(trace_path)
    return result
