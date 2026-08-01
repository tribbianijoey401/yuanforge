---
name: conflict-rules
title: Core-Extension Conflict Rules
description: 'YuanForge Core framework document'
category: invariant
stage: published
created_at: 2026-07-31
last_modified: 2026-08-01
author: framework-team
---

# Core-Extension Conflict Rules

**Version:** yuan.core.extension-conflict/v0.1  
**Last Updated:** 2026-07-31

## Overview

These four rules govern the interaction between Core Envelope fields (understood by the Harness for deterministic selection) and Role Extension fields (professional context from Agent roles). They ensure that the Core remains stable while allowing Agents to add rich professional context without compromising the deterministic guarantee.

---

## Rule One: Core Field Priority

### Statement

角色扩展不得覆盖 Core 字段。

### Prohibited Overwrites

The following Core-envelope fields **must not** be modified or overridden by any Role Extension, regardless of the agent's professional authority:

| Field | Reason |
|-------|--------|
| `work.revision` | Core determines revision sequencing; extensions can only consume current revision |
| `strategy_profile.target_scope` / `atomic_change_set.target_scope` | Extensions may refine but cannot expand beyond declared scope without approval |
| `strategy_profile.action_class` | Action class is chosen by proposal logic; extensions annotate but don't change it |
| `risk.level` | Risk is determined by Core analysis of changes; extensions may recommend but Core finalizes |
| `verification_plan.validators` | Validator list is determined by work requirements; extensions suggest validators but Core binds them |
| `atomic_change_set.side_effect_class` | Side-effect classification affects Reducer decisions; set by proposal, not by extension alone |

### Enforcement

During Core Schema Validation, if any Extension field attempts to modify one of the above Core fields, the Proposal is rejected with `ADMIT_REJECTED` reason: `core_field_overwrite_prohibited`.

---

## Rule Two: Dual Declaration for Core-Impacting Information

### Statement

影响 Core 的信息必须双重声明。

### Principle

If an Extension declares information that affects Core processing, that information MUST appear in BOTH the Extension namespace AND the corresponding Core field. This ensures the Harness sees the fact without needing to parse Extensions.

### Example: Backend Dev Data Model Change

When Backend Dev declares data model migration required:

```yaml
# In extension.backend-dev:
extensions:
  backend-dev:
    data_model_changes:
      changed: true
      migration_required: true

# Also mapped to Core:
strategy_profile:
  key_parameters:
    migration_required: true
```

Failure to dual-declare results in `ADMIT_REJECTED` reason: `core_impact_not_doubly_declared`. The Strategy Fingerprint would miss the migration parameter, causing potential duplicate execution on revision bump.

### Other Examples

| Extension Info | Required Core Mapping |
|----------------|----------------------|
| Security threat category | `hypothesis.class` or custom key_parameter |
| Test coverage gap | `risk.level` elevation recommendation |
| Architectural decision affecting deployment | `strategy_profile.key_parameters` deployment_strategy |

---

## Rule Three: Professional Conclusions Require Evidence

### Statement

专业结论不能替代 Evidence。

### Forbidden Standalone Claims

The following types of assertions **cannot alone satisfy completion requirements**:

```text
Security Auditor: 没有安全问题
Tester: 全部测试通过
Architect: 设计符合规范
Backend Dev: 已完成实现
Frontend Dev: 界面已交付
```

Each such claim MUST reference one or more Evidence IDs that provide mechanical verification.

### Required Pattern

Instead of standalone claims, Extensions must produce this pattern:

```yaml
extensions:
  security-auditor:
    security_checks:
      - check_id: SEC-TOKEN-01
        status: executed
        evidence_ref: E-000038
      - check_id: SEC-AUTHZ-03
        status: not_applicable
        rationale: "本次变更不涉及授权决策"
    
    findings:
      - finding_id: F-0004
        severity: medium
        claim: "刷新令牌缺少轮换"
        evidence_ref: E-000037
```

### Enforcement

During Role Extension Validation, the Harness checks that all validation-critical assertions have corresponding evidence_refs. Missing references result in Advisory Validation warning or Rejection depending on Work Contract severity requirements.

---

## Rule Four: Unknown Extension Fields Excluded from Core Determinism

### Statement

未知扩展字段不参与 Core 判定。

### Principle

Extensions may contain additional fields not defined in their schema. The Core handles them as follows:

| Treatment | Description |
|-----------|-------------|
| **Save** | Field value is preserved in the full Proposal record |
| **Skip Selection** | Not considered during proposal ranking/filtering |
| **Skip Fingerprint** | Not included in strategy fingerprint calculation |
| **Skip Reducer** | Not evaluated by Reducer decision table |
| **Skip AC** | Does not contribute to Any Condition satisfaction |
| **Do Not Override** | Cannot overwrite known Core or Extension fields |

### Default Handling (Core v0.1)

For unknown fields in v0.1:
- Status: `unvalidated` (marked in Proposal metadata)
- Behavior: Saved but not used for any Core determination
- Audit: Logged in Journal entry for future review

### Work Contract Override

The Work Contract may specify stricter handling via policy:

```yaml
extensions:
  policies:
    - reject_unknown_fields  # Reject proposals with unknown fields
    - treat_as_advisory      # Mark as advisory validation
```

Without explicit policy, Core v0.1 uses the conservative "save and ignore" approach.

---

## Conflict Resolution Summary Table

| Issue | Rule Applied | Outcome | Handler |
|-------|--------------|---------|---------|
| Extension modifies Core field | Rule One (Priority) | Reject (`ADMIT_REJECTED`) | Core Schema Validator |
| Core impact not mirrored in Core | Rule Two (Dual Decl.) | Reject (`ADMIT_REJECTED`) | Core Schema Validator |
| Claim without Evidence ref | Rule Three (Evidence Req.) | Advisory warning → Reject per policy | Role Extension Validator |
| Unknown extension field | Rule Four (Unknown Fields) | Save, mark unvalidated, ignore | Preservation layer |

---

## References

- `PROPOSAL.md` — Core Envelope structure and Extension Namespace format
- `INVARIANTS.md` — Invariant I7 (Core Trust Boundary protection) related to Rule One
- `REDUCER.md` — How Extension fields interact with reduction decisions (none, by design)
