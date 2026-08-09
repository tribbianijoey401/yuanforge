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

    memory_refs = [ref for ref in refs if "mem" in ref.lower()]
    footprint.memory_refs = len(memory_refs)

    doc_refs = sorted({ref for ref in refs if _is_document_ref(ref)})
    footprint.documents = len(doc_refs)
    # Logical Memory ID（如 MEM-001）是有效选择证据，但无法推导文档规模。
    complete = len(doc_refs) == len(refs)
    project_root = project_root.resolve()

    for ref in doc_refs:
        file_ref, _, section = ref.partition("#")
        path = (project_root / file_ref).resolve()
        try:
            path.relative_to(project_root)
        except ValueError:
            complete = False
            continue
        if not path.is_file():
            complete = False
            continue
        try:
            payload = path.read_bytes()
        except OSError:
            complete = False
            continue
        try:
            text_content = payload.decode("utf-8")
        except UnicodeError:
            complete = False
            continue
        selected_content = _select_section(text_content, section) if section else text_content
        if section and not selected_content:
            complete = False
            continue
        selected_bytes = selected_content.encode("utf-8")
        section_count = len(re.findall(r"^#{1,3}\s+.+$", selected_content, re.M))
        footprint.characters += len(selected_content)
        footprint.bytes += len(selected_bytes)
        footprint.sections += section_count
        footprint.per_document[ref] = {
            "characters": len(selected_content),
            "bytes": len(selected_bytes),
            "sections": section_count,
        }
    footprint.coverage = "FULL" if complete else "PARTIAL"
    return footprint


def _parse_context_refs(text: str) -> list[str]:
    """解析 context_refs 列表（支持 - item 与 [a, b] 两种形式）。"""
    refs: list[str] = []
    lines = text.splitlines()
    index = 0
    while index < len(lines):
        match = re.match(
            r"^\s*(?:-\s*)?(?:context_refs|memory_refs)\s*:\s*(.*)$",
            lines[index],
            re.I,
        )
        if not match:
            index += 1
            continue
        rest = match.group(1).strip()
        if rest.startswith("[") and rest.endswith("]"):
            refs.extend(_split_inline_refs(rest))
        elif rest:
            refs.append(_clean_ref(rest))
        else:
            cursor = index + 1
            while cursor < len(lines):
                item = re.match(r"^\s*-\s+(.+?)\s*$", lines[cursor])
                if not item:
                    if lines[cursor].strip():
                        break
                    cursor += 1
                    continue
                refs.append(_clean_ref(item.group(1)))
                cursor += 1
            index = cursor - 1
        index += 1
    return sorted(set(refs))


def _split_inline_refs(value: str) -> list[str]:
    return [
        _clean_ref(item)
        for item in value.strip()[1:-1].split(",")
        if item.strip()
    ]


def _clean_ref(value: str) -> str:
    return value.strip().strip("`'\"")


def _is_document_ref(value: str) -> bool:
    file_ref = value.partition("#")[0]
    return file_ref.lower().endswith(".md") or "/" in file_ref or "\\" in file_ref


def _select_section(text: str, section: str) -> str:
    """按 Markdown Heading 选取声明的 Section；找不到时返回空内容。"""
    target = section.strip().lower().replace("-", " ")
    lines = text.splitlines(keepends=True)
    start: int | None = None
    level = 0
    for index, line in enumerate(lines):
        heading = re.match(r"^(#{1,6})\s+(.+?)\s*$", line)
        if not heading:
            continue
        normalized = heading.group(2).strip().lower().replace("-", " ")
        if start is None and normalized == target:
            start = index
            level = len(heading.group(1))
            continue
        if start is not None and len(heading.group(1)) <= level:
            return "".join(lines[start:index])
    return "".join(lines[start:]) if start is not None else ""
