"""Agent / Skill Registry — 直接读取 Framework 目录，不建立重复数据库。

方案 §32：Agent Registry 直接读 .yuan/framework/agents/，Skill Registry 直接读
.yuan/framework/skills/。Agent Contract 的 Skill Assignment 三档语义
（Required/Recommended/Conditional）构成 Expected Skill 来源。
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class AgentContract:
    agent_id: str
    required_skills: list[str] = field(default_factory=list)
    recommended_skills: list[str] = field(default_factory=list)
    conditional_skills: list[str] = field(default_factory=list)
    raw_skill_assignment: str = ""


@dataclass
class Registry:
    agents: dict[str, AgentContract] = field(default_factory=dict)
    skills: list[str] = field(default_factory=list)
    workflows: list[str] = field(default_factory=list)

    def agent_ids(self) -> set[str]:
        return set(self.agents)

    def skill_ids(self) -> set[str]:
        return set(self.skills)


def _skill_id_from_path(path: Path) -> str:
    return path.parent.name if path.name == "SKILL.md" else path.stem


def _parse_skill_assignment(assignment: str) -> tuple[list[str], list[str], list[str]]:
    """从 Skill Assignment 行提取三档 Skill id。"""
    required: list[str] = []
    recommended: list[str] = []
    conditional: list[str] = []
    segments = re.split(r"[；;]", assignment)
    for segment in segments:
        paths = re.findall(r"`(skills/[^`]+)`", segment)
        if not paths:
            continue
        ids = [_skill_id_from_path(Path(path)) for path in paths]
        if re.search(r"Required", segment):
            required.extend(ids)
        elif re.search(r"Recommended", segment):
            recommended.extend(ids)
        elif re.search(r"Conditional", segment):
            conditional.extend(ids)
    return required, recommended, conditional


def load_registry(framework_root: Path) -> Registry:
    """从 Framework 目录加载 Agent/Skill/Workflow 注册表。"""
    registry = Registry()

    agents_dir = framework_root / "agents"
    if agents_dir.is_dir():
        for path in sorted(agents_dir.glob("*.md")):
            if path.name == "contract-template.md":
                continue
            text = path.read_text(encoding="utf-8")
            assignment = next(
                (line for line in text.splitlines() if "Skill Assignment" in line),
                "",
            )
            required, recommended, conditional = _parse_skill_assignment(assignment)
            registry.agents[path.stem] = AgentContract(
                agent_id=path.stem,
                required_skills=required,
                recommended_skills=recommended,
                conditional_skills=conditional,
                raw_skill_assignment=assignment,
            )

    skills_dir = framework_root / "skills"
    if skills_dir.is_dir():
        registry.skills = [
            _skill_id_from_path(path)
            for path in sorted(list(skills_dir.glob("*.md")) + list(skills_dir.glob("*/SKILL.md")))
        ]

    workflows_dir = framework_root / "workflows"
    if workflows_dir.is_dir():
        registry.workflows = sorted(path.stem for path in workflows_dir.glob("*.md"))
    return registry
