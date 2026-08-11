"""Read-only consistency signals for Yuan's persisted Work checkpoint."""

from __future__ import annotations

from typing import Any

from ..registry import Registry
from .expected_observed import Signal, WhyProvenance


def compute_state_consistency(
    snapshot: dict[str, Any],
    registry: Registry,
) -> list[Signal]:
    status = snapshot.get("status") or {}
    work = snapshot.get("work") or {}
    sources = snapshot.get("sources") or {}
    workflow_definition = snapshot.get("workflow") or {}
    work_state = str(status.get("work_state") or "unknown").lower()
    work_id = status.get("work")
    has_active_work = bool(work.get("has_active_work"))
    status_has_work = bool(work_id) or work_state in {"active", "paused"}
    issues: list[str] = []

    missing_sources = [
        path
        for path in ("docs/WORK.md", "docs/STATUS.md")
        if sources.get(path) in {"MISSING", "UNREADABLE"}
    ]
    if missing_sources:
        detail = ", ".join(
            f"{path}={sources.get(path)}" for path in missing_sources
        )
        return [
            Signal(
                signal_id="STATE_FILES_MISSING",
                level="MISSING",
                entity="project-state",
                summary=detail,
                why=WhyProvenance(
                    expected_rule="WORK and STATUS must both be readable Project State files",
                    observed=detail,
                    derived="Read-only source availability from the current snapshot",
                    check="Run Yuan update/bootstrap to create only the missing Project Documents",
                ),
            )
        ]

    canonical_issues = snapshot.get("state_validation")
    if canonical_issues is not None:
        if not canonical_issues:
            return []
        details = "; ".join(
            f"{issue.get('code')}: {issue.get('field')}={issue.get('actual')!r}; "
            f"repair={issue.get('repair')}"
            for issue in canonical_issues
        )
        return [
            Signal(
                signal_id="STATE_DIVERGENCE",
                level="INCONSISTENT",
                entity="project-state",
                summary=details,
                why=WhyProvenance(
                    expected_rule="framework://policies/state-contract.md",
                    observed=details,
                    derived="framework://tools/state_guard.py read-only validation",
                    check="Have Conductor repair the same State Commit; do not dispatch until STATE_VALID",
                ),
            )
        ]

    if has_active_work and not status_has_work:
        issues.append("WORK has an Active Goal but STATUS is idle or unknown")
    if status_has_work and not has_active_work:
        issues.append("STATUS declares Active/Paused Work but WORK has no Active Goal")
    if not status_has_work:
        return _signals(issues)

    workflow_id = status.get("workflow")
    stage = status.get("stage")
    agent = status.get("agent") or {}
    agent_id = agent.get("id")
    agent_state = str(agent.get("state") or "unknown").lower()

    if work_state not in {"active", "paused"}:
        issues.append(f"unsupported work_state={work_state}")
    if not work_id:
        issues.append("missing work id")
    if not workflow_id:
        issues.append("missing workflow")
    elif workflow_id not in registry.workflows:
        issues.append(f"unknown workflow={workflow_id}")
    if not stage:
        issues.append("missing stage")
    elif workflow_id and workflow_definition.get("workflow_id") == workflow_id:
        stages = workflow_definition.get("stages") or []
        if stage not in stages:
            issues.append(f"stage={stage} is not declared by workflow={workflow_id}")
    if not agent_id:
        issues.append("missing agent.id")
    elif agent_id not in registry.agent_ids():
        issues.append(f"unknown agent.id={agent_id}")
    if work_state == "paused" and agent_state != "paused":
        issues.append("paused Work requires agent.state=paused")
    if work_state == "active" and not work.get("current_task"):
        issues.append("Active Work is missing Current Task")
    if work_state == "paused" and not work.get("next_action"):
        issues.append("Paused Work is missing Next Action")
    return _signals(issues)


def _signals(issues: list[str]) -> list[Signal]:
    if not issues:
        return []
    return [
        Signal(
            signal_id="STATE_DIVERGENCE",
            level="INCONSISTENT",
            entity="project-state",
            summary="; ".join(issues),
            why=WhyProvenance(
                expected_rule=(
                    "Conductor must atomically maintain WORK/STATUS at every "
                    "activation, dispatch, result, transition, pause, and resume"
                ),
                observed="; ".join(issues),
                derived="Read-only comparison of the current WORK and STATUS snapshot",
                check="Have Conductor reconcile the persisted checkpoint before dispatch",
            ),
        )
    ]
