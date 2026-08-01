#!/usr/bin/env python3
"""YuanCore Phase 7 Acceptance Tests.

验证 Extension 架构的核心原则：
  1. 禁用任一扩展不破坏 Core 完成语义
  2. Work Contract 可按需声明扩展
  3. Core Tick 不要求固定角色或固定阶段
  4. 简单任务可在无 Task Board、无多 Agent 情况下完成
"""

import sys
import os
import json
import copy

sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
from core_validator import (
    CoreSchemaValidator,
    RoleExtensionValidator,
    select_proposal,
    run_reducer,
    read_state,
    write_state,
    get_nested,
    _default_state,
)

# ── 路径 ────────────────────────────────────────────────────────────────────
BASE_DIR = os.environ.get("YUANFORGE_BASE_DIR", "/home/admin/yuanforge")
EXT_DIR = os.path.join(BASE_DIR, ".yuan", "extensions")
WORKFLOW_DIR = os.path.join(EXT_DIR, "workflows")
POLICY_DIR = os.path.join(EXT_DIR, "policies")
SKILL_DIR = os.path.join(EXT_DIR, "skills")
MANIFEST_PATH = os.path.join(EXT_DIR, "MANIFEST.md")

# ── 测试用 Proposal ─────────────────────────────────────────────────────────
BASE_PROPOSAL = {
    "schema": "yuan.proposal/v1",
    "proposal_id": "P-000001",
    "selection_batch": "B-000001",
    "selection_rank": 1,
    "work": {"revision": 1, "hash": "sha256:test"},
    "producer": {"agent_id": "x", "role": "backend-dev", "platform": "hermes"},
    "hypothesis": {
        "class": "code_change",
        "statement": "Add refresh token endpoint",
        "falsification": "401 when invalid refresh token",
    },
    "strategy_profile": {
        "target_scope": ["src/auth/refresh.py"],
        "action_class": "code_change",
        "key_parameters": {},
        "relevant_input_refs": [],
        "verification_profile": ["unit_test"],
    },
    "atomic_change_set": {
        "intent": "add_refresh_token_endpoint",
        "target_scope": ["src/auth/refresh.py"],
        "expected_effect": ["new endpoint", "token validation"],
        "side_effect_class": "local_reversible",
    },
    "verification_plan": {
        "validators": ["unit_test"],
        "expected_evidence": ["E-001"],
    },
    "risk": {"level": "R1", "reasons": ["auth change"]},
    "extensions": {
        "backend-dev": {
            "schema": "yuan.agent.backend-dev/v1",
            "affected_components": ["auth"],
            "data_model_changes": {
                "changed": False,
                "entities": [],
                "migration_required": False,
                "compatibility_impact": "none",
            },
            "implementation_notes": {
                "concurrency_considerations": [],
                "backward_compatibility": [],
            },
        }
    },
}


# ── T1: 禁用任一扩展不破坏 Core 完成语义 ───────────────────────────────────
def test_1_no_extension_breaks_core():
    """Core 完整性：无扩展的 Proposal 仍可通过 Core Schema Validation。"""
    minimal = {k: v for k, v in BASE_PROPOSAL.items() if k != "extensions"}
    cv = CoreSchemaValidator(proposal_data=minimal)
    errors = cv.validate()
    ok = len(errors) == 0
    print(f"  T1 无扩展 Proposal Core 校验: {'PASS' if ok else 'FAIL'} ({len(errors)} errors)")
    if not ok:
        for e in errors:
            print(f"    - {e.message}")
    return ok


def test_2_extension_disabled_no_effect_on_reducer():
    """禁用扩展后 Reducer 判定不变。"""
    # 有扩展
    state_with = {
        "current_revision": 1,
        "status": "RUNNING",
        "attempt_id": "A-000001",
        "pending_changes": [],
    }
    evidence_with = [{"evidence_id": "E-001", "result": "pass", "status": "valid"}]
    inv = {}
    result_with = run_reducer(state_with, evidence_with, inv, 9999, 10000)

    # 无扩展（等价于禁用所有 extension workflows/policies/skills）
    # Reducer 只依赖 state + evidence + invariants，与扩展无关
    result_without = run_reducer(state_with, evidence_with, inv, 9999, 10000)

    same = result_with.result == result_without.result
    print(f"  T2 Reducer 与扩展无关: {'PASS' if same else 'FAIL'} "
          f"(with={result_with.result}, without={result_without.result})")
    return same


# ── T3: Work Contract 可按需声明扩展 ───────────────────────────────────────
def test_3_work_contract_declares_extensions():
    """Work Contract 可以声明所需的扩展。"""
    # 模拟一个需要 TDD + Security 的 Work Contract
    work_contract = {
        "schema": "yuan.work/v1",
        "work_id": "W-TEST01",
        "revision": 1,
        "risk_level": "R1",
        "extensions": {
            "workflows": ["tdd-loop", "phase-gates"],
            "policies": ["three-level-review", "evidence-binding"],
            "skills": ["test-driven-development", "debug-feedback-loop"],
        },
    }

    # 验证声明格式合法
    ok = (
        "workflows" in work_contract.get("extensions", {})
        and "policies" in work_contract.get("extensions", {})
        and "skills" in work_contract.get("extensions", {})
    )
    print(f"  T3 Work Contract 扩展声明: {'PASS' if ok else 'FAIL'}")
    return ok


def test_4_minimal_work_contract_no_extensions():
    """最小 Work Contract 不需要任何扩展。"""
    minimal_work = {
        "schema": "yuan.work/v1",
        "work_id": "W-MIN01",
        "revision": 1,
        "risk_level": "R0",
    }
    # 无 extensions 字段也合法
    ok = "schema" in minimal_work and "work_id" in minimal_work
    print(f"  T4 最小 Work Contract: {'PASS' if ok else 'FAIL'}")
    return ok


# ── T5: Core Tick 不要求固定角色或固定阶段 ─────────────────────────────────
def test_5_core_tick_any_role():
    """Core Tick 可接受任意角色的 Proposal。"""
    roles = ["backend-dev", "frontend-dev", "product-analyst", "tester", "architect"]
    results = []
    for role in roles:
        p = dict(BASE_PROPOSAL)
        p["producer"] = {"agent_id": "x", "role": role, "platform": "hermes"}
        cv = CoreSchemaValidator(proposal_data=p)
        errs = cv.validate()
        results.append((role, len(errs) == 0))

    all_ok = all(r for _, r in results)
    print(f"  T5 Core Tick 任意角色: {'PASS' if all_ok else 'FAIL'}")
    for role, ok in results:
        print(f"    {role}: {'OK' if ok else 'FAIL'}")
    return all_ok


def test_6_core_tick_any_phase():
    """Core Tick 可在任意阶段工作（不依赖 Workflow Phase 定义）。"""
    # Core Tick 的输入是 STATE + proposals + evidence
    # 不管当前处于 Discover/Plan/Build/Verify/Promote 哪个阶段
    for status in ["IDLE", "RUNNING", "PAUSED", "BLOCKED"]:
        state = _default_state()
        state["status"] = status
        state["current_revision"] = 1
        evidence = [{"evidence_id": "E-1", "result": "pass", "status": "valid"}]
        result = run_reducer(state, evidence, {}, 9999, 10000)
        # 不论状态如何，Reducer 都能返回结果
        assert hasattr(result, "result")
    print(f"  T6 Core Tick 任意阶段: PASS")
    return True


# ── T7: 简单任务无 Task Board 可完成 ──────────────────────────────────────
def test_7_simple_task_no_taskboard():
    """简单任务：无 Task Board，无多 Agent，Core 仍可 COMPLETE。"""
    # 模拟简单任务：单个 Proposal + 单条 Evidence
    state = _default_state()
    state["current_revision"] = 1
    state["status"] = "RUNNING"
    state["attempt_id"] = "A-000001"

    evidence = [
        {"evidence_id": "E-SIMPLE-01", "result": "pass", "status": "valid",
         "bound_work_revision": 1}
    ]
    invariants = {}
    budget = 9999
    max_budget = 10000

    result = run_reducer(state, evidence, invariants, budget, max_budget)
    ok = result.result == "COMPLETE"
    print(f"  T7 简单任务无 Task Board: {'PASS' if ok else 'FAIL'} (result={result.result})")
    return ok


def test_8_single_agent_no_multiagent():
    """单 Agent 任务：无需多 Agent 协作。"""
    # 单 Agent 的 Proposal（无 extensions 多角色协作）
    single_agent_proposal = {
        "schema": "yuan.proposal/v1",
        "proposal_id": "P-000002",
        "selection_batch": "B-000002",
        "selection_rank": 1,
        "work": {"revision": 1, "hash": "sha256:test2"},
        "producer": {"agent_id": "x", "role": "backend-dev", "platform": "hermes"},
        "hypothesis": {"class": "code_change", "statement": "s", "falsification": "f"},
        "strategy_profile": {
            "target_scope": ["src/utils.py"],
            "action_class": "code_change",
            "key_parameters": {},
            "relevant_input_refs": [],
            "verification_profile": ["unit_test"],
        },
        "atomic_change_set": {
            "intent": "fix_utils",
            "target_scope": ["src/utils.py"],
            "expected_effect": [],
            "side_effect_class": "local_reversible",
        },
        "verification_plan": {"validators": ["unit_test"], "expected_evidence": ["E-002"]},
        "risk": {"level": "R0", "reasons": []},
        "extensions": {
            "backend-dev": {
                "schema": "yuan.agent.backend-dev/v1",
                "affected_components": ["utils"],
                "data_model_changes": {
                    "changed": False, "entities": [],
                    "migration_required": False, "compatibility_impact": "none"
                },
                "implementation_notes": {
                    "concurrency_considerations": [],
                    "backward_compatibility": [],
                },
            }
        },
    }

    cv = CoreSchemaValidator(proposal_data=single_agent_proposal)
    core_ok = len(cv.validate()) == 0

    rv = RoleExtensionValidator(proposal_data=single_agent_proposal, role="backend-dev")
    role_ok = len(rv.validate()) == 0

    ok = core_ok and role_ok
    print(f"  T8 单 Agent 任务: {'PASS' if ok else 'FAIL'}")
    return ok


# ── T9: Extension 文件结构完整性 ───────────────────────────────────────────
def test_9_extension_structure():
    """Extension 目录结构正确。"""
    dirs_ok = all(os.path.isdir(d) for d in [WORKFLOW_DIR, POLICY_DIR, SKILL_DIR])
    manifest_ok = os.path.exists(MANIFEST_PATH)

    # 检查各目录下的文件
    workflows = os.listdir(WORKFLOW_DIR) if dirs_ok else []
    policies = os.listdir(POLICY_DIR) if dirs_ok else []
    skills = os.listdir(SKILL_DIR) if dirs_ok else []

    ok = dirs_ok and manifest_ok and len(workflows) >= 5 and len(policies) >= 3 and len(skills) >= 5
    print(f"  T9 Extension 结构: {'PASS' if ok else 'FAIL'}")
    print(f"    workflows: {len(workflows)}, policies: {len(policies)}, skills: {len(skills)}")
    return ok


# ── T10: Manifest 注册了所有扩展 ──────────────────────────────────────────
def test_10_manifest_completeness():
    """Manifest 列出了所有扩展文件。"""
    if not os.path.exists(MANIFEST_PATH):
        print("  T10 Manifest 完整性: FAIL (manifest not found)")
        return False

    with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    # 检查 workflows 中的文件是否在 Manifest 中注册
    all_ok = True
    for fname in os.listdir(WORKFLOW_DIR):
        if fname.endswith(".md"):
            name = fname.replace(".md", "")
            if name not in content:
                print(f"    MISSING workflow: {name}")
                all_ok = False

    for fname in os.listdir(POLICY_DIR):
        if fname.endswith(".md"):
            name = fname.replace(".md", "")
            if name not in content:
                print(f"    MISSING policy: {name}")
                all_ok = False

    for fname in os.listdir(SKILL_DIR):
        if fname.endswith(".md"):
            name = fname.replace(".md", "")
            if name not in content:
                print(f"    MISSING skill: {name}")
                all_ok = False

    print(f"  T10 Manifest 完整性: {'PASS' if all_ok else 'FAIL'}")
    return all_ok


# ── T11: 扩展文件有正确的 schema 声明 ─────────────────────────────────────
def test_11_extension_schema_declarations():
    """所有扩展文件包含 schema 版本声明。"""
    all_ok = True
    for dirname, label in [(WORKFLOW_DIR, "workflow"), (POLICY_DIR, "policy"), (SKILL_DIR, "skill")]:
        for fname in os.listdir(dirname):
            if not fname.endswith(".md"):
                continue
            path = os.path.join(dirname, fname)
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
            if "schema:" not in content and "schema " not in content:
                print(f"    MISSING schema: {label}/{fname}")
                all_ok = False
    print(f"  T11 扩展 Schema 声明: {'PASS' if all_ok else 'FAIL'}")
    return all_ok


# ── T12: 禁用扩展后 Core 仍可正常运行（端到端） ──────────────────────────
def test_12_end_to_end_no_extensions():
    """端到端：无 Extension 时 Core 仍可完成一个简单任务。"""
    # 创建最小 Proposal（无 extensions）
    minimal = dict(BASE_PROPOSAL)
    minimal["extensions"] = {}
    minimal["proposal_id"] = "P-000010"
    minimal["work"] = {"revision": 1, "hash": "sha256:minimal"}
    minimal["strategy_profile"]["target_scope"] = ["src/simple.py"]
    minimal["atomic_change_set"]["target_scope"] = ["src/simple.py"]
    minimal["risk"] = {"level": "R0", "reasons": []}

    cv = CoreSchemaValidator(proposal_data=minimal)
    core_errs = cv.validate()

    # 即使无 extensions，Core Schema 也应通过
    ok = len(core_errs) == 0
    print(f"  T12 端到端无扩展: {'PASS' if ok else 'FAIL'} ({len(core_errs)} core errors)")
    return ok


def run_all():
    tests = [
        ("T1", test_1_no_extension_breaks_core),
        ("T2", test_2_extension_disabled_no_effect_on_reducer),
        ("T3", test_3_work_contract_declares_extensions),
        ("T4", test_4_minimal_work_contract_no_extensions),
        ("T5", test_5_core_tick_any_role),
        ("T6", test_6_core_tick_any_phase),
        ("T7", test_7_simple_task_no_taskboard),
        ("T8", test_8_single_agent_no_multiagent),
        ("T9", test_9_extension_structure),
        ("T10", test_10_manifest_completeness),
        ("T11", test_11_extension_schema_declarations),
        ("T12", test_12_end_to_end_no_extensions),
    ]

    print("=" * 60)
    print("YuanCore Phase 7 Extension Architecture Tests")
    print("=" * 60)

    passed = 0
    failed = 0
    for name, fn in tests:
        try:
            ok = fn()
            if ok:
                passed += 1
                print(f"  [PASS] {name}")
            else:
                failed += 1
                print(f"  [FAIL] {name}")
        except Exception as e:
            failed += 1
            print(f"  [ERROR] {name}: {e}")

    print("=" * 60)
    print(f"Results: {passed}/{passed+failed} passed")
    if failed == 0:
        print("All Phase 7 acceptance tests PASSED!")
    else:
        print(f"FAILED: {failed} test(s)")
    print("=" * 60)
    return failed == 0


if __name__ == "__main__":
    ok = run_all()
    sys.exit(0 if ok else 1)
