"""读取 Project State 文件并组装语义 Snapshot。"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .parsers.framework import load_workflow_by_id
from .parsers.status import load_status
from .parsers.work import load_work


@dataclass
class Snapshot:
    observed_at: str
    files: dict[str, str] = field(default_factory=dict)  # relative path -> content hash
    work: dict[str, Any] = field(default_factory=dict)
    status: dict[str, Any] = field(default_factory=dict)
    workflow: dict[str, Any] = field(default_factory=dict)

    def fingerprint(self) -> str:
        payload = "|".join(f"{path}:{digest}" for path, digest in sorted(self.files.items()))
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    def to_dict(self) -> dict[str, Any]:
        return {
            "work": self.work,
            "status": self.status,
            "workflow": self.workflow,
        }


def _content_hash(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


WATCHED_DOCS = (
    "docs/STATUS.md",
    "docs/WORK.md",
    "docs/MEMORY.md",
    "docs/DECISIONS.md",
    "docs/ARCHITECTURE.md",
)


def collect_project_files(root: Path) -> dict[str, str]:
    """收集被观察文件的 content hash。文件缺失时记录 MISSING。"""
    files: dict[str, str] = {}
    for relative in WATCHED_DOCS:
        path = root / relative
        if path.is_file():
            try:
                files[relative] = _content_hash(path.read_bytes())
            except OSError:
                files[relative] = "UNREADABLE"
        else:
            files[relative] = "MISSING"
    return files


def build_snapshot(root: Path, observed_at: str) -> Snapshot:
    """读取当前可观察语义状态，生成 Snapshot。无法解析的字段保持空（= Unknown）。"""
    snapshot = Snapshot(observed_at=observed_at)
    snapshot.files = collect_project_files(root)

    status = load_status(root / "docs" / "STATUS.md")
    snapshot.status = {
        "work": status.work,
        "work_state": status.work_state,
        "workflow": status.workflow,
        "stage": status.stage,
        "agent": {"id": status.agent_id, "state": status.agent_state},
        "quality": {"test": status.quality_test, "review": status.quality_review},
        "situation": status.situation,
        "last_completed": status.last_completed,
        "next": status.next,
        "blocker": status.blocker,
    }

    work = load_work(root / "docs" / "WORK.md")
    snapshot.work = {
        "has_active_work": work.has_active_work,
        "goal": work.goal,
        "scope": work.scope,
        "current_task": work.current_task,
        "latest_result": work.latest_result,
        "open_findings": work.open_findings,
        "work_learnings": work.work_learnings,
    }

    # Expected：从 workflow 定义提取（Framework 静态定义，变化时才重读）
    workflow_id = status.workflow or ""
    framework_root = root / ".yuan" / "framework"
    if not framework_root.is_dir():
        framework_root = root / "framework"
    definition = load_workflow_by_id(framework_root, workflow_id)
    snapshot.workflow = {
        "workflow_id": definition.workflow_id,
        "required_agents": definition.required_agents,
        "optional_agents": definition.optional_agents,
        "required_skills": definition.required_skills,
    }
    return snapshot
