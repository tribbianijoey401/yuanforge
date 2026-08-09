"""解析 Framework Definition：workflow frontmatter 的 Expected Agent/Skill。"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class WorkflowDefinition:
    workflow_id: str
    stages: list[str] = field(default_factory=list)
    required_agents: list[str] = field(default_factory=list)
    required_agent_groups: list[list[str]] = field(default_factory=list)
    optional_agents: list[str] = field(default_factory=list)
    required_skills: list[str] = field(default_factory=list)
    raw: dict[str, Any] = field(default_factory=dict)


def parse_frontmatter_lists(frontmatter: str) -> dict[str, list[str]]:
    """解析 YAML Frontmatter 的列表字段，同时支持内联 [a, b] 与展开 - item 两种形式。"""
    result: dict[str, list[str]] = {}
    current_field: str | None = None
    current_items: list[str] = []
    for line in frontmatter.splitlines():
        match = re.match(r"^(\w+):\s*(.*)$", line)
        if match:
            if current_field is not None:
                result[current_field] = current_items
            current_field, rest = match.group(1), match.group(2).strip()
            current_items = []
            if rest.startswith("[") and rest.endswith("]"):
                current_items = [item.strip() for item in rest[1:-1].split(",") if item.strip()]
        elif current_field is not None and re.match(r"^\s*-\s+\S", line):
            current_items.append(re.sub(r"^\s*-\s+", "", line).strip())
    if current_field is not None:
        result[current_field] = current_items
    return result


def parse_workflow(text: str) -> WorkflowDefinition:
    if not text.startswith("---"):
        return WorkflowDefinition(workflow_id="unknown")
    body = text.split("---", 2)
    if len(body) < 3:
        return WorkflowDefinition(workflow_id="unknown")
    frontmatter = body[1]
    lists = parse_frontmatter_lists(frontmatter)
    workflow_match = re.search(r"^workflow:\s*(\S+)", frontmatter, re.M)
    workflow_id = workflow_match.group(1) if workflow_match else "unknown"
    return WorkflowDefinition(
        workflow_id=workflow_id,
        stages=list(lists.get("stages", [])),
        required_agents=list(lists.get("required_agents", [])),
        required_agent_groups=[
            [member for member in group.split("|") if member]
            for group in lists.get("required_agent_groups", [])
            if "|" in group
        ],
        optional_agents=list(lists.get("optional_agents", [])),
        required_skills=list(lists.get("required_skills", [])),
        raw=lists,
    )


def load_workflow(path: Path) -> WorkflowDefinition:
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        return WorkflowDefinition(workflow_id="unknown")
    return parse_workflow(text)


def load_workflow_by_id(framework_root: Path, workflow_id: str) -> WorkflowDefinition:
    """按 workflow id 从 framework/workflows/ 加载定义。"""
    if not workflow_id:
        return WorkflowDefinition(workflow_id="unknown")
    candidate = framework_root / "workflows" / f"{workflow_id}.md"
    if candidate.is_file():
        return load_workflow(candidate)
    return WorkflowDefinition(workflow_id=workflow_id)
