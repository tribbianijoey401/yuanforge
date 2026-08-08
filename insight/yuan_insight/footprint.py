"""Context Footprint（方案 §36）。

正式语义：Declared Context Footprint = Agent Handoff 中 Yuan 明确交付的
Context References 的规模。不包括 Agent 后续自行打开的文件、平台 System
Prompt、Token 数、模型实际"看见"的所有上下文。

v0 指标：References / Documents / Sections / Characters / Bytes / Memory refs。
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class ContextFootprint:
    references: int = 0
    documents: int = 0
    sections: int = 0
    characters: int = 0
    bytes: int = 0
    memory_refs: int = 0
    per_document: dict[str, dict] = field(default_factory=dict)
    coverage: str = "UNKNOWN"  # FULL / PARTIAL / UNKNOWN


def extract_context_refs(work_snapshot: dict, project_root: Path) -> ContextFootprint:
    """从 WORK Current Task / Latest Result 的 context_refs 计算 Declared Footprint。

    context_refs 是 Conductor 在 Handoff 中显式交付的 Context 引用（方案 §18）。
    v0 只统计能从 context_refs 稳定解析的引用；无法解析的记 PARTIAL。
    """
    footprint = ContextFootprint()
    current_task = work_snapshot.get("current_task") or ""
    latest_result = work_snapshot.get("latest_result") or ""
    text = current_task + "\n" + latest_result

    refs = _parse_context_refs(text)
    footprint.references = len(refs)
    if not refs:
        footprint.coverage = "UNKNOWN"
        return footprint

    memory_refs = [ref for ref in refs if "MEM" in ref or "memory" in ref.lower()]
    footprint.memory_refs = len(memory_refs)

    doc_refs = [ref for ref in refs if ref not in memory_refs]
    footprint.documents = len(set(doc_refs))

    for ref in doc_refs:
        path = project_root / ref
        if not path.is_file():
            continue
        try:
            payload = path.read_bytes()
        except OSError:
            continue
        text_content = payload.decode("utf-8", errors="replace")
        footprint.characters += len(text_content)
        footprint.bytes += len(payload)
        footprint.sections += len(
            re.findall(r"^#{1,3}\s+.+$", text_content, re.M)
        )
        footprint.per_document[ref] = {
            "characters": len(text_content),
            "bytes": len(payload),
            "sections": len(re.findall(r"^#{1,3}\s+.+$", text_content, re.M)),
        }
    footprint.coverage = "FULL"
    return footprint


def _parse_context_refs(text: str) -> list[str]:
    """解析 context_refs 列表（支持 - item 与 [a, b] 两种形式）。"""
    refs: list[str] = []
    for match in re.finditer(r"context_refs[:\s]+(.*)", text):
        rest = match.group(1).strip()
        if rest.startswith("["):
            refs.extend(
                item.strip().strip("'\"")
                for item in rest.strip("[]").split(",")
                if item.strip()
            )
        elif rest:
            refs.append(rest)
    # 展开形式：- docs/xxx.md
    for match in re.finditer(r"^\s*-\s+(docs/[\w\-./]+\.md|MEMORY[-\w]*)", text, re.M):
        refs.append(match.group(1))
    return sorted(set(refs))
