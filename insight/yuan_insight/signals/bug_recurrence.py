"""Signal：Known Bug Recurrence（方案 §39.4）。

目标定义：同一个已知 Root Cause / Pitfall 再次出现，不是"症状看起来相似"。
v0 没有可靠 Bug identity / Memory linkage，Signal 显示 unavailable，
不实现模糊语义匹配。Bug Manager Skill 暂不做。
"""

from __future__ import annotations

from dataclasses import dataclass

from .expected_observed import Signal, WhyProvenance


@dataclass
class BugIdentityEvidence:
    """Bug identity 的可用证据。v0 无可靠 linkage 时为空。"""

    work_id: str | None = None
    linked_memory_ids: list[str] | None = None
    known_root_causes: list[str] | None = None

    @property
    def has_reliable_identity(self) -> bool:
        return bool(self.linked_memory_ids or self.known_root_causes)


def compute_bug_recurrence(evidence: BugIdentityEvidence) -> list[Signal]:
    """v0：无可靠 Bug identity / Memory linkage 时 unavailable，不猜。"""
    if evidence.has_reliable_identity:
        # 未来版本：有 linkage 时比较当前 Work 的 Root Cause 与已知 Pitfall
        return [
            Signal(
                signal_id="BUG-RECURRENCE-PENDING",
                level="INFO",
                entity="bug-recurrence",
                summary="Bug identity linkage 已建立，Recurrence 判定待实现",
                why=WhyProvenance(
                    expected_rule="Known Bug Recurrence = 同一 Root Cause 再次出现",
                    observed=f"Work={evidence.work_id}, linked_memory={evidence.linked_memory_ids}",
                    derived="有 identity 但当前版本不实现模糊语义匹配",
                    check="未来版本启用；当前不猜测",
                ),
            )
        ]
    return [
        Signal(
            signal_id="BUG-RECURRENCE-UNAVAILABLE",
            level="INFO",
            entity="bug-recurrence",
            summary="Known Bug Recurrence: UNAVAILABLE（无可靠 Bug identity / Memory linkage）",
            why=WhyProvenance(
                expected_rule="Known Bug Recurrence = 同一 Root Cause / Pitfall 再次出现",
                observed="当前没有可靠的 Bug identity 与 Memory linkage 事实",
                derived="无法确定复发，不实现模糊语义匹配",
                check="未来引入 Bug Manager Skill 或 Memory linkage 后启用",
            ),
        )
    ]
