"""Snapshot Diff → Transition → Facts。

方案 §29：Transition 是底层存储单位，Fact 是 UI 展示单位。
一次 Snapshot Diff 的多个同时变化归入一个 Transition（不伪造严格顺序）。
"""

from __future__ import annotations

from typing import Any

from .loader import Snapshot


def _changes(before: dict[str, Any], after: dict[str, Any], prefix: str = "") -> list[dict[str, Any]]:
    """递归比较两个 dict，产出语义变化 Fact。"""
    facts: list[dict[str, Any]] = []
    keys = set(before) | set(after)
    for key in sorted(keys):
        path = f"{prefix}.{key}" if prefix else key
        old_value = before.get(key)
        new_value = after.get(key)
        if isinstance(old_value, dict) or isinstance(new_value, dict):
            facts.extend(_changes(
                old_value if isinstance(old_value, dict) else {},
                new_value if isinstance(new_value, dict) else {},
                path,
            ))
            continue
        if old_value != new_value:
            facts.append({
                "kind": "field_changed",
                "field": path,
                "from": old_value,
                "to": new_value,
            })
    return facts


def _workflow_facts(before: Snapshot, after: Snapshot) -> list[dict[str, Any]]:
    """Workflow Expected 变化（Framework 定义版本变化时）。"""
    if before.workflow == after.workflow:
        return []
    return [{
        "kind": "workflow_expected_changed",
        "from": before.workflow,
        "to": after.workflow,
    }]


def diff_snapshots(before: Snapshot, after: Snapshot) -> list[dict[str, Any]]:
    """比较两个 Snapshot，产出 Facts 列表（一个 Transition 的内容）。"""
    facts: list[dict[str, Any]] = []

    changed_files = [
        path for path in sorted(set(before.files) | set(after.files))
        if before.files.get(path) != after.files.get(path)
    ]
    if changed_files:
        facts.append({
            "kind": "files_changed",
            "sources_changed": changed_files,
        })

    facts.extend(_changes(before.status, after.status, prefix="status"))
    facts.extend(_changes(before.work, after.work, prefix="work"))
    facts.extend(_workflow_facts(before, after))
    return facts


def diff_work_snapshots(before: Snapshot, after: Snapshot, work_id: str) -> list[dict[str, Any]]:
    """Return Work-local semantic facts, excluding another lane's STATUS projection."""
    before_work = before.works.get(work_id, {})
    after_work = after.works.get(work_id, {})
    facts = _changes(before_work, after_work, prefix="work")
    path = f"docs/works/{work_id}.md"
    if before.files.get(path) != after.files.get(path):
        facts.insert(0, {"kind": "files_changed", "sources_changed": [path]})
    return facts


def to_transition(
    transition_id: str,
    session_id: str,
    observed_at: str,
    before: Snapshot,
    after: Snapshot,
    facts: list[dict[str, Any]],
    work_id: str | None = None,
) -> dict[str, Any]:
    """把 Facts 组装成 Transition（底层存储单位）。"""
    changed = sorted(
        path for path in set(before.files) | set(after.files)
        if before.files.get(path) != after.files.get(path)
    )
    work_state = after.works.get(work_id or "") or before.works.get(work_id or "", {})
    state = {
        "work": work_id or after.status.get("work"),
        "work_state": work_state.get("state", after.status.get("work_state")),
        "workflow": work_state.get("workflow", after.status.get("workflow")),
        "stage": work_state.get("stage", after.status.get("stage")),
        "agent": work_state.get("agent", after.status.get("agent")),
        "execution": work_state.get("execution", {}),
    }
    return {
        "id": transition_id,
        "session_id": session_id,
        "observed_at": observed_at,
        "sources_changed": [f"docs/works/{work_id}.md"] if work_id else changed,
        "before_hash": before.fingerprint(),
        "after_hash": after.fingerprint(),
        "state": state,
        "facts": facts,
    }
