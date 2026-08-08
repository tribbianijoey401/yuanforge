"""Signal 聚合入口：从 Snapshot + Trace 计算全部可用 Signals。"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ..registry import Registry
from .bug_recurrence import BugIdentityEvidence, compute_bug_recurrence
from .expected_observed import (
    Signal,
    WhyProvenance,
    compute_missing_agents,
    compute_missing_skills,
    expected_from_workflow,
    observed_from_snapshot,
)
from .memory_effectiveness import (
    compute_memory_effectiveness,
    extract_memory_selection,
)
from .repeated_review import compute_repeated_review, extract_findings


@dataclass
class SignalReport:
    signals: list[Signal] = field(default_factory=list)
    coverage: str = "UNKNOWN"

    def to_dict(self) -> dict[str, Any]:
        return {
            "coverage": self.coverage,
            "signals": [
                {
                    "signal_id": signal.signal_id,
                    "level": signal.level,
                    "entity": signal.entity,
                    "summary": signal.summary,
                    "why": {
                        "expected": signal.why.expected_rule,
                        "observed": signal.why.observed,
                        "derived": signal.why.derived,
                        "check": signal.why.check,
                    },
                }
                for signal in self.signals
            ],
        }


def compute_signals(
    snapshot: dict[str, Any],
    registry: Registry,
    coverage: str = "UNKNOWN",
) -> SignalReport:
    """从单个 Snapshot 计算 Signals。

    coverage 默认 UNKNOWN：单一 Snapshot 无法证明完整观察（STATUS 只保留当前
    Agent），因此 Missing 判定默认不触发——这正是方案 §30.2 的 Coverage 语义。
    Trace 就绪后传入 FULL coverage 才能触发 Missing。
    """
    report = SignalReport(coverage=coverage)

    snapshot_workflow = snapshot.get("workflow") or {}
    workflow_id = snapshot_workflow.get("workflow_id")
    if not workflow_id or workflow_id == "unknown":
        return report

    expected = expected_from_workflow(snapshot_workflow, registry)
    observed = observed_from_snapshot(snapshot)
    report.signals.extend(
        compute_missing_agents(expected, observed, coverage=coverage)
    )

    expected_skills = snapshot_workflow.get("required_skills", [])
    latest_result = (snapshot.get("work") or {}).get("latest_result") or ""
    observed_skills = _extract_skills_applied(latest_result)
    report.signals.extend(
        compute_missing_skills(expected_skills, observed_skills, coverage=coverage)
    )

    # Repeated Reviewer Finding（不依赖 coverage——Open Findings 是持久化事实）
    findings = extract_findings(snapshot.get("work") or {})
    report.signals.extend(compute_repeated_review(findings))

    # Known Bug Recurrence：v0 无可靠 Bug identity，显示 unavailable 不猜
    report.signals.extend(
        compute_bug_recurrence(BugIdentityEvidence(work_id=(snapshot.get("work") or {}).get("id")))
    )

    # Memory Effectiveness：selected 有事实则显示，usage evidence 无则 UNAVAILABLE
    memory_selection = extract_memory_selection(snapshot.get("work") or {})
    report.signals.extend(compute_memory_effectiveness(memory_selection))
    return report


def _extract_skills_applied(latest_result: str) -> list[str]:
    """从 WORK Latest Result 文本提取 skills_applied（如果有事实源）。"""
    if not latest_result:
        return []
    skills: list[str] = []
    capture = False
    for line in latest_result.splitlines():
        stripped = line.strip()
        if "skills_applied" in stripped:
            capture = True
            inline = stripped.split(":", 1)[1].strip() if ":" in stripped else ""
            if inline:
                skills.extend(_parse_inline_list(inline))
            continue
        if capture:
            if stripped.startswith("-"):
                skills.append(stripped.lstrip("- ").strip())
            elif stripped:
                break
    return sorted(set(skills))


def _parse_inline_list(text: str) -> list[str]:
    cleaned = text.strip("[]").strip()
    if not cleaned:
        return []
    return [item.strip().strip("'\"") for item in cleaned.split(",") if item.strip()]
