"""读取 Project State 文件并组装语义 Snapshot。"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
import re

from .parsers.framework import load_workflow_by_id
from .parsers.status import load_status
from .parsers.work import load_work
from .state_validation import validate_persisted_state


@dataclass
class Snapshot:
    observed_at: str
    files: dict[str, str] = field(default_factory=dict)  # relative path -> content hash
    work: dict[str, Any] = field(default_factory=dict)
    works: dict[str, dict[str, Any]] = field(default_factory=dict)
    status: dict[str, Any] = field(default_factory=dict)
    workflow: dict[str, Any] = field(default_factory=dict)
    state_validation: list[dict[str, Any]] | None = None

    def source_status(self) -> dict[str, str]:
        """Expose availability without leaking content hashes to the UI."""
        return {
            path: digest if digest in {"MISSING", "UNREADABLE"} else "AVAILABLE"
            for path, digest in self.files.items()
        }

    def fingerprint(self) -> str:
        payload = "|".join(f"{path}:{digest}" for path, digest in sorted(self.files.items()))
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    def to_dict(self) -> dict[str, Any]:
        return {
            "work": self.work,
            "works": self.works,
            "status": self.status,
            "workflow": self.workflow,
            "state_validation": self.state_validation,
            "sources": self.source_status(),
        }


def _content_hash(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


WATCHED_DOCS = (
    "docs/STATUS.md",
    "docs/WORK.md",  # legacy compatibility
    "docs/MEMORY.md",
    "docs/DECISIONS.md",
    "docs/ARCHITECTURE.md",
)


def collect_project_files(root: Path) -> dict[str, str]:
    """收集被观察文件的 content hash；Multi-Work 文件动态加入。"""
    files: dict[str, str] = {}
    relatives = list(WATCHED_DOCS)
    works_dir = root / "docs" / "works"
    if works_dir.is_dir():
        relatives.extend(
            path.relative_to(root).as_posix()
            for path in sorted(works_dir.glob("*.md"))
            if path.is_file()
        )

    for relative in relatives:
        path = root / relative
        if path.is_file():
            try:
                files[relative] = _content_hash(path.read_bytes())
            except OSError:
                files[relative] = "UNREADABLE"
        else:
            files[relative] = "MISSING"
    return files


def _focused_work_path(root: Path, status) -> tuple[Path, str | None, str]:
    """Return canonical observed Work path, id and source kind.

    Presence of ``focus`` in raw frontmatter distinguishes the new multi-work
    format from legacy v4. A new-format STATUS with ``focus: null`` must not
    accidentally resurrect legacy WORK.md as current state.
    """
    if "focus" in status.raw:
        if status.focus:
            return root / "docs" / "works" / f"{status.focus}.md", status.focus, "multi-work"
        return root / "docs" / "works" / ".no-focused-work", None, "multi-work"
    return root / "docs" / "WORK.md", status.work, "legacy"


def _frontmatter(path: Path) -> dict[str, Any]:
    """Read the small state fields Insight needs without owning State Guard parsing."""
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        return {}
    if not text.startswith("---"):
        return {}
    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}
    result: dict[str, Any] = {}
    current: str | None = None
    for line in parts[1].splitlines():
        match = re.match(r"^(\w+):\s*(.*)$", line)
        if match:
            current, value = match.groups()
            value = value.strip().strip("'\"")
            if value:
                result[current] = None if value.lower() == "null" else value
            else:
                result[current] = {}
        elif current and (nested := re.match(r"^\s+(\w+):\s*(.*)$", line)):
            if not isinstance(result.get(current), dict):
                result[current] = {}
            key, value = nested.groups()
            result[current][key] = value.strip().strip("'\"") or None
    return result


def _persisted_works(root: Path) -> dict[str, dict[str, Any]]:
    works: dict[str, dict[str, Any]] = {}
    works_dir = root / "docs" / "works"
    if not works_dir.is_dir():
        return works
    for path in sorted(works_dir.glob("*.md")):
        frontmatter = _frontmatter(path)
        parsed = load_work(path)
        work_id = str(frontmatter.get("id") or path.stem)
        works[work_id] = {
            "id": work_id,
            "path": path.relative_to(root).as_posix(),
            "state": frontmatter.get("state"),
            "workflow": frontmatter.get("workflow"),
            "stage": frontmatter.get("stage"),
            "agent": frontmatter.get("agent") if isinstance(frontmatter.get("agent"), dict) else {},
            "execution": frontmatter.get("execution") if isinstance(frontmatter.get("execution"), dict) else {},
            "goal": parsed.goal,
            "scope": parsed.scope,
            "current_task": parsed.current_task,
            "latest_result": parsed.latest_result,
            "next_action": parsed.next_action,
            "open_findings": parsed.open_findings,
            "work_learnings": parsed.work_learnings,
        }
    return works


def build_snapshot(root: Path, observed_at: str) -> Snapshot:
    """读取当前可观察语义状态，生成 Snapshot。无法解析的字段保持空（= Unknown）。"""
    snapshot = Snapshot(observed_at=observed_at)
    snapshot.files = collect_project_files(root)

    status = load_status(root / "docs" / "STATUS.md")
    snapshot.status = {
        "focus": status.focus,
        "work": status.work,
        "work_state": status.work_state,
        "workflow": status.workflow,
        "stage": status.stage,
        "agent": {
            "id": status.agent_id,
            "instance": status.agent_instance,
            "state": status.agent_state,
        },
        "quality": {"test": status.quality_test, "review": status.quality_review},
        "situation": status.situation,
        "last_completed": status.last_completed,
        "next": status.next,
        "blocker": status.blocker,
    }

    work_path, work_id, work_source = _focused_work_path(root, status)
    work = load_work(work_path)
    snapshot.work = {
        "id": work_id,
        "source": work_source,
        "path": work_path.relative_to(root).as_posix() if work_source != "multi-work" or work_id else None,
        "has_active_work": work.has_active_work,
        "goal": work.goal,
        "scope": work.scope,
        "current_task": work.current_task,
        "latest_result": work.latest_result,
        "next_action": work.next_action,
        "open_findings": work.open_findings,
        "work_learnings": work.work_learnings,
    }
    # ``work`` remains the focused compatibility view. ``works`` carries all
    # canonical persisted Work state so Phase 2 can attribute evidence per lane.
    snapshot.works = _persisted_works(root)

    # Expected：从 focused Work 的 STATUS projection 中取得 workflow id。
    workflow_id = status.workflow or ""
    framework_root = root / ".yuan" / "framework"
    if not framework_root.is_dir():
        framework_root = root / "framework"
    definition = load_workflow_by_id(framework_root, workflow_id)
    snapshot.workflow = {
        "workflow_id": definition.workflow_id,
        "stages": definition.stages,
        "required_agents": definition.required_agents,
        "required_agent_groups": definition.required_agent_groups,
        "optional_agents": definition.optional_agents,
    }
    snapshot.state_validation = validate_persisted_state(root, framework_root)
    return snapshot
