"""Signal：Repeated Reviewer Finding（方案 §39.3）。

基于 Open Findings / Latest Result 中的 Finding 分类跨 Review Round 的确定性
重复统计。只报告事实（如 `test-gap × 3 rounds`），不自动解释根因。
"""

from __future__ import annotations

import re
from collections import Counter
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


def _match_category(text: str) -> str | None:
    for category in FINDING_CATEGORIES:
        if category in text:
            return category
    return None


def compute_repeated_review(findings: list[ReviewFinding]) -> list[Signal]:
    """统计跨 Round 的 Finding 分类重复。"""
    counters: Counter[str] = Counter()
    for finding in findings:
        if finding.category:
            counters[finding.category] += 1

    signals: list[Signal] = []
    for category, count in counters.items():
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
