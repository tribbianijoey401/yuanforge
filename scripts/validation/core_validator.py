#!/usr/bin/env python3
"""YuanCore v0.1 Validator — complete implementation.

Two-stage validation:
  Stage 1: Core Schema Validation (mandatory for all proposals)
  Stage 2: Role Extension Validation (per registered role contract)

Plus deterministic selection, strategy fingerprint, and reducer logic.
"""

import yaml
import hashlib
import os
import re
import json
from typing import Dict, List, Optional, Tuple, Any

CORE_SCHEMA_VERSION = "yuan.proposal/v1"
BASE_DIR = os.environ.get("YUANFORGE_BASE_DIR", "/home/admin/yuanforge")
CORE_DIR = os.path.join(BASE_DIR, ".yuan", "core")
EXTENSIONS_DIR = os.path.join(BASE_DIR, ".yuan", "extensions")
WORK_DIR = os.path.join(BASE_DIR, "work")


class ValidationError(Exception):
    def __init__(self, message, field=None):
        self.message = message
        self.field = field
        super().__init__(message)


class ReducerResult:
    """Represents the deterministic reducer output."""
    def __init__(self, result: str, details: dict = None):
        self.result = result  # WAIT_AUTH, BLOCKED, BUDGET_EXIT, COMPLETE, CORRECT, CONTINUE
        self.details = details or {}

    def __repr__(self):
        return f"ReducerResult({self.result}, {self.details})"


def parse_yaml(text: str) -> dict:
    return yaml.safe_load(text) or {}


def get_nested(obj: dict, keys: str):
    for key in keys.split("."):
        if isinstance(obj, dict) and key in obj:
            obj = obj[key]
        else:
            return None
    return obj


def sha256_str(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


# ---------------------------------------------------------------------------
# Stage 1: Core Schema Validation
# ---------------------------------------------------------------------------

class CoreSchemaValidator:
    """Validates the Core Envelope of a Proposal."""

    VALID_ACTION_CLASSES = {
        "code_change", "config_update", "test_addition",
        "document_update", "workflow_update"
    }
    VALID_SIDE_EFFECT_CLASSES = {
        "local_reversible", "database_migration", "external_api_call"
    }
    VALID_RISK_LEVELS = {"R0", "R1", "R2"}
    VALID_PLATFORMS = {"codex", "claude", "hermes", "manual"}

    # Paths protected by Core Trust Boundary (I7)
    TRUST_BOUNDARY_PREFIXES = [
        ".yuan/core/",
        ".yuan/VERSION",
        "work/STATE.md",
        "work/journal/",
        "migration/BASELINE.md",
    ]

    def __init__(self, proposal_path: str = None, proposal_data: dict = None):
        if proposal_data:
            self.proposal = proposal_data
        elif proposal_path:
            with open(proposal_path, "r", encoding="utf-8") as f:
                self.proposal = parse_yaml(f.read())
        else:
            self.proposal = {}

    def validate(self, work_revision: Optional[int] = None) -> List[ValidationError]:
        errors = []

        # --- Schema version ---
        schema_val = self.proposal.get("schema")
        if schema_val != CORE_SCHEMA_VERSION:
            errors.append(ValidationError(
                f"Invalid schema: {schema_val} (expected {CORE_SCHEMA_VERSION})", "schema"
            ))

        # --- Required Core fields ---
        required_fields = [
            ("proposal_id", lambda v: isinstance(v, str) and bool(re.match(r'^P-\d{6,8}$', v))),
            ("selection_batch", lambda v: isinstance(v, str) and bool(re.match(r'^B-\d{6}$', v))),
            ("selection_rank", lambda v: isinstance(v, int) and v > 0),
            ("work.revision", lambda v: isinstance(v, int)),
            ("work.hash", lambda v: isinstance(v, str) and v.startswith("sha256:")),
            ("producer.agent_id", lambda v: isinstance(v, str) and len(v) > 0),
            ("producer.role", lambda v: isinstance(v, str) and len(v) > 0),
            ("producer.platform", lambda v: isinstance(v, str) and v in self.VALID_PLATFORMS),
            ("hypothesis.class", lambda v: isinstance(v, str) and len(v) > 0),
            ("hypothesis.statement", lambda v: isinstance(v, str) and len(v) > 0),
            ("hypothesis.falsification", lambda v: isinstance(v, str) and len(v) > 0),
            ("strategy_profile.target_scope", lambda v: isinstance(v, list) and len(v) > 0),
            ("strategy_profile.action_class", lambda v: v in self.VALID_ACTION_CLASSES),
            ("strategy_profile.key_parameters", lambda v: isinstance(v, dict)),
            ("strategy_profile.relevant_input_refs", lambda v: isinstance(v, list)),
            ("strategy_profile.verification_profile", lambda v: isinstance(v, list) and len(v) > 0),
            ("atomic_change_set.intent", lambda v: isinstance(v, str) and len(v) > 0),
            ("atomic_change_set.target_scope", lambda v: isinstance(v, list)),
            ("atomic_change_set.expected_effect", lambda v: isinstance(v, list)),
            ("atomic_change_set.side_effect_class", lambda v: v in self.VALID_SIDE_EFFECT_CLASSES),
            ("verification_plan.validators", lambda v: isinstance(v, list) and len(v) > 0),
            ("verification_plan.expected_evidence", lambda v: isinstance(v, list)),
            ("risk.level", lambda v: v in self.VALID_RISK_LEVELS),
            ("risk.reasons", lambda v: isinstance(v, list)),
            ("extensions", lambda v: isinstance(v, dict)),
        ]

        for field, validator in required_fields:
            value = get_nested(self.proposal, field)
            if value is None:
                errors.append(ValidationError(f"Missing required field: {field}", field))
            elif not validator(value):
                errors.append(ValidationError(f"Invalid value for {field}", field))

        # --- Overlap check: strategy_profile ↔ atomic_change_set target_scope ---
        strat_scope = set(get_nested(self.proposal, "strategy_profile.target_scope") or [])
        atomic_scope = set(get_nested(self.proposal, "atomic_change_set.target_scope") or [])
        if strat_scope and atomic_scope and not (strat_scope & atomic_scope):
            errors.append(ValidationError(
                "strategy_profile.target_scope and atomic_change_set.target_scope must overlap",
                "target_scope_overlap"
            ))

        # --- Work Revision match (if work_revision provided) ---
        if work_revision is not None:
            actual_revision = get_nested(self.proposal, "work.revision")
            if actual_revision is not None and actual_revision != work_revision:
                errors.append(ValidationError(
                    f"Work revision mismatch: proposal has revision {actual_revision}, "
                    f"expected {work_revision}",
                    "work.revision"
                ))

        # --- Trust boundary check (I7) ---
        producer_role = get_nested(self.proposal, "producer.role") or ""
        if producer_role not in ("conductor", "admin"):
            for path_item in atomic_scope:
                if self._is_trust_boundary_path(path_item):
                    errors.append(ValidationError(
                        f"Attempt targets Core Trust Boundary path: {path_item} "
                        f"(role: {producer_role} not authorized)",
                        "trust_boundary"
                    ))

        # --- Risk level sanity ---
        risk_level = get_nested(self.proposal, "risk.level")
        if risk_level:
            # R0 work cannot have R1/R2 proposals; R1 work cannot have R2 proposals
            # This is a cross-check: risk.level should reflect actual risk, not be downgraded
            if risk_level == "R0" and atomic_scope:
                # R0 should typically have minimal scope
                pass  # advisory only

        return errors

    def _is_trust_boundary_path(self, path: str) -> bool:
        """Check if a path is protected by Core Trust Boundary."""
        for prefix in self.TRUST_BOUNDARY_PREFIXES:
            if path == prefix.rstrip("/") or path.startswith(prefix.rstrip("/") + "/"):
                return True
            if path.startswith(".yuan/") and not path.startswith(".yuan/core/") and \
               not path.startswith(".yuan/extensions/") and \
               not path.startswith(".yuan/skills/") and \
               not path.startswith(".yuan/specs/") and \
               not path.startswith(".yuan/rules/") and \
               not path.startswith(".yuan/docs/") and \
               not path.startswith(".yuan/platforms/") and \
               not path.startswith(".yuan/runtime/"):
                # Other .yuan/ subdirs may also be protected depending on Work Contract
                pass
        return False

    def compute_strategy_fingerprint(self) -> str:
        """Compute deterministic strategy fingerprint from normalized Core fields."""
        h = self.proposal.get("hypothesis", {})
        sp = self.proposal.get("strategy_profile", {})
        acs = self.proposal.get("atomic_change_set", {})

        parts = []
        parts.append(f"{h.get('class', '')}:{h.get('statement', '')}")
        parts.append("scope:" + "|".join(sorted(str(s) for s in acs.get("target_scope", []))))
        parts.append("action:" + sp.get("action_class", ""))

        params = sp.get("key_parameters", {})
        parts.append("params:" + json.dumps(params, sort_keys=True, default=str))

        inputs = [str(r) for r in sp.get("relevant_input_refs", [])]
        parts.append("inputs:" + "|".join(sorted(inputs)))

        validators = [str(v) for v in sp.get("verification_profile", [])]
        parts.append("validators:" + "|".join(sorted(validators)))

        fp_input = "\x00".join(parts)
        return "sha256:" + sha256_str(fp_input)


# ---------------------------------------------------------------------------
# Stage 2: Role Extension Validation
# ---------------------------------------------------------------------------

class RoleExtensionValidator:
    """Validates the Role Extension namespace of a Proposal."""

    # Role-specific required fields
    REQUIRED_FIELDS = {
        "conductor": ["intent_summary", "agent_selection"],
        "architect": ["architecture_decisions", "affected_seams"],
        "backend-dev": ["affected_components", "data_model_changes", "implementation_notes"],
        "frontend-dev": ["ui_components", "accessibility_compliance"],
        "tester": ["test_matrix", "coverage_scope", "environment_requirements"],
        "product-analyst": ["user_stories", "acceptance_criteria", "risk_label"],
        "spec-reviewer": ["reviewed_ac", "reviewed_api_contract", "boundary_questions"],
        "security-auditor": ["threat_categories", "security_checks", "findings"],
        "quality-auditor": ["performance_checks", "db_checks", "findings"],
        "ux-reviewer": ["wcag_level", "interaction_checks", "findings"],
        "doc-engineer": ["docs_updated", "knowledge_distilled"],
        "ui-designer": ["design_system", "component_specs", "prototype_path"],
        "design-reviewer": ["api_contract_review", "data_model_review", "confrontation_attempts"],
    }

    # Fields that extensions MUST NOT override (Rule One)
    PROHIBITED_OVERRIDES = [
        "work_revision", "target_scope", "action_class",
        "risk_level", "verification_plan", "side_effect_class"
    ]

    def __init__(self, proposal_path: str = None, proposal_data: dict = None, role: str = None):
        if proposal_data:
            self.proposal = proposal_data
        elif proposal_path:
            with open(proposal_path, "r", encoding="utf-8") as f:
                self.proposal = parse_yaml(f.read())
        else:
            self.proposal = {}
        self.role = role or (
            get_nested(self.proposal, "producer.role") or "unknown"
        )

    def validate(self) -> List[ValidationError]:
        errors = []

        exts = self.proposal.get("extensions", {})
        if self.role not in exts:
            errors.append(ValidationError(
                f"Missing extension namespace for role: {self.role}",
                f"extensions.{self.role}"
            ))
            return errors

        ext_data = exts[self.role]

        # Schema version check
        expected_schema = f"yuan.agent.{self.role}/v1"
        actual_schema = ext_data.get("schema", "")
        if actual_schema != expected_schema:
            errors.append(ValidationError(
                f"Schema mismatch: expected {expected_schema}, got {actual_schema}",
                f"extensions.{self.role}.schema"
            ))

        # Required professional fields
        required = self.REQUIRED_FIELDS.get(self.role, [])
        for field in required:
            if field not in ext_data:
                errors.append(ValidationError(
                    f"Required professional field missing: {field}",
                    f"extensions.{self.role}.{field}"
                ))

        # Prohibited overrides (Rule One)
        for p in self.PROHIBITED_OVERRIDES:
            if p in ext_data:
                errors.append(ValidationError(
                    f"Extension attempts to override Core field: {p}",
                    f"extensions.{self.role}.{p}"
                ))

        # Rule Three: professional conclusions must reference Evidence
        self._check_evidence_binding(ext_data, errors)

        return errors

    def _check_evidence_binding(self, ext_data: dict, errors: List[ValidationError]):
        """Rule Three: check that validation-critical assertions have evidence refs."""
        role = self.role

        # Security Auditor: security_checks must have evidence_ref
        if role == "security-auditor":
            checks = ext_data.get("security_checks", [])
            for check in checks:
                if check.get("status") == "executed" and "evidence_ref" not in check:
                    errors.append(ValidationError(
                        f"Security check {check.get('check_id', '?')} executed without evidence_ref",
                        f"extensions.security-auditor.security_checks"
                    ))

        # Tester: test_matrix must have executed counts
        if role == "tester":
            tm = ext_data.get("test_matrix", {})
            for category in ["unit", "integration", "e2e"]:
                cat_data = tm.get(category, {})
                planned = cat_data.get("planned", 0)
                executed = cat_data.get("executed", 0)
                if planned > 0 and executed == 0:
                    errors.append(ValidationError(
                        f"Test category '{category}': {planned} planned, 0 executed",
                        f"extensions.tester.test_matrix.{category}"
                    ))

        # Backend Dev: data_model_changes.changed=true must map to Core key_parameters
        if role == "backend-dev":
            dmc = ext_data.get("data_model_changes", {})
            if dmc.get("changed") is True:
                key_params = get_nested(self.proposal, "strategy_profile.key_parameters") or {}
                if not any(k in key_params for k in ["migration_required", "data_model_changed"]):
                    errors.append(ValidationError(
                        "data_model_changes.changed=true but not mapped to strategy_profile.key_parameters "
                        "(Rule Two: dual declaration required)",
                        "extensions.backend-dev.data_model_changes"
                    ))


# ---------------------------------------------------------------------------
# Selection & Reducer
# ---------------------------------------------------------------------------

def select_proposal(candidates: List[dict], work_revision: int) -> Optional[dict]:
    """
    Deterministic selection:
    1. Filter: work revision must match
    2. Filter: Core Schema must pass
    3. Filter: Role Extension must pass
    4. Sort by selection_rank ascending
    5. Return first valid candidate
    """
    valid = []
    for c in candidates:
        # Work revision match
        rev = get_nested(c, "work.revision")
        if rev is None or rev != work_revision:
            continue

        # Filter: Core Schema must pass
        core_v = CoreSchemaValidator(proposal_data=c)
        if core_v.validate(work_revision=work_revision):
            continue

        # Filter: Role Extension must pass
        role = get_nested(c, "producer.role") or "unknown"
        role_v = RoleExtensionValidator(proposal_data=c, role=role)
        role_errors = role_v.validate()
        if role_errors:
            continue

        valid.append(c)

    if not valid:
        return None

    # Sort by selection_rank (lower = higher priority)
    valid.sort(key=lambda x: get_nested(x, "selection_rank") or 999999)
    return valid[0]


def run_reducer(
    state: dict,
    evidence_list: List[dict],
    invariants: dict,
    budget_remaining: int,
    budget_max: int,
) -> ReducerResult:
    """
    Deterministic reducer — evaluates six result types in priority order.
    Must be a pure function: same inputs → same output.
    """
    # Priority 1: BLOCKED (invariant violation)
    for inv_id, result in invariants.items():
        if result == "FAIL":
            return ReducerResult("BLOCKED", {
                "reason": f"Invariant {inv_id} violated",
                "invariant": inv_id,
            })

    # Priority 2: BLOCKED (unknown validation result)
    for ev in evidence_list:
        if ev.get("result") in ("unknown", "timeout", "error"):
            return ReducerResult("BLOCKED", {
                "reason": f"Unknown validation result for evidence {ev.get('evidence_id')}",
                "evidence_id": ev.get("evidence_id"),
            })

    # Priority 3: BUDGET_EXIT
    if budget_remaining <= 0 and state.get("status") not in ("COMPLETE", "FAILED"):
        return ReducerResult("BUDGET_EXIT", {
            "reason": "Resource budget exhausted",
            "budget_remaining": budget_remaining,
        })

    # Priority 4: WAIT_AUTH (from role extension)
    for ev in evidence_list:
        if ev.get("wait_auth") is True:
            return ReducerResult("WAIT_AUTH", {
                "reason": "Human authorization required",
                "evidence_id": ev.get("evidence_id"),
            })

    # Priority 5: COMPLETE
    all_pass = all(
        ev.get("result") == "pass"
        for ev in evidence_list
        if ev.get("status") == "valid"
    )
    no_pending_side_effects = not any(
        get_nested(ev, "pending_side_effects")
        for ev in evidence_list
    )
    if all_pass and no_pending_side_effects:
        return ReducerResult("COMPLETE", {
            "evidence_count": len(evidence_list),
        })

    # Priority 6: CORRECT (hypothesis falsified, alternate strategy found)
    # Check if any evidence contradicts the current hypothesis
    for ev in evidence_list:
        if ev.get("contradicts_hypothesis") is True:
            return ReducerResult("CORRECT", {
                "reason": "Original hypothesis falsified by new evidence",
                "evidence_id": ev.get("evidence_id"),
            })

    # Default: CONTINUE (need more evidence or refinement)
    return ReducerResult("CONTINUE", {
        "pending_evidence": [
            ev.get("validator_id") for ev in evidence_list
            if ev.get("result") == "fail"
        ],
    })


# ---------------------------------------------------------------------------
# STATE CAS Operations
# ---------------------------------------------------------------------------

def read_state(state_path: str = None) -> dict:
    """Read current STATE.md — extracts YAML from markdown code fences."""
    path = state_path or os.path.join(WORK_DIR, "STATE.md")
    if not os.path.exists(path):
        return _default_state()
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    # Try to extract YAML from code fence first
    yaml_text = _extract_yaml_block(content)
    if yaml_text:
        try:
            result = parse_yaml(yaml_text)
            if result:
                return result
        except Exception:
            pass
    # Fallback: parse full content (may work for pure YAML state files)
    try:
        result = parse_yaml(content)
        if result:
            return result
    except Exception:
        pass
    return _default_state()


def _extract_yaml_block(text: str) -> str:
    """Extract YAML from markdown ```yaml ... ``` fences, stripping comments."""
    import re
    # Match ```yaml ... ``` blocks
    match = re.search(r'```yaml\s*\n(.*?)\n\s*```', text, re.DOTALL)
    if match:
        block = match.group(1)
        # Strip inline comments (lines starting with # after content)
        lines = []
        for line in block.split('\n'):
            stripped = line.strip()
            if stripped.startswith('#'):
                continue
            # Remove trailing comments: "value  # comment"
            if '#' in line:
                idx = line.index('#')
                prefix = line[:idx].rstrip()
                if prefix and not prefix.endswith(':'):
                    line = prefix
            lines.append(line)
        return '\n'.join(lines)
    return ''


def _default_state() -> dict:
    return {
        "schema": "yuan.state/v1",
        "current_revision": 1,
        "current_artifact_hash": "",
        "status": "IDLE",
        "attempt_id": None,
        "pending_changes": [],
        "side_effect_trackers": [],
        "journals_start": "",
        "journals_end": "",
    }


def write_state(new_state: dict, state_path: str = None) -> bool:
    """
    CAS write: verify revision hasn't changed before writing.
    Returns True on success, False on conflict.
    """
    path = state_path or os.path.join(WORK_DIR, "STATE.md")
    current = read_state(path)

    # CAS check
    expected_rev = new_state.get("expected_revision")
    if expected_rev is not None and current.get("current_revision") != expected_rev:
        return False  # Concurrent modification detected

    # Write
    with open(path, "w", encoding="utf-8") as f:
        # Remove expected_revision (internal, not part of output)
        output = {k: v for k, v in new_state.items() if k != "expected_revision"}
        f.write(yaml.dump(output, default_flow_style=False, allow_unicode=True))

    return True


# ---------------------------------------------------------------------------
# Evidence freshness / stale detection
# ---------------------------------------------------------------------------

def is_evidence_stale(evidence: dict, current_revision: int) -> bool:
    """Check if evidence is stale (bound to an old work revision)."""
    bound_rev = evidence.get("bound_work_revision")
    if bound_rev is None:
        return True
    return bound_rev != current_revision


def compute_artifact_hash(file_paths: List[str], base_dir: str = None) -> str:
    """Compute artifact hash from a list of file paths."""
    import hashlib
    h = hashlib.sha256()
    for fp in sorted(file_paths):
        full = os.path.join(base_dir or BASE_DIR, fp)
        if os.path.exists(full):
            with open(full, "rb") as f:
                h.update(f.read())
        h.update(fp.encode("utf-8"))
    return "sha256:" + h.hexdigest()


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: core_validator.py <command> [args...]")
        print("Commands:")
        print("  validate <proposal_path>              Core Schema validation")
        print("  validate-role <proposal_path> <role>  Role Extension validation")
        print("  fingerprint <proposal_path>           Compute strategy fingerprint")
        print("  select <json_file> <work_revision>    Deterministic selection")
        print("  reducer <state_json> <evidence_json>  Run reducer")
        print("  tests                                 Run acceptance tests")
        print("  status                                Show validator status")
        sys.exit(1)

    cmd = sys.argv[1]

    if cmd == "validate" and len(sys.argv) >= 3:
        v = CoreSchemaValidator(proposal_path=sys.argv[2])
        errors = v.validate()
        if errors:
            print("REJECTED")
            for e in errors:
                print(f"  ERROR [{e.field}]: {e.message}")
            sys.exit(1)
        else:
            print("ADMITTED")
            print(f"  Fingerprint: {v.compute_strategy_fingerprint()}")
            sys.exit(0)

    elif cmd == "validate-role" and len(sys.argv) >= 4:
        role = sys.argv[3]
        v = RoleExtensionValidator(proposal_path=sys.argv[2], role=role)
        errors = v.validate()
        if errors:
            print("REJECTED")
            for e in errors:
                print(f"  ERROR [{e.field}]: {e.message}")
            sys.exit(1)
        else:
            print("ADMITTED")
            sys.exit(0)

    elif cmd == "fingerprint" and len(sys.argv) >= 3:
        v = CoreSchemaValidator(proposal_path=sys.argv[2])
        print(v.compute_strategy_fingerprint())

    elif cmd == "select" and len(sys.argv) >= 3:
        with open(sys.argv[2], "r") as f:
            candidates = json.load(f)
        work_rev = int(sys.argv[3]) if len(sys.argv) > 3 else 1
        selected = select_proposal(candidates, work_rev)
        if selected:
            print(json.dumps({
                "selected": selected.get("proposal_id"),
                "rank": selected.get("selection_rank"),
                "role": get_nested(selected, "producer.role"),
            }, indent=2))
        else:
            print("NO_VALID_CANDIDATE")
            sys.exit(1)

    elif cmd == "tests":
        sys.exit(run_tests())

    elif cmd == "status":
        print("YuanCore Validator v0.1")
        print(f"  Base: {BASE_DIR}")
        print(f"  Core dir: {CORE_DIR}")
        print(f"  Python: {sys.version.split()[0]}")

    else:
        print(f"Unknown command: {cmd}")
        sys.exit(1)


def run_tests() -> int:
    """Run all Phase 3 acceptance tests."""
    import tempfile
    import io

    print("=" * 60)
    print("YuanCore Phase 3 Acceptance Tests")
    print("=" * 60)

    base_proposal = {
        "schema": CORE_SCHEMA_VERSION,
        "proposal_id": "P-000042",
        "selection_batch": "B-000008",
        "selection_rank": 20,
        "work": {"revision": 7, "hash": "sha256:abcdef123456"},
        "producer": {
            "agent_id": "backend-dev-01",
            "role": "backend-dev",
            "platform": "hermes",
        },
        "hypothesis": {
            "class": "implementation_gap",
            "statement": "Refresh token rotation missing",
            "falsification": "Current implementation already handles this",
        },
        "strategy_profile": {
            "target_scope": ["src/auth/token.go", "tests/auth/token_test.go"],
            "action_class": "code_change",
            "key_parameters": {"token_rotation": True, "migration_required": False},
            "relevant_input_refs": ["artifact:sha256:abc"],
            "verification_profile": ["auth-unit-tests", "refresh-token-reuse-test"],
        },
        "atomic_change_set": {
            "intent": "Implement refresh token rotation",
            "target_scope": ["src/auth/token.go", "tests/auth/token_test.go"],
            "expected_effect": ["Old refresh tokens invalidated after use"],
            "side_effect_class": "local_reversible",
        },
        "verification_plan": {
            "validators": ["auth-unit-tests", "refresh-token-reuse-test"],
            "expected_evidence": ["AC-AUTH-04", "INV-SEC-03"],
        },
        "risk": {
            "level": "R1",
            "reasons": ["Modifies auth state transition"],
        },
        "extensions": {
            "backend-dev": {
                "schema": "yuan.agent.backend-dev/v1",
                "affected_components": ["auth-service"],
                "data_model_changes": {
                    "changed": False,
                    "entities": [],
                    "migration_required": False,
                    "compatibility_impact": "none",
                },
                "implementation_notes": {
                    "concurrency_considerations": ["Token must be single-use"],
                    "backward_compatibility": ["Existing access tokens unaffected"],
                },
            }
        },
    }

    results = []

    # T1: Same input -> same fingerprint
    print("\n[T1] Deterministic fingerprint")
    fp1 = CoreSchemaValidator(proposal_data=base_proposal).compute_strategy_fingerprint()
    fp2 = CoreSchemaValidator(proposal_data=base_proposal).compute_strategy_fingerprint()
    ok = fp1 == fp2
    results.append(("Same input -> same fingerprint", ok))
    print(f"  {'PASS' if ok else 'FAIL'}: {fp1[:40]}...")

    # T2: Different statement -> different fingerprint
    print("\n[T2] Different content -> different fingerprint")
    modified = dict(base_proposal)
    modified["hypothesis"] = dict(base_proposal["hypothesis"])
    modified["hypothesis"]["statement"] = "completely different hypothesis"
    fp3 = CoreSchemaValidator(proposal_data=modified).compute_strategy_fingerprint()
    ok = fp1 != fp3
    results.append(("Different content -> different fingerprint", ok))
    print(f"  {'PASS' if ok else 'FAIL'}")

    # T3: Missing required fields -> rejection
    print("\n[T3] Missing required fields -> rejection")
    incomplete = dict(base_proposal)
    incomplete["risk"] = {}  # Remove required level and reasons
    v = CoreSchemaValidator(proposal_data=incomplete)
    errs = v.validate()
    ok = len(errs) > 0
    results.append(("Missing fields -> rejection", ok))
    print(f"  {'PASS' if ok else 'FAIL'}: {len(errs)} errors")

    # T4: Invalid work revision -> rejection
    print("\n[T4] Work revision mismatch -> rejection")
    v = CoreSchemaValidator(proposal_data=base_proposal)
    errs = v.validate(work_revision=99)  # Expect 7, not 99
    ok = any("revision" in e.field for e in errs)
    results.append(("Work revision mismatch -> rejection", ok))
    print(f"  {'PASS' if ok else 'FAIL'}")

    # T5: Trust boundary violation -> rejection
    print("\n[T5] Trust boundary violation -> rejection")
    boundary_proposal = dict(base_proposal)
    boundary_proposal["producer"] = {"agent_id": "x", "role": "backend-dev", "platform": "hermes"}
    boundary_proposal["atomic_change_set"] = dict(base_proposal["atomic_change_set"])
    boundary_proposal["atomic_change_set"]["target_scope"] = [".yuan/core/PROTOCOL.md"]
    v = CoreSchemaValidator(proposal_data=boundary_proposal)
    errs = v.validate()
    ok = any("trust_boundary" in e.field for e in errs)
    results.append(("Trust boundary violation -> rejection", ok))
    print(f"  {'PASS' if ok else 'FAIL'}")

    # T6: Role extension validation - missing required fields
    print("\n[T6] Missing role extension fields -> rejection")
    bad_ext = dict(base_proposal)
    bad_ext["extensions"] = {"backend-dev": {"schema": "yuan.agent.backend-dev/v1"}}
    rv = RoleExtensionValidator(proposal_data=bad_ext, role="backend-dev")
    errs = rv.validate()
    ok = len(errs) > 0
    results.append(("Missing role extension fields -> rejection", ok))
    print(f"  {'PASS' if ok else 'FAIL'}: {len(errs)} errors")

    # T7: Role extension schema mismatch -> rejection
    print("\n[T7] Schema mismatch in extension -> rejection")
    bad_schema = dict(base_proposal)
    bad_schema["extensions"]["backend-dev"]["schema"] = "yuan.agent.backend-dev/v2"
    rv = RoleExtensionValidator(proposal_data=bad_schema, role="backend-dev")
    errs = rv.validate()
    ok = any("schema" in e.field for e in errs)
    results.append(("Schema mismatch -> rejection", ok))
    print(f"  {'PASS' if ok else 'FAIL'}")

    # T8: Extension overriding Core field -> rejection
    print("\n[T8] Extension overriding Core field -> rejection")
    override_ext = dict(base_proposal)
    override_ext["extensions"]["backend-dev"]["risk_level"] = "R0"
    rv = RoleExtensionValidator(proposal_data=override_ext, role="backend-dev")
    errs = rv.validate()
    ok = any("override" in e.message for e in errs)
    results.append(("Extension override Core -> rejection", ok))
    print(f"  {'PASS' if ok else 'FAIL'}")

    # T9: Selection - lower rank wins
    print("\n[T9] Selection by rank (lower = higher priority)")
    cand_a = dict(base_proposal)
    cand_a["proposal_id"] = "P-000001"
    cand_a["selection_rank"] = 50
    cand_b = dict(base_proposal)
    cand_b["proposal_id"] = "P-000002"
    cand_b["selection_rank"] = 10
    selected = select_proposal([cand_a, cand_b], work_revision=7)
    ok = selected and selected["proposal_id"] == "P-000002"
    results.append(("Selection rank ordering", ok))
    print(f"  {'PASS' if ok else 'FAIL'}: selected {selected['proposal_id'] if selected else 'none'}")

    # T10: Selection - work revision mismatch filtered out
    print("\n[T10] Selection filters wrong revision")
    cand_old = dict(base_proposal)
    cand_old["proposal_id"] = "P-000003"
    cand_old["work"] = {"revision": 99, "hash": "sha256:old"}
    cand_old["selection_rank"] = 5
    selected = select_proposal([cand_old], work_revision=7)
    ok = selected is None
    results.append(("Wrong revision filtered", ok))
    print(f"  {'PASS' if ok else 'FAIL'}")

    # T11: Reducer - all pass -> COMPLETE
    print("\n[T11] Reducer: all pass -> COMPLETE")
    state = {"status": "RUNNING", "current_revision": 7}
    evs = [
        {"evidence_id": "E-001", "result": "pass", "status": "valid"},
        {"evidence_id": "E-002", "result": "pass", "status": "valid"},
    ]
    result = run_reducer(state, evs, {}, 100, 100)
    ok = result.result == "COMPLETE"
    results.append(("Reducer all pass -> COMPLETE", ok))
    print(f"  {'PASS' if ok else 'FAIL'}: {result.result}")

    # T12: Reducer - invariant fail -> BLOCKED
    print("\n[T12] Reducer: invariant fail -> BLOCKED")
    result = run_reducer(state, evs, {"I0": "FAIL"}, 100, 100)
    ok = result.result == "BLOCKED"
    results.append(("Reducer invariant fail -> BLOCKED", ok))
    print(f"  {'PASS' if ok else 'FAIL'}: {result.result}")

    # T13: Reducer - budget exhausted -> BUDGET_EXIT
    print("\n[T13] Reducer: budget exhausted -> BUDGET_EXIT")
    result = run_reducer(state, [], {}, 0, 100)
    ok = result.result == "BUDGET_EXIT"
    results.append(("Reducer budget exit", ok))
    print(f"  {'PASS' if ok else 'FAIL'}: {result.result}")

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    all_ok = True
    for name, ok in results:
        status = "PASS" if ok else "FAIL"
        print(f"  [{status}] {name}")
        if not ok:
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
