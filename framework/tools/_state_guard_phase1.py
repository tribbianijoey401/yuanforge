#!/usr/bin/env python3
"""Yuan State Commit Guard.

The guard is read-only. In the multi-work model each ``docs/works/<id>.md``
file is the canonical state for one persisted Work. ``docs/STATUS.md`` is a
short recovery index plus a derived projection of the currently focused Work.
Legacy v4 single-work projects remain readable until Conductor migrates them on
the next formal State Commit.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


WORK_STATES = ("idle", "active", "paused")  # legacy catalog compatibility
PERSISTED_WORK_STATES = ("ready", "active", "paused", "blocked")
AGENT_STATES = ("idle", "active", "paused", "completed", "blocked")
LEGACY_ACTIVE_AGENT_STATES = {"active", "completed", "blocked"}
WORK_ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")


class StateIssue:
    def __init__(self, code: str, field: str, actual: Any, expected: str, repair: str) -> None:
        self.code = code
        self.field = field
        self.actual = actual
        self.expected = expected
        self.repair = repair

    def to_dict(self) -> dict[str, Any]:
        return {
            "code": self.code,
            "field": self.field,
            "actual": self.actual,
            "expected": self.expected,
            "repair": self.repair,
        }

    def __repr__(self) -> str:
        return f"StateIssue(code={self.code!r}, field={self.field!r}, actual={self.actual!r})"


def _scalar(value: str) -> Any:
    cleaned = value.strip().strip("'\"")
    if cleaned.lower() in {"", "null", "none", "~"}:
        return None
    return cleaned


def parse_frontmatter(text: str) -> dict[str, Any]:
    """Parse the small two-level YAML subset used by Yuan state files."""
    if not text.startswith("---"):
        return {}
    parts = text.split("---", 2)
    if len(parts) != 3:
        return {}
    result: dict[str, Any] = {}
    container = result
    for line in parts[1].splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or ":" not in stripped:
            continue
        indent = len(line) - len(line.lstrip())
        key, _, rest = stripped.partition(":")
        if indent == 0:
            if rest.strip():
                result[key] = _scalar(rest)
                container = result
            else:
                child: dict[str, Any] = {}
                result[key] = child
                container = child
        else:
            container[key] = _scalar(rest)
    return result


def _frontmatter_lists(text: str) -> dict[str, list[str]]:
    if not text.startswith("---"):
        return {}
    parts = text.split("---", 2)
    if len(parts) != 3:
        return {}
    result: dict[str, list[str]] = {}
    current: str | None = None
    items: list[str] = []
    for line in parts[1].splitlines():
        match = re.match(r"^(\w+):\s*(.*)$", line)
        if match:
            if current is not None:
                result[current] = items
            current, rest = match.group(1), match.group(2).strip()
            items = []
            if rest.startswith("[") and rest.endswith("]"):
                items = [item.strip() for item in rest[1:-1].split(",") if item.strip()]
        elif current is not None and re.match(r"^\s*-\s+\S", line):
            items.append(re.sub(r"^\s*-\s+", "", line).strip())
    if current is not None:
        result[current] = items
    return result


def _section(text: str, heading: str) -> str:
    match = re.search(
        rf"^##\s+{re.escape(heading)}\s*$\r?\n(.*?)(?=^##\s+|\Z)",
        text,
        re.MULTILINE | re.DOTALL,
    )
    if not match:
        return ""
    return re.sub(r"<!--.*?-->", "", match.group(1), flags=re.DOTALL).strip()


def build_catalog(framework_root: Path, workflow_id: str | None = None) -> dict[str, Any]:
    agents_dir = framework_root / "agents"
    workflows_dir = framework_root / "workflows"
    agents = sorted(
        path.stem for path in agents_dir.glob("*.md") if path.name != "contract-template.md"
    ) if agents_dir.is_dir() else []
    workflows = sorted(path.stem for path in workflows_dir.glob("*.md")) if workflows_dir.is_dir() else []
    stages: list[str] = []
    workflow_agents: list[str] = []
    if workflow_id:
        workflow_path = workflows_dir / f"{workflow_id}.md"
        if workflow_path.is_file():
            declared = _frontmatter_lists(workflow_path.read_text(encoding="utf-8"))
            stages = declared.get("stages", [])
            workflow_agents = sorted(
                set(
                    declared.get("required_agents", [])
                    + declared.get("optional_agents", [])
                    + [
                        member
                        for group in declared.get("required_agent_groups", [])
                        for member in group.split("|")
                        if member
                    ]
                )
            )
    return {
        "work_states": list(WORK_STATES),
        "persisted_work_states": list(PERSISTED_WORK_STATES),
        "agent_states": list(AGENT_STATES),
        "workflows": workflows,
        "stages": stages,
        "agents": agents,
        "workflow_agents": workflow_agents,
    }


def _issue(code: str, field: str, actual: Any, expected: str, repair: str) -> StateIssue:
    return StateIssue(code, field, actual, expected, repair)


def _read_text(path: Path) -> tuple[str | None, StateIssue | None]:
    try:
        return path.read_text(encoding="utf-8"), None
    except (OSError, UnicodeError) as exc:
        return None, _issue(
            "STATE_FILE_UNREADABLE",
            path.as_posix(),
            type(exc).__name__,
            "UTF-8 readable Project State file",
            "Repair file access or encoding before the next Dispatch.",
        )


def _validate_execution_identity(
    *,
    issues: list[StateIssue],
    framework_root: Path,
    field_prefix: str,
    workflow: Any,
    stage: Any,
    agent_id: Any,
) -> None:
    catalog = build_catalog(framework_root, str(workflow) if workflow else None)
    field = lambda name: f"{field_prefix}.{name}" if field_prefix else name

    if not workflow:
        issues.append(_issue(
            "STATE_WORKFLOW_MISSING", field("workflow"), workflow,
            "Framework Workflow file stem", "Select one Primary Workflow from policies/routing.md."
        ))
    elif workflow not in catalog["workflows"]:
        issues.append(_issue(
            "STATE_WORKFLOW_UNKNOWN", field("workflow"), workflow,
            ", ".join(catalog["workflows"]), "Use the exact framework/workflows/*.md file stem."
        ))

    if not stage:
        issues.append(_issue(
            "STATE_STAGE_MISSING", field("stage"), stage,
            "current Workflow frontmatter stage", "Select one exact stage from the chosen Workflow frontmatter."
        ))
    elif workflow in catalog["workflows"] and stage not in catalog["stages"]:
        issues.append(_issue(
            "STATE_STAGE_UNKNOWN", field("stage"), stage,
            ", ".join(catalog["stages"]), "Use a canonical Workflow stage from the current Workflow frontmatter."
        ))

    if not agent_id:
        issues.append(_issue(
            "STATE_AGENT_MISSING", field("agent.id"), agent_id,
            "Agent Contract file stem", "Select one exact framework/agents/*.md file stem."
        ))
    elif agent_id not in catalog["agents"]:
        issues.append(_issue(
            "STATE_AGENT_UNKNOWN", field("agent.id"), agent_id,
            ", ".join(catalog["agents"]), "Use a canonical Agent Contract id; put persona/session labels in agent.instance."
        ))
    elif workflow in catalog["workflows"] and agent_id not in catalog["workflow_agents"]:
        issues.append(_issue(
            "STATE_AGENT_NOT_ALLOWED", field("agent.id"), agent_id,
            ", ".join(catalog["workflow_agents"]), "Route only an Agent declared by the current Workflow frontmatter."
        ))


def _validate_legacy_project_state(
    project_root: Path,
    framework_root: Path,
    status: dict[str, Any],
) -> list[StateIssue]:
    """Validate the pre-multi-work v4 WORK.md + STATUS.md checkpoint."""
    work_path = project_root / "docs" / "WORK.md"
    if not work_path.is_file():
        return [_issue(
            "STATE_FILE_MISSING", "docs/WORK.md", None,
            "legacy WORK.md while STATUS has no focus field",
            "Restore the legacy file or migrate the checkpoint into docs/works/<work-id>.md."
        )]

    work_text, read_issue = _read_text(work_path)
    if read_issue is not None:
        return [read_issue]
    assert work_text is not None

    issues: list[StateIssue] = []
    has_active_work = bool(_section(work_text, "Goal"))
    work_id = status.get("work")
    work_state_raw = status.get("work_state")
    work_state = str(work_state_raw).lower() if work_state_raw is not None else None
    workflow = status.get("workflow")
    stage = status.get("stage")
    agent = status.get("agent") if isinstance(status.get("agent"), dict) else {}
    agent_id = agent.get("id")
    agent_state_raw = agent.get("state")
    agent_state = str(agent_state_raw).lower() if agent_state_raw is not None else None

    if work_state not in WORK_STATES:
        issues.append(_issue(
            "STATE_WORK_STATE_UNKNOWN", "work_state", work_state_raw,
            " | ".join(WORK_STATES), "Use a canonical legacy work_state or migrate to a persisted Work file."
        ))

    checkpoint_claimed = has_active_work or bool(work_id) or work_state not in {None, "idle"}
    if has_active_work and work_state not in {"active", "paused"}:
        issues.append(_issue(
            "STATE_WORK_STATUS_MISMATCH", "work_state", work_state_raw,
            "active or paused while legacy WORK has an Active Goal", "Reconcile the legacy checkpoint before Dispatch."
        ))
    if not has_active_work and (bool(work_id) or work_state in {"active", "paused"}):
        issues.append(_issue(
            "STATE_WORK_STATUS_MISMATCH", "work", work_id,
            "Active Goal in legacy WORK.md", "Restore the Work Goal or Distill the legacy checkpoint."
        ))

    if not checkpoint_claimed:
        dangling = {
            "work": work_id,
            "workflow": workflow,
            "stage": stage,
            "agent.id": agent_id,
            "agent.state": agent_state_raw,
        }
        for field, actual in dangling.items():
            if actual is not None and not (field == "agent.state" and actual == "idle"):
                issues.append(_issue(
                    "STATE_IDLE_CHECKPOINT_DIRTY", field, actual,
                    "null while work_state=idle", "Clear legacy active checkpoint references during Distill."
                ))
        return issues

    if not work_id:
        issues.append(_issue(
            "STATE_WORK_ID_MISSING", "work", work_id,
            "non-empty Work id", "Assign a stable Work id before Dispatch."
        ))

    _validate_execution_identity(
        issues=issues,
        framework_root=framework_root,
        field_prefix="",
        workflow=workflow,
        stage=stage,
        agent_id=agent_id,
    )

    if agent_state not in AGENT_STATES:
        issues.append(_issue(
            "STATE_AGENT_STATE_UNKNOWN", "agent.state", agent_state_raw,
            " | ".join(AGENT_STATES), "Use exactly one canonical agent.state value from state-contract.md."
        ))
    elif work_state == "paused" and agent_state != "paused":
        issues.append(_issue(
            "STATE_AGENT_STATE_MISMATCH", "agent.state", agent_state,
            "paused while work_state=paused", "Pause the current Agent in the same State Commit."
        ))
    elif work_state == "active" and agent_state not in LEGACY_ACTIVE_AGENT_STATES:
        issues.append(_issue(
            "STATE_AGENT_STATE_MISMATCH", "agent.state", agent_state,
            "active | completed | blocked while work_state=active",
            "Commit the actual dispatch boundary using a canonical active-work Agent state."
        ))

    if work_state == "active" and not _section(work_text, "Current Task"):
        issues.append(_issue(
            "STATE_CURRENT_TASK_MISSING", "WORK.Current Task", None,
            "current dispatch task", "Write the current Agent task and Done Conditions before Dispatch."
        ))
    if work_state == "paused" and not _section(work_text, "Next Action"):
        issues.append(_issue(
            "STATE_NEXT_ACTION_MISSING", "WORK.Next Action", None,
            "one resumable Next Action", "Persist one concrete Next Action before pausing."
        ))
    return issues


def _normalized(value: Any) -> Any:
    return value.lower() if isinstance(value, str) else value


def _projection_from_work(work_id: str, work: dict[str, Any]) -> dict[str, Any]:
    agent = work.get("agent") if isinstance(work.get("agent"), dict) else {}
    quality = work.get("quality") if isinstance(work.get("quality"), dict) else {}
    return {
        "work": work_id,
        "work_state": _normalized(work.get("state")),
        "workflow": work.get("workflow"),
        "stage": work.get("stage"),
        "agent.id": agent.get("id"),
        "agent.instance": agent.get("instance"),
        "agent.state": _normalized(agent.get("state")),
        "quality.test": quality.get("test"),
        "quality.review": quality.get("review"),
    }


def _status_projection(status: dict[str, Any]) -> dict[str, Any]:
    agent = status.get("agent") if isinstance(status.get("agent"), dict) else {}
    quality = status.get("quality") if isinstance(status.get("quality"), dict) else {}
    return {
        "work": status.get("work"),
        "work_state": _normalized(status.get("work_state")),
        "workflow": status.get("workflow"),
        "stage": status.get("stage"),
        "agent.id": agent.get("id"),
        "agent.instance": agent.get("instance"),
        "agent.state": _normalized(agent.get("state")),
        "quality.test": quality.get("test"),
        "quality.review": quality.get("review"),
    }


def _validate_multi_work_state(
    project_root: Path,
    framework_root: Path,
    status: dict[str, Any],
) -> list[StateIssue]:
    issues: list[StateIssue] = []
    works_dir = project_root / "docs" / "works"
    work_paths = sorted(works_dir.glob("*.md")) if works_dir.is_dir() else []
    works: dict[str, tuple[dict[str, Any], str]] = {}

    for path in work_paths:
        text, read_issue = _read_text(path)
        if read_issue is not None:
            issues.append(read_issue)
            continue
        assert text is not None
        fm = parse_frontmatter(text)
        field_prefix = f"works/{path.name}"
        if not fm:
            issues.append(_issue(
                "STATE_WORK_FRONTMATTER_INVALID", field_prefix, None,
                "structured Work frontmatter", "Restore the Work file from the official template without losing the Work body."
            ))
            continue

        declared_id = fm.get("id")
        file_id = path.stem
        if not declared_id:
            issues.append(_issue(
                "STATE_WORK_ID_MISSING", f"{field_prefix}.id", declared_id,
                file_id, "Set Work id to the file stem."
            ))
        elif declared_id != file_id:
            issues.append(_issue(
                "STATE_WORK_ID_MISMATCH", f"{field_prefix}.id", declared_id,
                file_id, "Rename the file or restore the canonical id so filename stem and id match."
            ))
        if not WORK_ID_PATTERN.match(file_id):
            issues.append(_issue(
                "STATE_WORK_ID_INVALID", field_prefix, file_id,
                "letters/digits plus . _ -; no path separators", "Use a filesystem-safe stable Work id."
            ))

        state_raw = fm.get("state")
        state = _normalized(state_raw)
        if state not in PERSISTED_WORK_STATES:
            issues.append(_issue(
                "STATE_WORK_STATE_UNKNOWN", f"{field_prefix}.state", state_raw,
                " | ".join(PERSISTED_WORK_STATES), "Use one canonical persisted Work state."
            ))

        if not _section(text, "Goal"):
            issues.append(_issue(
                "STATE_WORK_GOAL_MISSING", f"{field_prefix}.Goal", None,
                "non-empty Work Goal", "Persist the Work Goal before treating this file as a Work."
            ))

        workflow = fm.get("workflow")
        stage = fm.get("stage")
        agent = fm.get("agent") if isinstance(fm.get("agent"), dict) else {}
        agent_id = agent.get("id")
        agent_state_raw = agent.get("state")
        agent_state = _normalized(agent_state_raw)

        needs_execution_identity = state in {"active", "paused", "blocked"}
        has_partial_identity = any(value is not None for value in (workflow, stage, agent_id))
        if needs_execution_identity or has_partial_identity:
            _validate_execution_identity(
                issues=issues,
                framework_root=framework_root,
                field_prefix=field_prefix,
                workflow=workflow,
                stage=stage,
                agent_id=agent_id,
            )

        if state == "ready":
            if agent_state not in {None, "idle", "completed"}:
                issues.append(_issue(
                    "STATE_AGENT_STATE_MISMATCH", f"{field_prefix}.agent.state", agent_state_raw,
                    "null | idle | completed while Work is ready", "Clear an executing Agent state before leaving a Work ready."
                ))
        elif state == "active":
            if agent_state not in {"active", "completed"}:
                issues.append(_issue(
                    "STATE_AGENT_STATE_MISMATCH", f"{field_prefix}.agent.state", agent_state_raw,
                    "active | completed while Work is active",
                    "Commit the actual active dispatch boundary; use Work state blocked for a blocking stop."
                ))
            if not _section(text, "Current Task"):
                issues.append(_issue(
                    "STATE_CURRENT_TASK_MISSING", f"{field_prefix}.Current Task", None,
                    "current dispatch task", "Write the current Agent task and Done Conditions before Dispatch."
                ))
        elif state == "paused":
            if agent_state != "paused":
                issues.append(_issue(
                    "STATE_AGENT_STATE_MISMATCH", f"{field_prefix}.agent.state", agent_state_raw,
                    "paused while Work is paused", "Pause the focused Agent in the same State Commit."
                ))
            if not _section(text, "Next Action"):
                issues.append(_issue(
                    "STATE_NEXT_ACTION_MISSING", f"{field_prefix}.Next Action", None,
                    "one resumable Next Action", "Persist one concrete Next Action before pausing this Work."
                ))
        elif state == "blocked":
            if agent_state != "blocked":
                issues.append(_issue(
                    "STATE_AGENT_STATE_MISMATCH", f"{field_prefix}.agent.state", agent_state_raw,
                    "blocked while Work is blocked", "Record the blocking execution boundary in the same Work."
                ))
            if not _section(text, "Blocker"):
                issues.append(_issue(
                    "STATE_BLOCKER_MISSING", f"{field_prefix}.Blocker", None,
                    "observable blocker or missing authority", "Record why this Work cannot proceed."
                ))

        works[file_id] = (fm, text)

    focus = status.get("focus")
    if focus is not None and (not isinstance(focus, str) or not WORK_ID_PATTERN.match(focus)):
        issues.append(_issue(
            "STATE_FOCUS_INVALID", "focus", focus,
            "null or a valid docs/works/<id>.md file stem", "Set focus to an existing persisted Work id."
        ))

    if focus is not None and focus not in works:
        issues.append(_issue(
            "STATE_FOCUS_MISSING", "focus", focus,
            "existing docs/works/<focus>.md", "Choose an existing Work or clear focus."
        ))

    active_ids = [
        work_id for work_id, (fm, _) in works.items()
        if _normalized(fm.get("state")) == "active"
    ]
    if len(active_ids) > 1:
        issues.append(_issue(
            "STATE_MULTIPLE_ACTIVE_WORKS", "docs/works", active_ids,
            "at most one active Work in Phase 1",
            "Pause or ready the other Work before Dispatch; Phase 1 has no concurrent Work scheduler."
        ))
    elif active_ids and focus != active_ids[0]:
        issues.append(_issue(
            "STATE_ACTIVE_WORK_NOT_FOCUSED", "focus", focus,
            active_ids[0], "Focus the only active Work before Dispatch."
        ))

    actual_projection = _status_projection(status)
    if focus is None:
        expected_projection = {
            "work": None,
            "work_state": "idle",
            "workflow": None,
            "stage": None,
            "agent.id": None,
            "agent.instance": None,
            "agent.state": None,
            "quality.test": "pending",
            "quality.review": "pending",
        }
        legacy_path = project_root / "docs" / "WORK.md"
        if not works and legacy_path.is_file():
            legacy_text, _ = _read_text(legacy_path)
            if legacy_text and _section(legacy_text, "Goal"):
                issues.append(_issue(
                    "STATE_LEGACY_WORK_UNMIGRATED", "docs/WORK.md", "active Goal",
                    "docs/works/<work-id>.md or an empty legacy compatibility file",
                    "On the next Conductor State Commit, migrate the legacy Work into the multi-work store."
                ))
    elif focus in works:
        expected_projection = _projection_from_work(focus, works[focus][0])
    else:
        expected_projection = None

    if expected_projection is not None:
        for field, expected in expected_projection.items():
            actual = actual_projection[field]
            if actual != expected:
                issues.append(_issue(
                    "STATE_FOCUS_PROJECTION_MISMATCH", f"STATUS.{field}", actual,
                    repr(expected),
                    "Regenerate STATUS as a derived projection of the focused Work; do not edit a second truth source."
                ))

    return issues


def validate_project_state(project_root: Path, framework_root: Path) -> list[StateIssue]:
    """Validate persisted state without modifying any Project-owned file."""
    status_path = project_root / "docs" / "STATUS.md"
    if not status_path.is_file():
        return [_issue(
            "STATE_FILE_MISSING", "docs/STATUS.md", None,
            "readable Project recovery index", "Run Yuan update/bootstrap to create only the missing document."
        )]

    status_text, read_issue = _read_text(status_path)
    if read_issue is not None:
        return [read_issue]
    assert status_text is not None
    status = parse_frontmatter(status_text)

    if not status:
        legacy_work = project_root / "docs" / "WORK.md"
        if legacy_work.is_file():
            legacy_text, _ = _read_text(legacy_work)
            if legacy_text and not _section(legacy_text, "Goal"):
                return []
        return [_issue(
            "STATE_FRONTMATTER_INVALID", "docs/STATUS.md", None,
            "structured YAML frontmatter", "Restore STATUS.md frontmatter without guessing Project facts."
        )]

    if "focus" in status:
        return _validate_multi_work_state(project_root, framework_root, status)
    return _validate_legacy_project_state(project_root, framework_root, status)


def resolve_framework_root(project_root: Path) -> Path:
    vendored = project_root / ".yuan" / "framework"
    if vendored.is_dir():
        return vendored
    source = project_root / "framework"
    if source.is_dir():
        return source
    return Path(__file__).resolve().parents[1]


def _print_issues(issues: list[StateIssue], as_json: bool) -> None:
    if as_json:
        print(json.dumps([issue.to_dict() for issue in issues], ensure_ascii=False, indent=2))
        return
    if not issues:
        print("STATE_VALID: persisted Work/STATUS checkpoint is canonical")
        return
    for issue in issues:
        print(
            f"{issue.code}: {issue.field}={issue.actual!r}; "
            f"expected={issue.expected}; repair={issue.repair}"
        )


def main() -> int:
    parser = argparse.ArgumentParser(description="Yuan State Commit Guard")
    subparsers = parser.add_subparsers(dest="command", required=True)
    check = subparsers.add_parser("check", help="validate persisted Work state and STATUS focus")
    check.add_argument("project_root")
    check.add_argument("--json", action="store_true")
    catalog = subparsers.add_parser("catalog", help="show canonical state values")
    catalog.add_argument("project_root")
    catalog.add_argument("--workflow")
    args = parser.parse_args()

    project_root = Path(args.project_root).resolve()
    framework_root = resolve_framework_root(project_root)
    if args.command == "catalog":
        print(json.dumps(build_catalog(framework_root, args.workflow), ensure_ascii=False, indent=2))
        return 0
    issues = validate_project_state(project_root, framework_root)
    _print_issues(issues, args.json)
    return 0 if not issues else 2


if __name__ == "__main__":
    raise SystemExit(main())
