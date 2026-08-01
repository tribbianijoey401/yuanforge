---
name: backend-dev
title: Backend Developer
description: 'YuanForge Core framework document'
category: role
stage: published
created_at: 2026-07-31
last_modified: 2026-08-01
author: framework-team
---

# Yuan Agent Contract: Backend Developer

**Extension Namespace:** `backend-dev`  
**Extension Schema Version:** `yuan.agent.backend-dev/v1`  

## Proposal Contract

### Base Schema

This contract extends `.yuan/core/schemas/PROPOSAL.md`. All Core Envelope fields apply.

### Extension Namespace

`backend-dev`

### Extension Schema Version

`yuan.agent.backend-dev/v1`

### Required Professional Fields

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `affected_components` | array[string] | Service components impacted by the change | `["auth-service"]` |
| `api_contract_changes` | object | Whether API surface changed and references | `{changed: false, refs: []}` |
| `data_model_changes` | object | Data model modification details | See example below |
| `dependency_changes` | object | Added/removed dependencies | `{added: [], removed: []}` |
| `implementation_notes` | object | Technical considerations for implementers | See example below |

### Data Model Changes Example

```yaml
data_model_changes:
  changed: true
  entities:
    - refresh_tokens
  migration_required: false
  compatibility_impact: none
```

### Implementation Notes Example

```yaml
implementation_notes:
  concurrency_considerations:
    - "同一刷新令牌只能成功兑换一次"
  backward_compatibility:
    - "已签发访问令牌不受影响"
```

### Professional Validation Rules

1. When `data_model_changes.changed == true`, `atomic_change_set.target_scope` MUST cover all relevant data model files
2. When `migration_required == true`, Core `risk.level` MUST NOT be lower than Work-defined migration risk level
3. API changes (`api_contract_changes.changed == true`) must be reflected either in Work Contract OR a separate approved Change Proposal
4. Professional fields MUST NOT hide or reduce the declared Core target scope

### Evidence Binding Rules

Backend Dev implementation claims must reference specific test Evidence:
- Unit tests covering the modified functionality (evidence ref: AC-* identifiers)
- Integration tests verifying component interactions (evidence ref: AC-* identifiers)
- Performance benchmarks if impact noted in `implementation_notes` (evidence ref: PERF-*)

Self-declarations like "implementation complete" alone are not sufficient evidence.

---

## Excluded Fields (Core Only)

Backend Dev extensions CANNOT modify:
- `hypothesis` fields
- `strategy_profile.action_class`
- `atomic_change_set.target_scope` (can refine within declared bounds but not expand without approval)
- `risk.level` (must reflect actual risk, never downgrade)
- `verification_profile.validators` (must include appropriate validators for the changed components)