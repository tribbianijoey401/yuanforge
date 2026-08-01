---
name: tester
title: Tester
description: 'YuanForge Core framework document'
category: role
stage: published
created_at: 2026-07-31
last_modified: 2026-08-01
author: framework-team
---

# Yuan Agent Contract: Tester

**Extension Namespace:** `tester`  
**Extension Schema Version:** `yuan.agent.tester/v1`  

## Proposal Contract

### Base Schema

This contract extends `.yuan/core/schemas/PROPOSAL.md`. All Core Envelope fields apply.

### Extension Namespace

`tester`

### Extension Schema Version

`yuan.agent.tester/v1`

### Required Professional Fields

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `test_matrix` | object | Test counts by category | `{unit: {planned: 28}, integration: {planned: 8}, e2e: {planned: 3}}` |
| `coverage_scope` | array[string] | Areas covered by testing | `["registration", "login", "refresh-token", "role-authorization"]` |
| `environment_requirements` | object | Test environment prerequisites | `{database: "isolated", external_services: "mocked"}` |
| `known_test_gaps` | array[string] | Identified gaps in coverage | `["跨区域时钟偏差场景未覆盖"]` |
| `evidence_refs` | array[string] | Existing Evidence IDs supporting test validity | `["E-000043", "E-000044"]` |

### Test Matrix Example

```yaml
test_matrix:
  unit:
    planned: 25
    executed: 0
    passed: 0
  integration:
    planned: 6
    executed: 0
    passed: 0
  e2e:
    planned: 2
    executed: 0
    passed: 0
```

### Professional Validation Rules

1. `coverage_scope` MUST include all items in `strategy_profile.target_scope` plus any transitive dependencies
2. If `test_matrix.unit.planned` is less than number of changed functions, risk_level should be elevated at least one tier
3. `environment_requirements.database` must match the database isolation level required by the Work Contract when risk >= R1
4. Every `known_test_gap` must either be justified as acceptable risk OR have a corresponding remediation plan in an alternate proposal

### Evidence Binding Rules

Tester conclusions require concrete Evidence:
- "All tests pass" requires ALL planned tests to have matching Evidence records with result=pass
- "Environment verified" requires Evidence from infrastructure validator showing setup completed successfully
- Known gaps must be documented with corresponding risk acceptance Evidence from Security Auditor or Conductor

Pure assertions like "I ran the tests" without Evidence attachment are rejected during Role Extension Validation.

---

## Excluded Fields (Core Only)

Tester extensions CANNOT modify:
- `hypothesis` fields (Tester validates hypotheses, doesn't define them)
- `strategy_profile.action_class`
- `atomic_change_set.target_scope` (Tester observes, doesn't modify production code)
- `risk.level` (may recommend elevation based on test coverage, but Core makes final determination)
- `verification_plan.validators` (Tester proposes validators, but they must be approved by Core and validated by Extension)