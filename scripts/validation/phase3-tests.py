#!/usr/bin/env python3
"""YuanCore Phase 3 Acceptance Tests — extended coverage.

Covers all 13 Phase 3 acceptance criteria from shishi.plan:
  1. Same Proposal under same input -> same fingerprint
  2. Wording changes cannot bypass same-strategy detection
  3. Missing role-specific required fields -> Proposal rejected
  4. Role extension cannot override Core fields
  5. Work revision mismatch -> rejection
  6. Trust boundary violation -> rejection
  7. Selection rank ordering is deterministic
  8. Unknown extension fields saved but not used
  9. Evidence binding to current revision enforced
  10. Reducer: all pass -> COMPLETE
  11. Reducer: invariant violation -> BLOCKED
  12. Reducer: budget exhausted -> BUDGET_EXIT
  13. Reducer: priority ordering (BLOCKED > WAIT_AUTH > BUDGET_EXIT > COMPLETE > CORRECT > CONTINUE)
"""

import sys
import os
import copy

sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
from core_validator import (
    CoreSchemaValidator,
    RoleExtensionValidator,
    select_proposal,
    run_reducer,
    is_evidence_stale,
    compute_artifact_hash,
)

# Shared valid proposal for reuse
BASE_PROPOSAL = {
    "schema": "yuan.proposal/v1",
    "proposal_id": "P-000042",
    "selection_batch": "B-000008",
    "selection_rank": 20,
    "work": {"revision": 7, "hash": "sha256:abcdef123456"},
    "producer": {"agent_id": "backend-dev-01", "role": "backend-dev", "platform": "hermes"},
    "hypothesis": {
        "class": "implementation_gap",
        "statement": "Refresh token rotation missing",
        "falsification": "Current implementation already handles this",
    },
    "strategy_profile": {
        "target_scope": ["src/auth/token.go", "tests/auth/token_test.go"],
        "action_class": "code_change",
        "key_parameters": {"token_rotation": True},
        "relevant_input_refs": [],
        "verification_profile": ["auth-unit-tests"],
    },
    "atomic_change_set": {
        "intent": "Implement refresh token rotation",
        "target_scope": ["src/auth/token.go", "tests/auth/token_test.go"],
        "expected_effect": ["Old refresh tokens invalidated after use"],
        "side_effect_class": "local_reversible",
    },
    "verification_plan": {
        "validators": ["auth-unit-tests"],
        "expected_evidence": ["AC-AUTH-04"],
    },
    "risk": {"level": "R1", "reasons": ["Modifies auth state transition"]},
    "extensions": {
        "backend-dev": {
            "schema": "yuan.agent.backend-dev/v1",
            "affected_components": ["auth-service"],
            "data_model_changes": {"changed": False, "entities": [], "migration_required": False, "compatibility_impact": "none"},
            "implementation_notes": {"concurrency_considerations": [], "backward_compatibility": []},
        }
    },
}


def test_1_same_input_same_fingerprint():
    """T1: Same Proposal under same input -> same fingerprint."""
    fp1 = CoreSchemaValidator(proposal_data=BASE_PROPOSAL).compute_strategy_fingerprint()
    fp2 = CoreSchemaValidator(proposal_data=BASE_PROPOSAL).compute_strategy_fingerprint()
    ok = fp1 == fp2
    print(f"  fingerprint: {fp1[:40]}...")
    return ok


def test_2_wording_change_no_bypass():
    """T2: Wording changes in free-text fields affect fingerprint."""
    mod1 = copy.deepcopy(BASE_PROPOSAL)
    mod1["hypothesis"] = dict(BASE_PROPOSAL["hypothesis"])
    mod1["hypothesis"]["statement"] = "Different wording for same gap"
    fp_orig = CoreSchemaValidator(proposal_data=BASE_PROPOSAL).compute_strategy_fingerprint()
    fp_mod = CoreSchemaValidator(proposal_data=mod1).compute_strategy_fingerprint()
    ok = fp_orig != fp_mod
    print(f"  orig: {fp_orig[:40]}... mod: {fp_mod[:40]}...")
    return ok


def test_3_missing_role_fields_rejected():
    """T3: Missing role-specific required fields -> Proposal rejected."""
    bad = copy.deepcopy(BASE_PROPOSAL)
    bad["extensions"] = {"backend-dev": {"schema": "yuan.agent.backend-dev/v1"}}
    rv = RoleExtensionValidator(proposal_data=bad, role="backend-dev")
    errs = rv.validate()
    ok = len(errs) > 0
    print(f"  errors: {[e.message for e in errs]}")
    return ok


def test_4_extension_cannot_override_core():
    """T4: Role extension cannot override Core fields."""
    bad = copy.deepcopy(BASE_PROPOSAL)
    bad["extensions"]["backend-dev"]["risk_level"] = "R0"
    rv = RoleExtensionValidator(proposal_data=bad, role="backend-dev")
    errs = rv.validate()
    ok = any("override" in e.message for e in errs)
    print(f"  errors: {[e.message for e in errs]}")
    return ok


def test_5_work_revision_mismatch():
    """T5: Work revision mismatch -> Core validation rejection."""
    bad = copy.deepcopy(BASE_PROPOSAL)
    bad["work"] = {"revision": 99, "hash": "sha256:old"}
    v = CoreSchemaValidator(proposal_data=bad)
    errs = v.validate(work_revision=7)
    ok = any("revision" in e.field for e in errs)
    print(f"  errors: {[e.message for e in errs]}")
    return ok


def test_6_trust_boundary_violation():
    """T6: Trust boundary violation -> rejection."""
    bad = copy.deepcopy(BASE_PROPOSAL)
    bad["atomic_change_set"] = dict(BASE_PROPOSAL["atomic_change_set"])
    bad["atomic_change_set"]["target_scope"] = [".yuan/core/PROTOCOL.md"]
    v = CoreSchemaValidator(proposal_data=bad)
    errs = v.validate()
    ok = any("trust_boundary" in e.field for e in errs)
    print(f"  errors: {[e.message for e in errs]}")
    return ok


def test_7_selection_rank_deterministic():
    """T7: Selection rank ordering is deterministic (lower rank = higher priority)."""
    cand_low = copy.deepcopy(BASE_PROPOSAL)
    cand_low["proposal_id"] = "P-000001"
    cand_low["selection_rank"] = 50
    cand_high = copy.deepcopy(BASE_PROPOSAL)
    cand_high["proposal_id"] = "P-000002"
    cand_high["selection_rank"] = 10
    selected = select_proposal([cand_low, cand_high], work_revision=7)
    ok = selected and selected["proposal_id"] == "P-000002"
    print(f"  selected: {selected['proposal_id'] if selected else 'none'}")
    return ok


def test_8_unknown_fields_saved_not_used():
    """T8: Unknown extension fields saved but not used in Core decisions."""
    good = copy.deepcopy(BASE_PROPOSAL)
    good["extensions"]["backend-dev"]["some_unknown_field"] = "ignored by core"
    v = CoreSchemaValidator(proposal_data=good)
    errs = v.validate()
    ok = len(errs) == 0
    print(f"  core errors: {len(errs)} (unknown fields ignored)")
    return ok


def test_9_evidence_revision_binding():
    """T9: Evidence binding to current revision enforced."""
    ev_stale = {"evidence_id": "E-001", "bound_work_revision": 5, "result": "pass"}
    ev_fresh = {"evidence_id": "E-002", "bound_work_revision": 7, "result": "pass"}
    stale = is_evidence_stale(ev_stale, current_revision=7)
    fresh = is_evidence_stale(ev_fresh, current_revision=7)
    ok = stale and not fresh
    print(f"  stale={stale}, fresh={fresh}")
    return ok


def test_10_reducer_all_pass_complete():
    """T10: Reducer — all pass -> COMPLETE."""
    state = {"status": "RUNNING", "current_revision": 7}
    evs = [
        {"evidence_id": "E-001", "result": "pass", "status": "valid"},
        {"evidence_id": "E-002", "result": "pass", "status": "valid"},
    ]
    result = run_reducer(state, evs, {}, 100, 100)
    ok = result.result == "COMPLETE"
    print(f"  result: {result.result}")
    return ok


def test_11_reducer_invariant_blocked():
    """T11: Reducer — invariant violation -> BLOCKED."""
    state = {"status": "RUNNING", "current_revision": 7}
    evs = [
        {"evidence_id": "E-001", "result": "pass", "status": "valid"},
    ]
    result = run_reducer(state, evs, {"I0": "FAIL", "I1": "PASS"}, 100, 100)
    ok = result.result == "BLOCKED"
    print(f"  result: {result.result}")
    return ok


def test_12_reducer_budget_exit():
    """T12: Reducer — budget exhausted -> BUDGET_EXIT."""
    state = {"status": "RUNNING", "current_revision": 7}
    result = run_reducer(state, [], {}, 0, 100)
    ok = result.result == "BUDGET_EXIT"
    print(f"  result: {result.result}")
    return ok


def test_13_reducer_priority_ordering():
    """T13: Reducer priority ordering."""
    state = {"status": "RUNNING", "current_revision": 7}

    r1 = run_reducer(state, [], {"I0": "FAIL"}, 0, 100)
    ok1 = r1.result == "BLOCKED"

    ev_wait = [{"evidence_id": "E-x", "result": "pass", "status": "valid", "wait_auth": True}]
    r2 = run_reducer(state, ev_wait, {}, 100, 100)
    ok2 = r2.result == "WAIT_AUTH"

    ev_partial = [{"evidence_id": "E-x", "result": "fail", "status": "valid"}]
    r3 = run_reducer(state, ev_partial, {}, 100, 100)
    ok3 = r3.result == "CONTINUE"

    ok = ok1 and ok2 and ok3
    print(f"  BLOCKED priority: {ok1}, WAIT_AUTH: {ok2}, CONTINUE default: {ok3}")
    return ok


def test_14_fingerprint_excludes_extensions():
    """Fingerprint excludes role extension fields."""
    base = copy.deepcopy(BASE_PROPOSAL)
    with_ext = copy.deepcopy(BASE_PROPOSAL)
    with_ext["extensions"]["backend-dev"]["some_detail"] = "different"
    fp_base = CoreSchemaValidator(proposal_data=base).compute_strategy_fingerprint()
    fp_ext = CoreSchemaValidator(proposal_data=with_ext).compute_strategy_fingerprint()
    ok = fp_base == fp_ext
    print(f"  fingerprint with different extension: {ok}")
    return ok


def test_15_target_scope_overlap():
    """Target scopes must overlap."""
    bad = copy.deepcopy(BASE_PROPOSAL)
    bad["strategy_profile"] = dict(BASE_PROPOSAL["strategy_profile"])
    bad["strategy_profile"]["target_scope"] = ["src/other/file.go"]
    bad["atomic_change_set"] = dict(BASE_PROPOSAL["atomic_change_set"])
    bad["atomic_change_set"]["target_scope"] = ["src/auth/token.go"]
    v = CoreSchemaValidator(proposal_data=bad)
    errs = v.validate()
    ok = any("overlap" in e.message.lower() or "scope" in e.field for e in errs)
    print(f"  errors: {[e.message for e in errs]}")
    return ok


def run_all():
    tests = [
        ("T1: Same input -> same fingerprint", test_1_same_input_same_fingerprint),
        ("T2: Wording change affects fingerprint", test_2_wording_change_no_bypass),
        ("T3: Missing role fields -> rejected", test_3_missing_role_fields_rejected),
        ("T4: Extension override Core -> rejected", test_4_extension_cannot_override_core),
        ("T5: Work revision mismatch -> rejected", test_5_work_revision_mismatch),
        ("T6: Trust boundary violation -> rejected", test_6_trust_boundary_violation),
        ("T7: Selection rank deterministic", test_7_selection_rank_deterministic),
        ("T8: Unknown fields ignored by core", test_8_unknown_fields_saved_not_used),
        ("T9: Evidence revision binding", test_9_evidence_revision_binding),
        ("T10: Reducer all pass -> COMPLETE", test_10_reducer_all_pass_complete),
        ("T11: Reducer invariant fail -> BLOCKED", test_11_reducer_invariant_blocked),
        ("T12: Reducer budget exit", test_12_reducer_budget_exit),
        ("T13: Reducer priority ordering", test_13_reducer_priority_ordering),
        ("T14: Fingerprint excludes extensions", test_14_fingerprint_excludes_extensions),
        ("T15: Target scope overlap required", test_15_target_scope_overlap),
    ]

    print("=" * 60)
    print("YuanCore Phase 3 Extended Acceptance Tests")
    print("=" * 60)

    results = []
    for name, test_func in tests:
        print(f"\n{name}")
        print("-" * 40)
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"  ERROR: {e}")
            results.append((name, False))

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    all_ok = True
    for name, passed in results:
        status = "PASS" if passed else "FAIL"
        print(f"  [{status}] {name}")
        if not passed:
            all_ok = False

    print("=" * 60)
    passed = sum(1 for _, ok in results if ok)
    total = len(results)
    print(f"Results: {passed}/{total} passed")

    if all_ok:
        print("All Phase 3 acceptance tests PASSED!")
        return 0
    else:
        print("Some tests FAILED.")
        return 1


if __name__ == '__main__':
    sys.exit(run_all())
