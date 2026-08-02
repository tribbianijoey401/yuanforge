"""Yuan Record 的轻量语义校验器。

JSON Schema 用于描述交换格式；本模块是不依赖第三方库的规范性运行时校验。
"""

from __future__ import annotations

import re
from typing import Any

from .canonical import digest, verify_digest
from .errors import ValidationError
from .paths import normalize_relative, scope_contains

SHA256 = re.compile(r"^[0-9a-f]{64}$")
IDENT = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")
ACTION_TYPES = {"file-read", "file-write", "command", "verify", "reconcile"}
SIDE_EFFECTS = {"none", "filesystem", "process", "network", "external"}
PROFILES = {"GUIDED", "AUDITED", "ENFORCED"}


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValidationError(message)


def require_keys(value: dict[str, Any], required: set[str], label: str) -> None:
    missing = sorted(required - set(value))
    require(not missing, f"{label} 缺少字段：{', '.join(missing)}")


def identifier(value: Any, label: str) -> str:
    require(isinstance(value, str) and bool(IDENT.fullmatch(value)), f"{label} 不合法")
    return value


def sha256(value: Any, label: str) -> str:
    require(isinstance(value, str) and bool(SHA256.fullmatch(value)), f"{label} 不是合法的 SHA-256")
    return value


def binding(value: Any, label: str) -> dict[str, Any]:
    require(isinstance(value, dict), f"{label} 必须是 Object")
    require_keys(value, {"id", "revision", "digest"}, label)
    identifier(value["id"], f"{label}.id")
    identifier(value["revision"], f"{label}.revision")
    sha256(value["digest"], f"{label}.digest")
    return value


def validate_work(value: Any, *, require_digest: bool = True) -> dict[str, Any]:
    require(isinstance(value, dict), "Work 必须是 Object")
    require_keys(
        value,
        {
            "schema_version", "work_id", "revision", "goal", "profile",
            "protocol", "harness", "artifact", "acceptance_criteria",
            "safety_invariants", "grants", "budgets", "predecessor", "created_at",
        },
        "Work",
    )
    require(value["schema_version"] == "yuan.work/v1", "不支持该 Work Schema")
    identifier(value["work_id"], "work_id")
    require(isinstance(value["revision"], int) and value["revision"] > 0, "Work revision 不合法")
    require(isinstance(value["goal"], str) and value["goal"].strip(), "goal 不能为空")
    require(value["profile"] in PROFILES, "profile 不合法")
    binding(value["protocol"], "protocol")
    binding(value["harness"], "harness")
    predecessor = value["predecessor"]
    if predecessor is not None:
        require(isinstance(predecessor, dict), "predecessor 必须是 Object 或 null")
        require(
            set(predecessor) == {"run_id", "work_digest", "result", "head_digest"},
            "predecessor 字段不合法",
        )
        identifier(predecessor["run_id"], "predecessor.run_id")
        sha256(predecessor["work_digest"], "predecessor.work_digest")
        sha256(predecessor["head_digest"], "predecessor.head_digest")
        require(
            predecessor["result"] in {"CONTINUE", "CORRECT", "COMPLETE", "BLOCKED", "WAIT_AUTH", "BUDGET_EXIT"},
            "predecessor.result 不合法",
        )
    artifact = value["artifact"]
    require(isinstance(artifact, dict), "artifact 必须是 Object")
    require_keys(artifact, {"root", "include", "exclude", "environment"}, "artifact")
    require(artifact["root"] == ".", "当前只支持仓库根目录 Artifact")
    require(isinstance(artifact["include"], list) and artifact["include"], "artifact.include 不能为空")
    require(isinstance(artifact["exclude"], list), "artifact.exclude 必须是 List")
    for pattern in artifact["include"] + artifact["exclude"]:
        require(isinstance(pattern, str) and pattern and "\\" not in pattern, "Artifact Pattern 不合法")
        require(not pattern.startswith("/") and ".." not in pattern.split("/"), "Artifact Pattern 不安全")
    binding(artifact["environment"], "artifact.environment")

    criteria = value["acceptance_criteria"]
    require(isinstance(criteria, list) and criteria, "acceptance_criteria 不能为空")
    seen: set[str] = set()
    for item in criteria:
        require(isinstance(item, dict), "Acceptance Criterion 必须是 Object")
        require_keys(item, {"id", "description", "required", "verifier", "min_assertions", "independence"}, "criterion")
        cid = identifier(item["id"], "criterion.id")
        require(cid not in seen, "Acceptance Criterion id 重复")
        seen.add(cid)
        require(isinstance(item["description"], str) and item["description"].strip(), "Criterion description 不能为空")
        require(isinstance(item["required"], bool), "criterion.required 必须是 Boolean")
        binding(item["verifier"], "criterion.verifier")
        verifier = item["verifier"]
        require(verifier.get("kind") == "python-script", "不支持该 Verifier kind")
        normalize_relative(verifier.get("entrypoint"))
        require(isinstance(verifier.get("timeout_seconds"), int) and 0 < verifier["timeout_seconds"] <= 600, "Verifier timeout 不合法")
        files = verifier.get("files")
        require(isinstance(files, list) and files, "Verifier File Closure 不能为空")
        paths = []
        for file in files:
            require(isinstance(file, dict) and set(file) == {"path", "digest"}, "Verifier File Binding 不合法")
            paths.append(normalize_relative(file["path"]))
            sha256(file["digest"], "Verifier File digest")
        require(len(paths) == len(set(paths)), "Verifier Closure Path 重复")
        require(verifier["entrypoint"] in paths, "Verifier entrypoint 不在其 Closure 内")
        closure = {"kind": verifier["kind"], "entrypoint": verifier["entrypoint"], "files": files}
        require(verifier["digest"] == digest(closure), "Verifier Closure digest 不匹配")
        require(isinstance(item["min_assertions"], int) and item["min_assertions"] > 0, "min_assertions 必须为正数")
        require(item["independence"] in {"independent", "previous-root", "external"}, "independence 不合法")

    invariants = value["safety_invariants"]
    require(isinstance(invariants, list), "safety_invariants 必须是 List")
    invariant_ids = set()
    for item in invariants:
        require(isinstance(item, dict), "Safety Invariant 必须是 Object")
        require_keys(item, {"id", "description", "criterion_id"}, "Safety Invariant")
        iid = identifier(item["id"], "Safety Invariant.id")
        require(iid not in invariant_ids, "Safety Invariant id 重复")
        invariant_ids.add(iid)
        require(item["criterion_id"] in seen, "Safety Invariant 引用了未知 Criterion")

    grants = value["grants"]
    require(isinstance(grants, list), "grants 必须是 List")
    grant_ids = set()
    for grant in grants:
        require(isinstance(grant, dict), "Grant 必须是 Object")
        require_keys(grant, {"id", "action_types", "side_effect_classes", "scopes"}, "grant")
        gid = identifier(grant["id"], "grant.id")
        require(gid not in grant_ids, "Grant id 重复")
        grant_ids.add(gid)
        require(isinstance(grant["action_types"], list) and set(grant["action_types"]) <= ACTION_TYPES, "Grant action_types 不合法")
        require(isinstance(grant["side_effect_classes"], list) and set(grant["side_effect_classes"]) <= SIDE_EFFECTS, "Grant side_effect_classes 不合法")
        require(isinstance(grant["scopes"], list) and grant["scopes"], "Grant scopes 不能为空")
        for scope in grant["scopes"]:
            normalize_relative(scope)

    budgets = value["budgets"]
    require(isinstance(budgets, dict), "budgets 必须是 Object")
    require_keys(budgets, {"ticks", "attempts", "tool_calls", "command_seconds"}, "budgets")
    for name, amount in budgets.items():
        require(isinstance(amount, int) and amount >= 0, f"Budget 不合法：{name}")
    if require_digest:
        require(verify_digest(value), "Work digest 不匹配")
    return value


def validate_proposal(value: Any) -> dict[str, Any]:
    require(isinstance(value, dict), "Proposal 必须是 Object")
    require_keys(value, {"attempt_id", "strategy", "hypothesis", "relevant_inputs", "action", "budget_charge"}, "proposal")
    identifier(value["attempt_id"], "attempt_id")
    require(isinstance(value["strategy"], str) and value["strategy"].strip(), "strategy 不能为空")
    require(isinstance(value["hypothesis"], dict), "hypothesis 必须是 Object")
    require_keys(value["hypothesis"], {"claim", "falsification"}, "hypothesis")
    require(all(isinstance(value["hypothesis"][key], str) and value["hypothesis"][key].strip() for key in ("claim", "falsification")), "hypothesis 文本不能为空")
    require(isinstance(value["relevant_inputs"], list), "relevant_inputs 必须是 List")
    for item in value["relevant_inputs"]:
        require(isinstance(item, dict), "Relevant Input 必须是 Object")
        require_keys(item, {"path", "digest"}, "Relevant Input")
        normalize_relative(item["path"])
        sha256(item["digest"], "Relevant Input digest")
    action = value["action"]
    require(isinstance(action, dict), "action 必须是 Object")
    require_keys(action, {"type", "mutating", "side_effect_class", "paths", "grant_id", "high_impact"}, "action")
    require(action["type"] in ACTION_TYPES, "Action type 不合法")
    require(isinstance(action["mutating"], bool), "action.mutating 必须是 Boolean")
    require(action["side_effect_class"] in SIDE_EFFECTS, "side_effect_class 不合法")
    require(isinstance(action["paths"], list), "action.paths 必须是 List")
    for path in action["paths"]:
        normalize_relative(path)
    if action["mutating"]:
        require(bool(action["paths"]), "Mutating Action 必须声明 paths")
        require(action["side_effect_class"] != "none", "Mutating Action 必须声明副作用类别")
    require(action["grant_id"] is None or isinstance(action["grant_id"], str), "grant_id 不合法")
    require(isinstance(action["high_impact"], bool), "high_impact 必须是 Boolean")
    reconciliation = value.get("reconciliation")
    if action["type"] == "reconcile":
        require(not action["mutating"], "Reconciliation Attempt 必须是只读动作")
        require(action["side_effect_class"] == "none", "Reconciliation Attempt 不得声明副作用")
        require(isinstance(reconciliation, dict), "Reconciliation Attempt 缺少 reconciliation Binding")
        require(set(reconciliation) == {"target_attempt_id"}, "reconciliation 字段不合法")
        identifier(reconciliation["target_attempt_id"], "reconciliation.target_attempt_id")
    else:
        require(reconciliation is None, "普通 Attempt 不得携带 reconciliation Binding")
    charges = value["budget_charge"]
    require(isinstance(charges, dict), "budget_charge 必须是 Object")
    require(set(charges) == {"ticks", "attempts", "tool_calls", "command_seconds"}, "budget_charge 字段不合法")
    for key in ("ticks", "attempts", "tool_calls", "command_seconds"):
        require(isinstance(charges.get(key), int) and charges[key] >= 0, f"Charge 不合法：{key}")
    require(charges["ticks"] == 1 and charges["attempts"] == 1, "每个 Attempt 必须恰好消耗一个 Tick 和一个 Attempt")
    return value


def action_authorized(work: dict[str, Any], action: dict[str, Any]) -> bool:
    if not action["mutating"]:
        return True
    if action["high_impact"] or not action["grant_id"]:
        return False
    matches = [grant for grant in work["grants"] if grant["id"] == action["grant_id"]]
    if len(matches) != 1:
        return False
    grant = matches[0]
    return (
        action["type"] in grant["action_types"]
        and action["side_effect_class"] in grant["side_effect_classes"]
        and all(any(scope_contains(scope, path) for scope in grant["scopes"]) for path in action["paths"])
    )


def validate_evidence(value: Any, work: dict[str, Any], artifact_digest: str) -> dict[str, Any]:
    require(isinstance(value, dict), "Evidence 必须是 Object")
    require_keys(value, {"schema_version", "evidence_id", "work", "attempt_id", "criterion_id", "artifact", "environment", "harness", "verifier", "status", "assertions", "receipt", "independence", "created_at", "digest"}, "Evidence")
    require(value["schema_version"] == "yuan.evidence/v1", "不支持该 Evidence Schema")
    identifier(value["evidence_id"], "evidence_id")
    identifier(value["attempt_id"], "attempt_id")
    require(value["work"] == {"id": work["work_id"], "revision": work["revision"], "digest": work["digest"]}, "Evidence Work Binding 不匹配")
    criteria = [item for item in work["acceptance_criteria"] if item["id"] == value["criterion_id"]]
    require(len(criteria) == 1, "Evidence Criterion 未被 Work 唯一绑定")
    criterion = criteria[0]
    require(value["artifact"] == {"scope": work["artifact"]["root"], "digest": artifact_digest}, "Evidence Artifact 已过期或超出 Scope")
    sha256(value["artifact"]["digest"], "Evidence Artifact digest")
    require(value["environment"] == work["artifact"]["environment"], "Evidence Environment 不匹配")
    require(value["harness"] == work["harness"], "Evidence Harness 不匹配")
    require(value["verifier"] == criterion["verifier"], "Evidence Verifier 不匹配")
    require(value["status"] in {"PASS", "FAIL"}, "Evidence status 不合法")
    assertions = value["assertions"]
    require(isinstance(assertions, list) and len(assertions) >= criterion["min_assertions"], "Evidence 的 Assertion 数量不足")
    ids = []
    for assertion in assertions:
        require(isinstance(assertion, dict), "Assertion 必须是 Object")
        require_keys(assertion, {"id", "passed"}, "assertion")
        ids.append(identifier(assertion["id"], "assertion.id"))
        require(isinstance(assertion["passed"], bool), "assertion.passed 必须是 Boolean")
    require(len(ids) == len(set(ids)), "Assertion id 重复")
    if value["status"] == "PASS":
        require(all(item["passed"] for item in assertions), "PASS Evidence 包含失败 Assertion")
    else:
        require(any(not item["passed"] for item in assertions), "FAIL Evidence 不包含失败 Assertion")
    receipt = value["receipt"]
    require(isinstance(receipt, dict), "Evidence receipt 必须是 Object")
    require_keys(receipt, {"tool", "stdout", "stderr"}, "Evidence receipt")
    for name in ("tool", "stdout", "stderr"):
        sha256(receipt[name], f"receipt.{name}")
    require(value["independence"] == criterion["independence"], "Evidence independence 不匹配")
    require(verify_digest(value), "Evidence digest 不匹配")
    return value


def with_digest(value: dict[str, Any]) -> dict[str, Any]:
    result = dict(value)
    result["digest"] = digest(result, ("digest",))
    return result
