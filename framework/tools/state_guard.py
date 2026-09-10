#!/usr/bin/env python3
"""Yuan State Commit Guard — Multi-Work Phase 2.

Phase 1 validation remains the compatibility foundation. Phase 2 only relaxes
"multiple active" when every concurrently active Work proves an independent
Agent-Platform execution instance and an independent mutable workspace.
Yuan validates those identities; it does not allocate, schedule, or merge them.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
from pathlib import Path
from typing import Any


_PHASE1_PATH = Path(__file__).with_name("_state_guard_phase1.py")
_spec = importlib.util.spec_from_file_location("yuan_state_guard_phase1", _PHASE1_PATH)
if _spec is None or _spec.loader is None:
    raise RuntimeError(f"Cannot load {_PHASE1_PATH}")
_phase1 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_phase1)

StateIssue = _phase1.StateIssue
WORK_STATES = _phase1.WORK_STATES
PERSISTED_WORK_STATES = _phase1.PERSISTED_WORK_STATES
AGENT_STATES = _phase1.AGENT_STATES
WORK_ID_PATTERN = _phase1.WORK_ID_PATTERN
EXECUTION_MODES = ("shared", "isolated")
CHANNEL_ONLY_INSTANCES = {"subagent", "background-process", "persona-degraded"}

parse_frontmatter = _phase1.parse_frontmatter
resolve_framework_root = _phase1.resolve_framework_root


def build_catalog(framework_root: Path, workflow_id: str | None = None) -> dict[str, Any]:
    catalog = dict(_phase1.build_catalog(framework_root, workflow_id))
    catalog["execution_modes"] = list(EXECUTION_MODES)
    return catalog


def _issue(code: str, field: str, actual: Any, expected: str, repair: str) -> StateIssue:
    return StateIssue(code, field, actual, expected, repair)


def _normalized(value: Any) -> Any:
    return value.lower() if isinstance(value, str) else value


def _concurrent_active_issues(project_root: Path, status: dict[str, Any]) -> list[StateIssue]:
    works_dir = project_root / "docs" / "works"
    if not works_dir.is_dir():
        return []

    works: dict[str, dict[str, Any]] = {}
    for path in sorted(works_dir.glob("*.md")):
        try:
            fm = parse_frontmatter(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError):
            continue
        if fm:
            works[path.stem] = fm

    active_ids = [
        work_id for work_id, fm in works.items()
        if _normalized(fm.get("state")) == "active"
    ]
    if len(active_ids) <= 1:
        return []

    issues: list[StateIssue] = []
    workspaces: dict[str, str] = {}
    instances: dict[str, str] = {}
    isolation_ok = True

    for work_id in active_ids:
        fm = works[work_id]
        prefix = f"works/{work_id}.md"
        execution = fm.get("execution") if isinstance(fm.get("execution"), dict) else {}
        agent = fm.get("agent") if isinstance(fm.get("agent"), dict) else {}
        mode = _normalized(execution.get("mode"))
        workspace = execution.get("workspace")
        instance = agent.get("instance")

        if mode != "isolated":
            isolation_ok = False
            issues.append(_issue(
                "STATE_ACTIVE_WORK_ISOLATION_REQUIRED",
                f"{prefix}.execution.mode",
                mode,
                "isolated for every concurrently active Work",
                "Serialize this Work, or persist a Platform-provided independent workspace before concurrent activation.",
            ))

        if not isinstance(workspace, str) or not workspace.strip():
            isolation_ok = False
            issues.append(_issue(
                "STATE_ACTIVE_WORKSPACE_MISSING",
                f"{prefix}.execution.workspace",
                workspace,
                "non-empty independent mutable workspace identity",
                "Do not invent an id; obtain a real sandbox/worktree/workspace from the Agent Platform.",
            ))
        else:
            workspace = workspace.strip()
            if workspace in workspaces:
                isolation_ok = False
                issues.append(_issue(
                    "STATE_ACTIVE_WORKSPACE_CONFLICT",
                    f"{prefix}.execution.workspace",
                    workspace,
                    f"unique across active Works; already used by {workspaces[workspace]}",
                    "Serialize one Work or move it to a genuinely independent mutable workspace.",
                ))
            else:
                workspaces[workspace] = work_id

        if not isinstance(instance, str) or not instance.strip():
            isolation_ok = False
            issues.append(_issue(
                "STATE_ACTIVE_AGENT_INSTANCE_MISSING",
                f"{prefix}.agent.instance",
                instance,
                "distinct independent execution instance for concurrent active Work",
                "Use a Platform-issued independent agent/process instance; single-persona execution must serialize.",
            ))
        else:
            instance = instance.strip()
            if instance == "persona-degraded":
                isolation_ok = False
                issues.append(_issue(
                    "STATE_PARALLEL_EXECUTION_UNAVAILABLE",
                    f"{prefix}.agent.instance",
                    instance,
                    "independent subagent/background execution instance",
                    "Serialize this Work because one-LLM persona switching is not concurrent execution.",
                ))
            elif instance in CHANNEL_ONLY_INSTANCES:
                isolation_ok = False
                issues.append(_issue(
                    "STATE_ACTIVE_AGENT_INSTANCE_IDENTITY_REQUIRED",
                    f"{prefix}.agent.instance",
                    instance,
                    "a stable Platform execution identity such as subagent:<id> or background-process:<id>",
                    "Persist the Platform-provided instance id; a channel label alone is insufficient for concurrent Work.",
                ))
            if instance in instances:
                isolation_ok = False
                issues.append(_issue(
                    "STATE_ACTIVE_AGENT_INSTANCE_CONFLICT",
                    f"{prefix}.agent.instance",
                    instance,
                    f"unique across active Works; already used by {instances[instance]}",
                    "Use separate Platform execution instances or serialize the Work.",
                ))
            else:
                instances[instance] = work_id

    focus = status.get("focus")
    if focus not in active_ids:
        issues.append(_issue(
            "STATE_ACTIVE_WORK_NOT_FOCUSED",
            "focus",
            focus,
            "one of the active Work ids: " + ", ".join(active_ids),
            "Keep focus on one active Work while other isolated active Works remain in flight.",
        ))

    if not isolation_ok:
        issues.append(_issue(
            "STATE_MULTIPLE_ACTIVE_WORKS",
            "docs/works",
            active_ids,
            "multiple active Works only when all concurrent lanes are independently isolated",
            "Satisfy the Phase 2 isolation contract for every active Work, or reduce to one active Work.",
        ))
    return issues


def validate_project_state(project_root: Path, framework_root: Path) -> list[StateIssue]:
    issues = list(_phase1.validate_project_state(project_root, framework_root))
    status_path = project_root / "docs" / "STATUS.md"
    try:
        status = parse_frontmatter(status_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError):
        return issues
    if "focus" not in status:
        return issues

    concurrent = _concurrent_active_issues(project_root, status)
    if any(issue.code == "STATE_MULTIPLE_ACTIVE_WORKS" for issue in issues):
        # Phase 1 rejected all multiple-active states. Phase 2 replaces that
        # blanket rejection with the deterministic isolation checks above.
        issues = [issue for issue in issues if issue.code != "STATE_MULTIPLE_ACTIVE_WORKS"]
    issues.extend(concurrent)
    return issues


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
