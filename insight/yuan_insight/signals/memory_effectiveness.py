"""Signal：Memory Effectiveness（方案 §39.5）。

如果 Core 没有 Reported Used 事实，Signal 不得假设 selected != used。
v0 显示 "Memory selected: YES / Usage evidence: UNAVAILABLE"，
不计算虚假的 "Memory effectiveness 20%"。
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from .expected_observed import Signal, WhyProvenance


@dataclass
class MemorySelection:
    selected_ids: list[str] | None = None
    reported_used_ids: list[str] | None = None


def extract_memory_selection(work_snapshot: dict) -> MemorySelection:
    """从 WORK Current Task / Latest Result 提取 Memory 选择与使用声明。

    context_refs 中的 memory 引用 = selected；skills/result 中明确声明的
    memory_used = reported used。两者都是 Agent 声明，不是验证事实。
    """
    selection = MemorySelection()
    current_task = work_snapshot.get("current_task") or ""
    latest_result = work_snapshot.get("latest_result") or ""
    text = current_task + "\n" + latest_result

    # memory_refs / context_refs 中带 memory 的引用 = selected
    refs = re.findall(r"(?:memory_refs|context_refs)[:\s]+\[?([^\]]*)\]?", text)
    selected: list[str] = []
    for ref in refs:
        for item in re.split(r"[,\s]+", ref):
            if item and ("MEM" in item or "memory" in item.lower()):
                selected.append(item.strip())
    # 显式 memory_used 声明 = reported used
    used: list[str] = []
    for match in re.finditer(r"memory_used[:\s]+(.*?)(?:\n|$)", text):
        for item in re.split(r"[,\s]+", match.group(1).strip()):
            if item:
                used.append(item.strip())
    selection.selected_ids = sorted(set(selected)) if selected else None
    selection.reported_used_ids = sorted(set(used)) if used else None
    return selection


def compute_memory_effectiveness(selection: MemorySelection) -> list[Signal]:
    """v0：有 selected 事实时显示，无 usage 证据时明确 UNAVAILABLE，不伪造。"""
    if not selection.selected_ids:
        return []
    if selection.reported_used_ids:
        return [
            Signal(
                signal_id="MEMORY-REPORTED-USED",
                level="INFO",
                entity="memory",
                summary=f"Memory selected {len(selection.selected_ids)} 条，reported used {len(selection.reported_used_ids)} 条",
                why=WhyProvenance(
                    expected_rule="Memory 使用应可追踪（Agent 声明）",
                    observed=f"selected={selection.selected_ids}, used={selection.reported_used_ids}",
                    derived="Agent 声明已使用部分 Memory；这是声明不是验证",
                    check="结合 Work Outcome 评估 Memory 是否真正帮助",
                ),
            )
        ]
    return [
        Signal(
            signal_id="MEMORY-USAGE-UNAVAILABLE",
            level="INFO",
            entity="memory",
            summary="Memory selected: YES / Usage evidence: UNAVAILABLE",
            why=WhyProvenance(
                expected_rule="Memory selected 应有 usage evidence 支持",
                observed=f"selected={selection.selected_ids}, reported_used 无事实",
                derived="不能假设 selected != used，也不计算虚假 effectiveness",
                check="未来 Core 加入 Reported Used 事实后启用判定",
            ),
        )
    ]
