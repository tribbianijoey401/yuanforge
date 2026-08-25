#!/usr/bin/env python3
"""Yuan State Commit Guard.

This module is the executable authority for persisted WORK/STATUS checkpoint
validation.  It is deliberately read-only: Conductor owns state writes, while
the guard decides whether a committed checkpoint is safe to dispatch from.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


WORK_STATES = ("idle", "active", "paused")
AGENT_STATES = ("idle", "active", "paused", "completed", "blocked")
ACTIVE_AGENT_STATES = {"active", "completed", "blocked"}
PRESENTATION_CONTRACT_STATES = ("n/a", "pending", "frozen")
UI_GATE_RULES = {
    "new-feature": frozenset({"implement", "verify", "review"}),
    "large-project": frozenset({"build", "verify", "review"}),
}


class StateIssue:
    def __init__(
        self,
        code: str,
        field: str,
        actual: Any,
        expected: str,
        repair: str,
    ) -> None:
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
        return (
            f"StateIssue(code={self.code!r}, field={self.field!r}, "
            f"actual={self.actual!r})"
        )


def _scalar(value: str) -> Any:
    cleaned = value.strip().strip("'\"")
    if cleaned.lower() in {"", "null", "none", "~"}:
        return None
    return cleaned


def parse_frontmatter(text: str) -> dict[str, Any]:
    """Parse the small two-level YAML subset used by STATUS.md."""
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


def _labeled_value(text: str, label: str) -> str:
    match = re.search(
        rf"^{re.escape(label)}\s*:\s*(.+?)\s*$",
        text,
        re.MULTILINE | re.IGNORECASE,
    )
    return match.group(1).strip() if match else ""


def _usable_contract_value(value: str) -> bool:
    return value.strip().lower() not in {
        "",
        "n/a",
        "na",
        "none",
        "null",
        "pending",
        "tbd",
        "todo",
        "unknown",
        "unavailable",
    }


def build_catalog(framework_root: Path, workflow_id: str | None = None) -> dict[str, Any]:
    agents_dir = framework_root / "agents"
    workflows_dir = framework_root / "workflows"
    agents = sorted(
        path.stem
        for path in agents_dir.glob("*.md")
        if path.name != "contract-template.md"
    ) if agents_dir.is_dir() else []
    workflows = sorted(path.stem for path in workflows_dir.glob("*.md")) \
        if workflows_dir.is_dir() else []
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
        "agent_states": list(AGENT_STATES),
        "presentation_contract_states": list(PRESENTATION_CONTRACT_STATES),
        "workflows": workflows,
        "stages": stages,
        "agents": agents,
        "workflow_agents": workflow_agents,
    }


def _issue(
    code: str,
    field: str,
    actual: Any,
    expected: str,
    repair: str,
) -> StateIssue:
    return StateIssue(code, field, actual, expected, repair)


def validate_project_state(project_root: Path, framework_root: Path) -> list[StateIssue]:
    """Validate persisted state without modifying any Project-owned file."""
    status_path = project_root / "docs" / "STATUS.md"
    work_path = project_root / "docs" / "WORK.md"
    issues: list[StateIssue] = []
    for path, field in ((status_path, "docs/STATUS.md"), (work_path, "docs/WORK.md")):
        if not path.is_file():
            issues.append(
                _issue(
                    "STATE_FILE_MISSING",
                    field,
                    None,
                    "readable Project State file",
                    "Run Yuan update/bootstrap to create only the missing document.",
                )
            )
    if issues:
        return issues
    try:
        status_text = status_path.read_text(encoding="utf-8")
        work_text = work_path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        return [
            _issue(
                "STATE_FILE_UNREADABLE",
                "project-state",
                type(exc).__name__,
                "UTF-8 readable WORK.md and STATUS.md",
                "Repair file access or encoding before the next Dispatch.",
            )
        ]

    status = parse_frontmatter(status_text)
    has_active_work = bool(_section(work_text, "Goal"))
    if not status:
        return [
            _issue(
                "STATE_FRONTMATTER_INVALID",
                "docs/STATUS.md",
                None,
                "structured YAML frontmatter",
                "Restore STATUS.md frontmatter from the official template, preserving Project facts.",
            )
        ] if has_active_work else []

    work_id = status.get("work")
    work_state_raw = status.get("work_state")
    work_state = str(work_state_raw).lower() if work_state_raw is not None else None
    workflow = status.get("workflow")
    stage = status.get("stage")
    agent = status.get("agent") if isinstance(status.get("agent"), dict) else {}
    agent_id = agent.get("id")
    agent_state_raw = agent.get("state")
    agent_state = str(agent_state_raw).lower() if agent_state_raw is not None else None
    presentation_contract = status.get("presentation_contract")

    if work_state not in WORK_STATES:
        issues.append(
            _issue(
                "STATE_WORK_STATE_UNKNOWN",
                "work_state",
                work_state_raw,
                " | ".join(WORK_STATES),
                "Use exactly one canonical work_state value from state-contract.md.",
            )
        )

    checkpoint_claimed = has_active_work or bool(work_id) or work_state not in {None, "idle"}
    if has_active_work and work_state not in {"active", "paused"}:
        issues.append(
            _issue(
                "STATE_WORK_STATUS_MISMATCH",
                "work_state",
                work_state_raw,
                "active or paused while WORK has an Active Goal",
                "Reconcile WORK and STATUS before Dispatch.",
            )
        )
    if not has_active_work and (bool(work_id) or work_state in {"active", "paused"}):
        issues.append(
            _issue(
                "STATE_WORK_STATUS_MISMATCH",
                "work",
                work_id,
                "Active Goal in WORK.md",
                "Restore the Work Goal or Distill both files to no active work.",
            )
        )

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
                issues.append(
                    _issue(
                        "STATE_IDLE_CHECKPOINT_DIRTY",
                        field,
                        actual,
                        "null while work_state=idle",
                        "Clear active checkpoint references during Distill.",
                    )
                )
        return issues

    if not work_id:
        issues.append(
            _issue(
                "STATE_WORK_ID_MISSING",
                "work",
                work_id,
                "non-empty Work id",
                "Assign a stable Work id before Dispatch.",
            )
        )

    catalog = build_catalog(framework_root, str(workflow) if workflow else None)
    if not workflow:
        issues.append(
            _issue(
                "STATE_WORKFLOW_MISSING",
                "workflow",
                workflow,
                "Framework Workflow file stem",
                "Select one Primary Workflow from policies/routing.md.",
            )
        )
    elif workflow not in catalog["workflows"]:
        issues.append(
            _issue(
                "STATE_WORKFLOW_UNKNOWN",
                "workflow",
                workflow,
                ", ".join(catalog["workflows"]),
                "Use the exact framework/workflows/*.md file stem.",
            )
        )

    if not stage:
        issues.append(
            _issue(
                "STATE_STAGE_MISSING",
                "stage",
                stage,
                "current Workflow frontmatter stage",
                "Select one exact stage from the chosen Workflow frontmatter.",
            )
        )
    elif workflow in catalog["workflows"] and stage not in catalog["stages"]:
        issues.append(
            _issue(
                "STATE_STAGE_UNKNOWN",
                "stage",
                stage,
                ", ".join(catalog["stages"]),
                "Use a canonical Workflow stage from the current Workflow frontmatter.",
            )
        )

    if not agent_id:
        issues.append(
            _issue(
                "STATE_AGENT_MISSING",
                "agent.id",
                agent_id,
                "Agent Contract file stem",
                "Select one exact framework/agents/*.md file stem.",
            )
        )
    elif agent_id not in catalog["agents"]:
        issues.append(
            _issue(
                "STATE_AGENT_UNKNOWN",
                "agent.id",
                agent_id,
                ", ".join(catalog["agents"]),
                "Use a canonical Agent Contract id; put persona/session labels in agent.instance.",
            )
        )
    elif workflow in catalog["workflows"] and agent_id not in catalog["workflow_agents"]:
        issues.append(
            _issue(
                "STATE_AGENT_NOT_ALLOWED",
                "agent.id",
                agent_id,
                ", ".join(catalog["workflow_agents"]),
                "Route only an Agent declared by the current Workflow frontmatter.",
            )
        )

    if agent_state not in AGENT_STATES:
        issues.append(
            _issue(
                "STATE_AGENT_STATE_UNKNOWN",
                "agent.state",
                agent_state_raw,
                " | ".join(AGENT_STATES),
                "Use exactly one canonical agent.state value from state-contract.md.",
            )
        )
    elif work_state == "paused" and agent_state != "paused":
        issues.append(
            _issue(
                "STATE_AGENT_STATE_MISMATCH",
                "agent.state",
                agent_state,
                "paused while work_state=paused",
                "Pause the current Agent in the same State Commit.",
            )
        )
    elif work_state == "active" and agent_state not in ACTIVE_AGENT_STATES:
        issues.append(
            _issue(
                "STATE_AGENT_STATE_MISMATCH",
                "agent.state",
                agent_state,
                "active | completed | blocked while work_state=active",
                "Commit the actual dispatch boundary using a canonical active-work Agent state.",
            )
        )

    if (
        presentation_contract is not None
        and presentation_contract not in PRESENTATION_CONTRACT_STATES
    ):
        issues.append(
            _issue(
                "STATE_PRESENTATION_CONTRACT_UNKNOWN",
                "presentation_contract",
                presentation_contract,
                " | ".join(PRESENTATION_CONTRACT_STATES),
                "Use exactly one canonical presentation_contract value from state-contract.md.",
            )
        )

    ui_stages = UI_GATE_RULES.get(str(workflow) if workflow else "")
    if (
        ui_stages
        and agent_id == "frontend-dev"
        and stage in ui_stages
        and presentation_contract != "frozen"
    ):
        issues.append(
            _issue(
                "STATE_UI_DESIGN_MISSING",
                "presentation_contract",
                presentation_contract,
                "frozen before frontend-dev enters implementation stages",
                "Dispatch ui-designer to freeze the Presentation Contract before frontend-dev implements.",
            )
        )

    if (
        ui_stages
        and agent_id == "frontend-dev"
        and stage in ui_stages
        and presentation_contract == "frozen"
    ):
        contract_section = _section(work_text, "Presentation Contract")
        required_contract_fields = {
            "Status": "frozen",
            "Product Truth": None,
            "Contract Locator": None,
            "Prototype / Verification": None,
        }
        missing_fields = []
        for label, expected_value in required_contract_fields.items():
            actual_value = _labeled_value(contract_section, label)
            if expected_value is not None:
                valid = actual_value.lower() == expected_value
            else:
                valid = _usable_contract_value(actual_value)
            if not valid:
                missing_fields.append(label)
        if missing_fields:
            issues.append(
                _issue(
                    "STATE_UI_PRESENTATION_CONTRACT_INCOMPLETE",
                    "WORK.Presentation Contract",
                    ", ".join(missing_fields),
                    "Status=frozen plus Product Truth, Contract Locator, and Prototype / Verification evidence",
                    "Complete the locatable Presentation Contract evidence in WORK.md before frontend-dev dispatch.",
                )
            )

    if work_state == "active" and not _section(work_text, "Current Task"):
        issues.append(
            _issue(
                "STATE_CURRENT_TASK_MISSING",
                "WORK.Current Task",
                None,
                "current dispatch task",
                "Write the current Agent task and Done Conditions before Dispatch.",
            )
        )
    if work_state == "paused" and not _section(work_text, "Next Action"):
        issues.append(
            _issue(
                "STATE_NEXT_ACTION_MISSING",
                "WORK.Next Action",
                None,
                "one resumable Next Action",
                "Persist one concrete Next Action before pausing.",
            )
        )
    return issues


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
        print("STATE_VALID: persisted WORK/STATUS checkpoint is canonical")
        return
    for issue in issues:
        print(
            f"{issue.code}: {issue.field}={issue.actual!r}; "
            f"expected={issue.expected}; repair={issue.repair}"
        )


def main() -> int:
    parser = argparse.ArgumentParser(description="Yuan State Commit Guard")
    subparsers = parser.add_subparsers(dest="command", required=True)
    check = subparsers.add_parser("check", help="validate persisted WORK/STATUS")
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
