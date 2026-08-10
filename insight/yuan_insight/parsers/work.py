"""解析 docs/WORK.md 的 Contract 与 Active Workspace 语义。"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class WorkState:
    has_active_work: bool = False
    goal: str | None = None
    scope: str | None = None
    current_task: str | None = None
    latest_result: str | None = None
    next_action: str | None = None
    open_findings: list[str] = field(default_factory=list)
    work_learnings: list[str] = field(default_factory=list)
    raw: dict[str, Any] = field(default_factory=dict)


def _heading_sections(text: str) -> dict[str, str]:
    sections: dict[str, str] = {}
    current: str | None = None
    for line in text.splitlines():
        heading = re.match(r"^#{1,3}\s+(.+)$", line.strip())
        if heading:
            current = heading.group(1).strip().lower()
            if current not in sections:
                sections[current] = ""
            active = current
        else:
            active = current
            if active is not None and line.strip():
                sections[active] += line.strip() + "\n"
    return sections


def _is_empty(text: str) -> bool:
    """去掉列表标记、HTML 注释和空白后是否为空。"""
    cleaned = re.sub(r"<!--.*?-->", "", text, flags=re.S)
    cleaned = re.sub(r"^\s*[-*]\s*", "", cleaned, flags=re.M)
    return not cleaned.strip()


def parse_work(text: str) -> WorkState:
    # Template guidance is metadata for humans/LLMs, not persisted Work fact.
    text = re.sub(r"<!--.*?-->", "", text, flags=re.S)
    sections = _heading_sections(text)
    state = WorkState()

    goal = sections.get("goal", "")
    state.has_active_work = bool(goal.strip())
    state.goal = goal.strip() or None
    state.scope = sections.get("scope", "").strip() or None
    state.current_task = sections.get("current task", "").strip() or None
    state.latest_result = sections.get("latest result", "").strip() or None
    state.next_action = sections.get("next action", "").strip() or None

    findings = sections.get("open findings", "")
    if findings and not _is_empty(findings):
        raw_findings = [
            re.sub(r"^\s*[-*]\s*", "", line).strip()
            for line in findings.splitlines()
            if line.strip() and not re.match(r"^\s*[-*]\s*$", line)
        ]
        state.open_findings = [
            item for item in raw_findings if item and item not in ("无", "None", "-", "—")
        ]

    learnings = sections.get("work learnings", "")
    if learnings and not _is_empty(learnings):
        state.work_learnings = [
            re.sub(r"^\s*[-*]\s*", "", line).strip()
            for line in learnings.splitlines()
            if line.strip()
        ]
    return state


def load_work(path: Path) -> WorkState:
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        return WorkState()
    return parse_work(text)
