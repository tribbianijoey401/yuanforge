"""确定性归约为唯一 Yuan Result 的纯函数。"""

from __future__ import annotations

from typing import Any

from . import RESULTS


def budget_exhausted(work: dict[str, Any], used: dict[str, int]) -> bool:
    return bool(used.get("_exhausted", False))


def reduce_projection(projection: dict[str, Any]) -> dict[str, Any]:
    """返回 Result 与机器可读原因；分支顺序就是 Protocol 优先级。"""
    work = projection.get("work")
    errors = sorted(set(projection.get("errors", [])))
    attempts = projection.get("attempts", {})
    unknown = sorted(key for key, value in attempts.items() if value["state"] == "UNKNOWN")
    if errors or unknown or work is None:
        reasons = errors + [f"存在 UNKNOWN Side Effect：{item}" for item in unknown]
        if work is None:
            reasons.append("没有 Active Work")
        return {"result": "BLOCKED", "reasons": sorted(set(reasons))}

    if projection.get("superseded") is not None:
        return {
            "result": "BLOCKED",
            "reasons": ["用户已变更需求，当前 Work 已被不可变 Supersede Event 关闭"],
            "reason_code": "WORK_SUPERSEDED",
            "successor_required": True,
        }

    if projection.get("authorization_required"):
        return {
            "result": "WAIT_AUTH",
            "reasons": ["具体 Action 超出 Active Work Grant"],
            "authorization": projection["authorization_required"],
        }

    if budget_exhausted(work, projection.get("budgets_used", {})):
        return {"result": "BUDGET_EXIT", "reasons": ["具体 Proposal 无法放入剩余 Work Budget"]}

    unresolved = sorted(
        key for key, value in attempts.items() if value["state"] in {"PREPARED", "DISPATCHED", "OBSERVED"}
    )
    required = [item for item in work["acceptance_criteria"] if item["required"]]
    latest = projection.get("criterion_evidence", {})
    passed = {
        cid
        for cid, evidence in latest.items()
        if evidence.get("status") == "PASS" and evidence.get("current") is True
    }
    invariants_hold = all(item["criterion_id"] in passed for item in work["safety_invariants"])
    required_handoffs = work["routing"]["handoff_agents"]
    artifact_review_agents = set(work["routing"]["artifact_review_agents"])
    handoffs = projection.get("agent_handoffs", {})
    ready_handoffs = {
        agent_id
        for agent_id, handoff in handoffs.items()
        if handoff.get("status") == "READY"
        and (agent_id not in artifact_review_agents or handoff.get("current") is True)
    }
    complete = (
        all(item["id"] in passed for item in required)
        and invariants_hold
        and all(agent_id in ready_handoffs for agent_id in required_handoffs)
        and not unresolved
        and all(value["state"] in {"COMMITTED", "NOT_APPLICABLE"} for value in attempts.values())
    )
    if complete:
        return {"result": "COMPLETE", "reasons": ["全部 Completion Predicate 成立"]}

    newest_handoff = projection.get("latest_handoff")
    if newest_handoff and newest_handoff.get("status") == "NEEDS_WORK" and projection.get("legal_next_step", True):
        return {
            "result": "CORRECT",
            "reasons": [f"Agent {newest_handoff['agent_id']} 的 Handoff 要求继续修正"],
        }

    newest = projection.get("latest_evidence")
    if newest and newest.get("status") == "FAIL" and projection.get("legal_next_step", True):
        return {
            "result": "CORRECT",
            "reasons": [f"Evidence {newest['evidence_id']} 反驳了 Active Strategy"],
        }

    if projection.get("legal_next_step", True):
        reasons = []
        if unresolved:
            reasons.append("存在需要 Observation 或 Reconciliation 的 Attempt")
        unmet = sorted(item["id"] for item in required if item["id"] not in passed)
        if unmet:
            reasons.append("未满足 Acceptance Criterion：" + ", ".join(unmet))
        missing_handoffs = sorted(agent_id for agent_id in required_handoffs if agent_id not in ready_handoffs)
        if missing_handoffs:
            reasons.append("未完成或已过期的 Role Handoff：" + ", ".join(missing_handoffs))
        return {"result": "CONTINUE", "reasons": reasons or ["仍有合法工作"]}

    return {"result": "BLOCKED", "reasons": ["不存在安全合法的下一步"]}


def assert_result(value: str) -> str:
    if value not in RESULTS:
        raise AssertionError(f"Reducer Result 不合法：{value}")
    return value
