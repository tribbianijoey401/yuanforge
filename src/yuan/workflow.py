"""Work Intake、确认、风险路由绑定与角色交接语义。"""

from __future__ import annotations

import copy
from datetime import datetime, timezone
from typing import Any

from .canonical import digest, verify_digest
from .primitives import identifier as _identifier, require as _require, sha256 as _sha256


RISK_LEVELS = {"R0", "R1", "R2"}
PHASES = {"intake", "design", "implementation", "review", "verification", "handoff"}


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def intake_subject(value: dict[str, Any]) -> dict[str, Any]:
    return {key: copy.deepcopy(item) for key, item in value.items() if key not in {"confirmation", "digest"}}


def validate_intake(
    value: Any,
    *,
    require_digest: bool = True,
    require_confirmation: bool = False,
) -> dict[str, Any]:
    required = {
        "schema_version", "request", "questions", "assumptions", "risk",
        "signals", "confirmation", "created_at", "digest",
    }
    _require(isinstance(value, dict) and set(value) == required, "Intake 字段不合法")
    _require(value["schema_version"] == "yuan.intake/v1", "Intake Schema Version 不受支持")
    _require(isinstance(value["request"], str) and value["request"].strip(), "Intake request 不能为空")
    questions = value["questions"]
    _require(isinstance(questions, list), "Intake questions 必须是 List")
    question_ids: set[str] = set()
    for question in questions:
        _require(
            isinstance(question, dict) and set(question) == {"id", "question", "blocking", "answer"},
            "Intake Question 字段不合法",
        )
        qid = _identifier(question["id"], "question.id")
        _require(qid not in question_ids, "Intake Question id 重复")
        question_ids.add(qid)
        _require(isinstance(question["question"], str) and question["question"].strip(), "问题不能为空")
        _require(isinstance(question["blocking"], bool), "question.blocking 必须是 Boolean")
        _require(question["answer"] is None or isinstance(question["answer"], str), "question.answer 不合法")
    assumptions = value["assumptions"]
    _require(isinstance(assumptions, list), "Intake assumptions 必须是 List")
    assumption_ids: set[str] = set()
    for assumption in assumptions:
        _require(
            isinstance(assumption, dict) and set(assumption) == {"id", "assumption", "impact"},
            "Intake Assumption 字段不合法",
        )
        aid = _identifier(assumption["id"], "assumption.id")
        _require(aid not in assumption_ids, "Intake Assumption id 重复")
        assumption_ids.add(aid)
        _require(
            all(isinstance(assumption[name], str) and assumption[name].strip() for name in ("assumption", "impact")),
            "Assumption 文本不能为空",
        )
    risk = value["risk"]
    _require(isinstance(risk, dict) and set(risk) == {"level", "rationale"}, "Intake risk 字段不合法")
    _require(risk["level"] in RISK_LEVELS, "Intake risk.level 不合法")
    _require(isinstance(risk["rationale"], str) and risk["rationale"].strip(), "Risk rationale 不能为空")
    signals = value["signals"]
    _require(isinstance(signals, list) and len(signals) == len(set(signals)), "Intake signals 不合法")
    for signal in signals:
        _identifier(signal, "signal")
    _require(isinstance(value["created_at"], str) and value["created_at"], "Intake created_at 不合法")
    confirmation = value["confirmation"]
    if confirmation is not None:
        _require(
            isinstance(confirmation, dict)
            and set(confirmation) == {"status", "statement", "subject_digest", "created_at"},
            "Intake Confirmation 字段不合法",
        )
        _require(confirmation["status"] == "CONFIRMED", "Intake Confirmation Status 不合法")
        _require(isinstance(confirmation["statement"], str) and confirmation["statement"].strip(), "确认声明不能为空")
        _sha256(confirmation["subject_digest"], "confirmation.subject_digest")
        _require(
            confirmation["subject_digest"] == digest(intake_subject(value)),
            "Intake Confirmation 没有绑定当前需求、答案、假设和风险",
        )
        _require(isinstance(confirmation["created_at"], str) and confirmation["created_at"], "确认时间不合法")
    if require_confirmation:
        _require(confirmation is not None, "Intake 尚未获得用户确认")
        unanswered = [item["id"] for item in questions if item["blocking"] and not (item["answer"] or "").strip()]
        _require(not unanswered, "仍有未回答的阻塞问题：" + ", ".join(unanswered))
    if require_digest:
        _require(verify_digest(value), "Intake digest 不匹配")
    return value


def intake_template(request: str) -> dict[str, Any]:
    value = {
        "schema_version": "yuan.intake/v1",
        "request": request,
        "questions": [],
        "assumptions": [],
        "risk": {"level": "R1", "rationale": "待根据影响范围确认。"},
        "signals": [],
        "confirmation": None,
        "created_at": _utc_now(),
    }
    value["digest"] = digest(value, ("digest",))
    return value


def intake_summary(value: dict[str, Any]) -> dict[str, Any]:
    validate_intake(value)
    return {
        "request": value["request"],
        "questions": [
            {
                "id": item["id"],
                "question": item["question"],
                "blocking": item["blocking"],
                "answer": item["answer"],
            }
            for item in value["questions"]
        ],
        "assumptions": copy.deepcopy(value["assumptions"]),
        "risk": copy.deepcopy(value["risk"]),
        "signals": copy.deepcopy(value["signals"]),
        "subject_digest": digest(intake_subject(value)),
    }


def intake_decision(value: dict[str, Any]) -> dict[str, Any]:
    validate_intake(value)
    unanswered = [item["id"] for item in value["questions"] if item["blocking"] and not (item["answer"] or "").strip()]
    if unanswered:
        return {"result": "BLOCKED", "reason_code": "NEEDS_INPUT", "questions": unanswered}
    if value["confirmation"] is None:
        return {
            "result": "BLOCKED",
            "reason_code": "NEEDS_CONFIRMATION",
            "confirmation_required": "intake",
            "summary": intake_summary(value),
        }
    validate_intake(value, require_confirmation=True)
    return {"result": "CONTINUE", "reason_code": "INTAKE_CONFIRMED", "intake_digest": value["digest"]}


def confirm_intake(value: dict[str, Any], statement: str) -> dict[str, Any]:
    draft = copy.deepcopy(value)
    draft["confirmation"] = None
    draft["digest"] = digest(draft, ("digest",))
    validate_intake(draft)
    unanswered = [item["id"] for item in draft["questions"] if item["blocking"] and not (item["answer"] or "").strip()]
    _require(not unanswered, "仍有未回答的阻塞问题：" + ", ".join(unanswered))
    _require(isinstance(statement, str) and statement.strip(), "用户确认声明不能为空")
    draft["confirmation"] = {
        "status": "CONFIRMED",
        "statement": statement.strip(),
        "subject_digest": digest(intake_subject(draft)),
        "created_at": _utc_now(),
    }
    draft["digest"] = digest(draft, ("digest",))
    return validate_intake(draft, require_confirmation=True)


def validate_routing(value: Any) -> dict[str, Any]:
    required = {
        "schema_version", "profile_id", "profile_digest", "risk", "signals",
        "agents", "skills", "handoff_agents", "artifact_review_agents", "digest",
    }
    _require(isinstance(value, dict) and set(value) == required, "Routing 字段不合法")
    _require(value["schema_version"] == "yuan.routing/v1", "Routing Schema Version 不受支持")
    _identifier(value["profile_id"], "routing.profile_id")
    _sha256(value["profile_digest"], "routing.profile_digest")
    _require(value["risk"] in RISK_LEVELS, "Routing risk 不合法")
    for name in ("signals", "agents", "skills", "handoff_agents", "artifact_review_agents"):
        items = value[name]
        _require(isinstance(items, list) and len(items) == len(set(items)), f"Routing {name} 不合法")
        for item in items:
            _identifier(item, f"routing.{name}")
    _require(set(value["handoff_agents"]) <= set(value["agents"]), "Handoff Agent 不在 Routing Agents 中")
    _require(set(value["artifact_review_agents"]) <= set(value["handoff_agents"]), "Artifact Reviewer 不在 Handoff Agents 中")
    _require(verify_digest(value), "Routing digest 不匹配")
    return value


def work_subject(value: dict[str, Any]) -> dict[str, Any]:
    return {key: copy.deepcopy(item) for key, item in value.items() if key not in {"confirmation", "digest", "created_at"}}


def validate_work_confirmation(value: Any, work: dict[str, Any], *, required: bool) -> None:
    if value is None:
        _require(not required, "Work 尚未获得用户最终确认")
        return
    _require(
        isinstance(value, dict) and set(value) == {"status", "statement", "subject_digest", "created_at"},
        "Work Confirmation 字段不合法",
    )
    _require(value["status"] == "CONFIRMED", "Work Confirmation Status 不合法")
    _require(isinstance(value["statement"], str) and value["statement"].strip(), "Work 确认声明不能为空")
    _require(value["subject_digest"] == digest(work_subject(work)), "Work Confirmation 没有绑定当前完整契约")
    _require(isinstance(value["created_at"], str) and value["created_at"], "Work 确认时间不合法")


def confirm_work(work: dict[str, Any], statement: str) -> dict[str, Any]:
    _require(isinstance(statement, str) and statement.strip(), "用户确认声明不能为空")
    value = copy.deepcopy(work)
    value["confirmation"] = None
    value["digest"] = digest(value, ("digest",))
    value["confirmation"] = {
        "status": "CONFIRMED",
        "statement": statement.strip(),
        "subject_digest": digest(work_subject(value)),
        "created_at": _utc_now(),
    }
    value["digest"] = digest(value, ("digest",))
    return value


def validate_handoff(value: Any, work: dict[str, Any]) -> dict[str, Any]:
    required = {
        "schema_version", "handoff_id", "work", "agent_id", "to_agent_id", "phase",
        "status", "summary", "artifact_digest", "evidence_ids", "created_at", "digest",
    }
    _require(isinstance(value, dict) and set(value) == required, "Role Handoff 字段不合法")
    _require(value["schema_version"] == "yuan.handoff/v1", "Role Handoff Schema Version 不受支持")
    _identifier(value["handoff_id"], "handoff_id")
    _require(
        value["work"] == {"id": work["work_id"], "revision": work["revision"], "digest": work["digest"]},
        "Role Handoff Work Binding 不匹配",
    )
    _identifier(value["agent_id"], "handoff.agent_id")
    _identifier(value["to_agent_id"], "handoff.to_agent_id")
    _require(value["agent_id"] in work["routing"]["handoff_agents"], "Agent 不需要或不允许提交 Handoff")
    _require(value["to_agent_id"] == "user" or value["to_agent_id"] in work["routing"]["agents"], "Handoff 目标不在 Routing 中")
    _require(value["phase"] in PHASES, "Handoff phase 不合法")
    _require(value["status"] in {"READY", "NEEDS_WORK"}, "Handoff status 不合法")
    _require(isinstance(value["summary"], str) and value["summary"].strip(), "Handoff summary 不能为空")
    _sha256(value["artifact_digest"], "handoff.artifact_digest")
    _require(isinstance(value["evidence_ids"], list) and len(value["evidence_ids"]) == len(set(value["evidence_ids"])), "Handoff evidence_ids 不合法")
    if value["agent_id"] in work["routing"]["artifact_review_agents"] and value["status"] == "READY":
        _require(bool(value["evidence_ids"]), "Artifact Reviewer 的 READY Handoff 必须引用当前 Evidence")
    for evidence_id in value["evidence_ids"]:
        _identifier(evidence_id, "handoff.evidence_id")
    _require(isinstance(value["created_at"], str) and value["created_at"], "Handoff created_at 不合法")
    _require(verify_digest(value), "Role Handoff digest 不匹配")
    return value
