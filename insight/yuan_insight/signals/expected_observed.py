"""Expected vs Observed 比较引擎（方案 §31/§39/§40）。

Expected 来自 Framework Definition（workflow frontmatter + agent 合约 Skill
Assignment），Observed 来自 Yuan 持久化事实（Snapshot/STATUS/WORK）。
Missing 判定必须 coverage-aware：观察覆盖不足时只能说 Not Observed，不能判 Missing。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ..registry import Registry


@dataclass
class WhyProvenance:
    expected_rule: str
    observed: str
    derived: str
    check: str


@dataclass
class Signal:
    signal_id: str
    level: str  # MISSING / REPEATED / INFO
    entity: str
    summary: str
    why: WhyProvenance


@dataclass
class ExpectedAgents:
    required: list[str] = field(default_factory=list)
    required_groups: list[list[str]] = field(default_factory=list)
    optional: list[str] = field(default_factory=list)


@dataclass
class ObservedAgents:
    observed_ids: list[str] = field(default_factory=list)
    completed_ids: list[str] = field(default_factory=list)
    reported_skills: list[str] = field(default_factory=list)
    coverage: str = "UNKNOWN"  # FULL / PARTIAL / UNKNOWN


def expected_from_workflow(
    snapshot_workflow: dict[str, Any],
    registry: Registry,
) -> ExpectedAgents:
    """从 Snapshot 的 workflow Expected + registry 提取 Expected Agents。"""
    required = list(snapshot_workflow.get("required_agents", []))
    optional = list(snapshot_workflow.get("optional_agents", []))
    raw_groups = snapshot_workflow.get("required_agent_groups", [])
    groups: list[list[str]] = []
    for group in raw_groups:
        members = group if isinstance(group, list) else str(group).split("|")
        normalized = [str(member) for member in members if str(member)]
        if normalized:
            groups.append(normalized)
    return ExpectedAgents(required=required, required_groups=groups, optional=optional)


def observed_from_snapshot(snapshot: dict[str, Any]) -> ObservedAgents:
    """从 Snapshot 提取 Observed Agent 事实。

    Observed 来源：STATUS 的 current/previous agent。由于 STATUS 只保留当前
    Agent（覆盖语义），Insight 无法从单一 Snapshot 看到全部历史 Agent；
    完整 Observed 集合需要 Trace。此处返回基于当前 Snapshot 的最小事实。
    """
    status = snapshot.get("status") or snapshot
    agent = status.get("agent") or {}
    agent_id = agent.get("id")
    agent_state = agent.get("state")
    observed: ObservedAgents = ObservedAgents()
    if agent_id:
        observed.observed_ids = [agent_id]
    if agent_id and agent_state == "completed":
        observed.completed_ids = [agent_id]
    observed.coverage = "PARTIAL" if agent_id else "UNKNOWN"
    return observed


def observed_from_trace(trace_facts: list[dict[str, Any]]) -> ObservedAgents:
    """从 Trace Facts 聚合完整 Observed Agent 集合（跨 Transition）。"""
    observed: ObservedAgents = ObservedAgents()
    for transition in trace_facts:
        facts = transition.get("facts", []) if "facts" in transition else [transition]
        if transition.get("work_id") or (transition.get("state") or {}).get("work"):
            # Manager Model 下，存在受管 Work 即可确定 Conductor 参与了状态维护。
            if "conductor" not in observed.observed_ids:
                observed.observed_ids.append("conductor")
        state_agent = (transition.get("state") or {}).get("agent") or {}
        transition_agent: str | None = state_agent.get("id")
        if transition_agent and transition_agent not in observed.observed_ids:
            observed.observed_ids.append(transition_agent)
        for fact in facts:
            if fact.get("field") == "status.agent.id":
                for value in (fact.get("from"), fact.get("to")):
                    if value and str(value) not in observed.observed_ids:
                        observed.observed_ids.append(str(value))
                if fact.get("to"):
                    transition_agent = str(fact["to"])
            if fact.get("field") == "work.latest_result":
                for value in (fact.get("from"), fact.get("to")):
                    for skill in _skills_from_result(str(value or "")):
                        if skill not in observed.reported_skills:
                            observed.reported_skills.append(skill)
        if transition_agent:
            for fact in facts:
                if fact.get("field") == "status.agent.state" and fact.get("to") == "completed":
                    if transition_agent not in observed.completed_ids:
                        observed.completed_ids.append(transition_agent)
    observed.coverage = "FULL" if observed.observed_ids else "UNKNOWN"
    return observed


def _skills_from_result(text: str) -> list[str]:
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
    return sorted(set(skills))


def compute_missing_agents(
    expected: ExpectedAgents,
    observed: ObservedAgents,
    coverage: str,
) -> list[Signal]:
    """判定 Missing Agent（方案 §39.1）。

    只有满足全部条件才标 MISSING：
    - Expected rule 明确（workflow 声明 required_agents）
    - 相关 stage/work 已完成或正在进行
    - 观察 coverage 充分（FULL）
    - 该 agent 未被观察到
    否则只能说 NOT_OBSERVED / UNKNOWN。
    """
    signals: list[Signal] = []
    if coverage != "FULL":
        return signals
    observed_ids = set(observed.observed_ids)
    for agent_id in expected.required:
        if agent_id in observed_ids:
            continue
        signals.append(
            Signal(
                signal_id=f"MISSING-AGENT-{agent_id}",
                level="MISSING",
                entity=agent_id,
                summary=f"Expected Agent {agent_id} 未被观察到",
                why=WhyProvenance(
                    expected_rule=f"Workflow required_agents 声明 {agent_id}",
                    observed=f"Coverage={coverage}，已观察 Agents={sorted(observed_ids)}",
                    derived=f"{agent_id} 应在当前 Workflow 出现但未出现",
                    check="检查 Conductor Routing 与 Workflow 遵循情况",
                ),
            )
        )
    for group in expected.required_groups:
        if observed_ids.intersection(group):
            continue
        group_id = "-or-".join(group)
        signals.append(
            Signal(
                signal_id=f"MISSING-AGENT-GROUP-{group_id}",
                level="MISSING",
                entity="|".join(group),
                summary=f"Expected Agent Group {' / '.join(group)} 未被观察到",
                why=WhyProvenance(
                    expected_rule=f"Workflow required_agent_groups 声明 {' | '.join(group)} 至少一个",
                    observed=f"Coverage={coverage}，已观察 Agents={sorted(observed_ids)}",
                    derived=f"{' / '.join(group)} 中应至少出现一个 Agent",
                    check="检查 Conductor Writer Routing 与 Workflow 遵循情况",
                ),
            )
        )
    return signals


def compute_missing_skills(
    expected_workflow_skills: list[str],
    observed_skills: list[str],
    coverage: str,
) -> list[Signal]:
    """判定 Missing Skill（方案 §39.2）。

    需要两个事实：Expected Skill 明确 + Actual skill usage 有事实源
    （skills_applied）。任一缺失都不能判 Missing。
    """
    signals: list[Signal] = []
    if coverage != "FULL" or not observed_skills:
        return signals
    observed_set = set(observed_skills)
    for skill_id in expected_workflow_skills:
        if skill_id in observed_set:
            continue
        signals.append(
            Signal(
                signal_id=f"MISSING-SKILL-{skill_id}",
                level="MISSING",
                entity=skill_id,
                summary=f"Expected Skill {skill_id} 未被报告使用",
                why=WhyProvenance(
                    expected_rule=f"Workflow required_skills 声明 {skill_id}",
                    observed=f"Reported skills_applied={sorted(observed_set)}",
                    derived=f"{skill_id} 应在当前 Workflow 中被使用但未报告",
                    check="检查 Agent Skill 选择与 Workflow 规则",
                ),
            )
        )
    return signals
