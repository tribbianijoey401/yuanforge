"""解析 docs/STATUS.md 的 YAML Frontmatter 与恢复摘要。"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class StatusState:
    work: str | None = None
    work_state: str | None = None
    workflow: str | None = None
    stage: str | None = None
    agent_id: str | None = None
    agent_instance: str | None = None
    agent_state: str | None = None
    quality_test: str | None = None
    quality_review: str | None = None
    situation: str | None = None
    last_completed: str | None = None
    next: str | None = None
    blocker: str | None = None
    raw: dict[str, Any] = field(default_factory=dict)


def parse_frontmatter(text: str) -> dict[str, Any]:
    """解析 YAML Frontmatter（--- 包裹），支持标量与 agent/quality 两层嵌套。"""
    if not text.startswith("---"):
        return {}
    body = text.split("---", 2)
    if len(body) < 3:
        return {}
    value: dict[str, Any] = {}
    container: dict[str, Any] = value
    for line in body[1].splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        indent = len(line) - len(line.lstrip())
        if ":" not in stripped:
            continue
        key, _, rest = stripped.partition(":")
        rest = rest.strip()
        if indent == 0:
            if rest == "":
                child: dict[str, Any] = {}
                value[key] = child
                container = child
            else:
                value[key] = _scalar(rest)
                container = value
        else:
            container[key] = _scalar(rest)
    return value


def _scalar(rest: str) -> Any:
    if rest in ("null", "~"):
        return None
    if rest.startswith('"') and rest.endswith('"'):
        return rest[1:-1]
    if rest == "[]":
        return []
    return rest


def parse_status(text: str) -> StatusState:
    """从 STATUS.md 提取可观察语义状态。无法解析的字段为 None（= Unknown）。"""
    fm = parse_frontmatter(text)
    state = StatusState(raw=fm)
    state.work = fm.get("work")
    state.work_state = fm.get("work_state")
    state.workflow = fm.get("workflow")
    state.stage = fm.get("stage")
    agent = fm.get("agent")
    if isinstance(agent, dict):
        state.agent_id = agent.get("id")
        state.agent_instance = agent.get("instance")
        state.agent_state = agent.get("state")
    quality = fm.get("quality")
    if isinstance(quality, dict):
        state.quality_test = quality.get("test")
        state.quality_review = quality.get("review")

    headings: dict[str, str] = {}
    current_heading: str | None = None
    for line in text.splitlines():
        heading = re.match(r"^#+\s+(.+)$", line.strip())
        if heading:
            current_heading = heading.group(1).strip().lower()
            if current_heading not in headings:
                headings[current_heading] = ""
        else:
            active_heading = current_heading
            if active_heading is not None and line.strip():
                headings[active_heading] += line.strip() + "\n"
    state.situation = headings.get("current situation", "").strip() or None
    state.last_completed = headings.get("last completed", "").strip() or None
    state.next = headings.get("next", "").strip() or None
    state.blocker = headings.get("blocker", "").strip() or None
    return state


def load_status(path: Path) -> StatusState:
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        return StatusState()
    return parse_status(text)
