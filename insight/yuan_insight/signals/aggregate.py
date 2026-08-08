"""Signal 聚合入口：从 Snapshot + Trace 计算全部可用 Signals。"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from ..registry import Registry
from .expected_observed import (
    Signal,
    WhyProvenance,
    compute_missing_agents,
    compute_missing_skills,
    expected_from_workflow,
    observed_from_snapshot,
)


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
