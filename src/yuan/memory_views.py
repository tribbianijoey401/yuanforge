"""从权威 Memory Record 生成可读、可重建的项目视图。"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .canonical import canonical_bytes
from .ledger import atomic_write
from .validate import with_digest


MEMORY_ROOT = Path("docs/memory")
CATEGORIES = {
    "project": "knowledge", "feature": "knowledge", "module": "knowledge",
    "architecture": "knowledge", "convention": "knowledge", "decision": "decisions",
    "pitfall": "experience", "incident": "experience", "checkpoint": "continuity",
    "handoff": "continuity",
}
VIEW_KINDS = {
    "ARCHITECTURE.md": ("architecture", "module"),
    "DECISIONS.md": ("decision",),
    "PITFALLS.md": ("pitfall", "incident"),
    "CONVENTIONS.md": ("convention",),
}


def record_relative(record: dict[str, Any]) -> Path:
    if record["schema_version"] == "yuan.memory/v1":
        return MEMORY_ROOT / "records" / record["kind"] / record["memory_id"] / f"{record['revision']:06d}.json"
    return MEMORY_ROOT / "records" / CATEGORIES[record["kind"]] / record["kind"] / record["memory_id"] / f"{record['revision']:06d}.json"


def index_value(heads: list[dict[str, Any]]) -> dict[str, Any]:
    values = []
    for head in sorted(heads, key=lambda item: item["memory_id"]):
        values.append({
            "memory_id": head["memory_id"], "revision": head["revision"], "kind": head["kind"],
            "category": CATEGORIES[head["kind"]], "title": head["title"], "summary": head["summary"],
            "status": head["status"], "confidence": head["confidence"], "tags": head["tags"],
            "digest": head["digest"], "record": record_relative(head).as_posix(),
        })
    return with_digest({"schema_version": "yuan.memory-index/v2", "heads": values})


def _table(title: str, description: str, items: list[dict[str, Any]]) -> bytes:
    lines = [f"# {title}", "", description, ""]
    if items:
        lines.extend(["| ID | Kind | Rev | Status | Confidence | Summary |", "|---|---|---:|---|---|---|"])
        for item in items:
            summary = item["summary"].replace("|", "\\|").replace("\n", " ")
            lines.append(f"| `{item['memory_id']}` | {item['kind']} | {item['revision']} | {item['status']} | {item['confidence']} | {summary} |")
    else:
        lines.append("当前尚无记录。")
    return ("\n".join(lines).rstrip() + "\n").encode("utf-8")


def _current(heads: list[dict[str, Any]]) -> bytes:
    candidates = [item for item in heads if item["kind"] in {"checkpoint", "handoff"} and item["status"] == "active"]
    head = max(candidates, key=lambda item: (item["created_at"], item["memory_id"]), default=None)
    lines = ["# 当前项目交接", "", "此文件由 `yuan memory rebuild` 生成；请勿直接编辑。", ""]
    if head is None:
        lines.extend(["当前尚无连续性检查点。", "", "使用 `yuan memory checkpoint` 保存已完成事项、阻塞与下一步。"])
    else:
        lines.extend([f"## {head['title']}", "", head["summary"], "", head["details"], ""])
        labels = {
            "completed": "已完成", "blockers": "阻塞", "next_steps": "下一步",
            "open_questions": "待确认问题", "resume_commands": "恢复命令",
        }
        for field, label in labels.items():
            values = head.get("data", {}).get(field, [])
            if values:
                lines.extend([f"### {label}", "", *[f"- {value}" for value in values], ""])
        lines.extend([f"来源：`{head['memory_id']}` revision {head['revision']} / `{head['digest']}`", ""])
    return ("\n".join(lines).rstrip() + "\n").encode("utf-8")


def _project(heads: list[dict[str, Any]]) -> bytes:
    projects = [item for item in heads if item["kind"] == "project" and item["status"] == "active"]
    lines = ["# 项目长期概览", "", "此文件由 `project` Memory Record 生成；权威事实仍是 JSON Revision。", ""]
    if not projects:
        lines.append("当前尚无项目概览记录。")
    for item in projects:
        lines.extend([f"## {item['title']}", "", item["summary"], "", item["details"], ""])
    return ("\n".join(lines).rstrip() + "\n").encode("utf-8")


def write_views(root: Path, heads: list[dict[str, Any]]) -> dict[str, Any]:
    index = index_value(heads)
    atomic_write(root / MEMORY_ROOT / "index.json", canonical_bytes(index))
    atomic_write(root / MEMORY_ROOT / "INDEX.md", _table("Yuan 项目长期记忆", "此文件由权威 Memory Record 重建。", index["heads"]))
    atomic_write(root / MEMORY_ROOT / "CURRENT.md", _current(heads))
    atomic_write(root / MEMORY_ROOT / "PROJECT.md", _project(heads))
    for filename, kinds in VIEW_KINDS.items():
        items = [item for item in index["heads"] if item["kind"] in kinds and item["status"] != "superseded"]
        atomic_write(root / MEMORY_ROOT / "views" / filename, _table(filename[:-3].title(), "此文件是可重建的人类可读视图。", items))
    return index
