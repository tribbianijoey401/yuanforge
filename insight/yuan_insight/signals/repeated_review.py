"""Signal：Repeated Reviewer Finding（方案 §39.3）。

基于 Open Findings / Latest Result 中的 Finding 分类跨 Review Round 的确定性
重复统计。只报告事实（如 `test-gap × 3 rounds`），不自动解释根因。
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from .expected_observed import Signal, WhyProvenance

FINDING_CATEGORIES = {
    "requirement-miss",
    "correctness",
    "regression",
    "test-gap",
    "security",
    "architecture",
    "maintainability",
}

REPEAT_THRESHOLD = 2  # 同一分类出现 ≥2 轮才报 Repeated


@dataclass
class ReviewFinding:
    category: str | None
    round_number: int
    text: str


def extract_findings(work_snapshot: dict) -> list[ReviewFinding]:
    """从 WORK Open Findings / Latest Result 提取 Finding 分类。

    可解析的分类来自 verdict-protocol 的七分类；无法识别分类的 Finding
    保留为 None（分类 Unknown），不计入重复统计。
    """
    findings: list[ReviewFinding] = []
    open_findings = work_snapshot.get("open_findings") or []
    latest_result = work_snapshot.get("latest_result") or ""

    round_number = 1
    for item in open_findings:
        category = _match_category(item)
        findings.append(ReviewFinding(category=category, round_number=round_number, text=item))

    for line in latest_result.splitlines():
        category = _match_category(line)
        if category:
            findings.append(ReviewFinding(category=category, round_number=round_number, text=line))
    return findings


def extract_findings_from_transitions(
    transitions: list[dict],
) -> list[ReviewFinding]:
    """从 Trace Transition 提取 Review Round。

    同一 Transition 代表同一次稳定语义更新，同类 Finding 在其中只计
    一个 Round；只有出现在不同 Transition 才构成 Repeated Review。
    """
    findings: list[ReviewFinding] = []
    for index, transition in enumerate(transitions, 1):
        round_id = index
        categories_seen: set[str] = set()
        state = transition.get("state") or {}
        agent_id = str((state.get("agent") or {}).get("id") or "")
        stage = str(state.get("stage") or "")
        role_is_review = agent_id == "tester" or agent_id.endswith("reviewer") or agent_id.endswith("auditor")
        for fact in transition.get("facts", []):
            if fact.get("field") not in ("work.latest_result", "work.open_findings"):
                continue
            value = fact.get("to")
            lines = value if isinstance(value, list) else str(value or "").splitlines()
            text = "\n".join(str(line) for line in lines)
            if not role_is_review and stage not in {"review", "regression"}:
                if "finding" not in text.lower() and "verdict" not in text.lower():
                    continue
            for line in lines:
                category = _match_category(str(line))
                if not category or category in categories_seen:
                    continue
                categories_seen.add(category)
                findings.append(
                    ReviewFinding(
                        category=category,
                        round_number=round_id,
                        text=str(line),
                    )
                )
    return findings


def _match_category(text: str) -> str | None:
    for category in FINDING_CATEGORIES:
        if category in text:
            return category
    return None


def compute_repeated_review(findings: list[ReviewFinding]) -> list[Signal]:
    """统计跨 Round 的 Finding 分类重复。"""
    rounds_by_category: dict[str, set[int]] = {}
    for finding in findings:
        if finding.category:
            rounds_by_category.setdefault(finding.category, set()).add(
                finding.round_number
            )

    signals: list[Signal] = []
    for category, rounds in rounds_by_category.items():
        count = len(rounds)
        if count < REPEAT_THRESHOLD:
            continue
        signals.append(
            Signal(
                signal_id=f"REPEATED-REVIEW-{category}",
                level="REPEATED",
                entity=category,
                summary=f"Repeated reviewer finding: {category} × {count} rounds",
                why=WhyProvenance(
                    expected_rule="Reviewer Finding 应随 Review Round 收敛",
                    observed=f"Finding 分类 {category} 出现 {count} 次",
                    derived=f"同一 Finding 分类跨 {count} 轮重复出现",
                    check="检查修复是否真正定位根因，或审查标准是否过于严格",
                ),
            )
        )
    return signals
