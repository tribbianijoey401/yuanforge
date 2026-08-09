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
    coverage: str = "UNKNOWN"
    gaps: list[dict[str, Any]] = field(default_factory=list)

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
            "coverage": self.coverage,
            "gaps": self.gaps,
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
        state = transition.get("state") or {}
        state_stage = state.get("stage")
        if state_stage and state_stage not in stages:
            stages.append(state_stage)
        state_agent = (state.get("agent") or {}).get("id")
        if state_agent and state_agent not in agents:
            agents.append(state_agent)
        for fact in transition.get("facts", []):
            field = fact.get("field", "")
            if field == "status.stage" and fact.get("to"):
                if fact["to"] not in stages:
                    stages.append(fact["to"])
            elif field == "status.agent.id":
                for value in (fact.get("from"), fact.get("to")):
                    if value and value not in agents:
                        agents.append(value)
            elif field == "work.latest_result":
                for value in (fact.get("from"), fact.get("to")):
                    skills.extend(_extract_skills_applied(str(value or "")))
            elif fact.get("kind") == "files_changed":
                files.extend(fact.get("sources_changed", []))

    summary.stages = stages
    summary.agents = agents
    summary.skills = sorted(set(skills))
    summary.files_changed = sorted(set(files))
    summary.sessions = sessions
    return summary


def _extract_skills_applied(text: str) -> list[str]:
    skills: list[str] = []
    capture = False
    for line in text.splitlines():
        stripped = line.strip()
        if "skills_applied" in stripped:
            capture = True
            inline = stripped.split(":", 1)[1].strip() if ":" in stripped else ""
            if inline:
                skills.extend(
                    item.strip().strip("'\"")
                    for item in inline.strip("[]").split(",")
                    if item.strip()
                )
            continue
        if capture and stripped.startswith("-"):
            skills.append(stripped.lstrip("- ").strip())
        elif capture and stripped:
            break
    return skills


def write_work_summary(
    insight_dir: Path,
    work_id: str,
    trace_path: Path,
    coverage: str = "UNKNOWN",
    gaps: list[dict[str, Any]] | None = None,
) -> Path:
    """生成长期 Work Observation Summary。

    Summary 与 Trace retention 解耦；删除旧 Trace 不会删除 Summary。
    """
    summary = summarize_trace(trace_path)
    summary.work_id = work_id
    summary.coverage = coverage
    summary.gaps = list(gaps or [])
    summaries = insight_dir / "summaries"
    summaries.mkdir(parents=True, exist_ok=True)
    destination = summaries / f"{work_id}.json"
    destination.write_text(
        json.dumps(summary.to_dict(), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return destination


def _read_summary(path: Path) -> dict[str, Any] | None:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        return None
    return value if isinstance(value, dict) else None


def list_work_summaries(insight_dir: Path, limit: int = 50) -> list[dict[str, Any]]:
    """列出全部归档 Work 的 Summary，按最后观察时间倒序。"""
    values: dict[str, dict[str, Any]] = {}
    summaries_dir = insight_dir / "summaries"
    if summaries_dir.is_dir():
        for path in summaries_dir.glob("*.json"):
            value = _read_summary(path)
            if value and value.get("work_id"):
                values[str(value["work_id"])] = value

    traces = insight_dir / "traces"
    if traces.is_dir():
        for path in traces.glob("*.jsonl"):
            if path.name == "current.jsonl" or path.stem in values:
                continue
            summary = summarize_trace(path).to_dict()
            values[path.stem] = summary

    ordered = sorted(
        values.values(),
        key=lambda value: str(value.get("last_observed_at") or ""),
        reverse=True,
    )
    return ordered[:limit]


def get_work_summary(insight_dir: Path, work_id: str) -> dict[str, Any] | None:
    """获取单个 Work 的 Summary（含完整 Trace）。"""
    traces = insight_dir / "traces"
    trace_path = traces / f"{work_id}.jsonl"
    summary_path = insight_dir / "summaries" / f"{work_id}.json"
    result = _read_summary(summary_path) if summary_path.is_file() else None
    if result is None and trace_path.is_file():
        result = summarize_trace(trace_path).to_dict()
    if result is None:
        return None
    result["trace_available"] = trace_path.is_file()
    result["trace"] = _iter_transitions(trace_path) if trace_path.is_file() else []
    return result
