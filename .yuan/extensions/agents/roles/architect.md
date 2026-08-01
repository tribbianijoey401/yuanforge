---
name: architect
title: Architect Agent
description: 'YuanForge Core framework document'
category: role
stage: published
created_at: 2026-07-31
last_modified: 2026-08-01
author: framework-team
---

# Yuan Agent Contract: Architect

**Extension Namespace:** `architect`  
**Extension Schema Version:** `yuan.agent.architect/v1`  

## Proposal Contract

### Base Schema

This contract extends `.yuan/core/schemas/PROPOSAL.md`. All Core Envelope fields apply.

### Extension Namespace

`architect`

### Extension Schema Version

`yuan.agent.architect/v1`

### Required Professional Fields

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `architecture_decisions` | array[object] | Key architectural choices made, including alternatives considered and tradeoffs | See example below |
| `affected_seams` | array[string] | Component seams affected by the decision | `["frontend-auth-api", "auth-database"]` |
| `compatibility_constraints` | array[string] | Constraints to preserve backward compatibility | `["不修改现有登录响应字段"]` |
| `task_decomposition` | object | Optional task breakdown view references | `{optional: true, refs: ["work/views/TASK_BOARD.md#AUTH-12"]}` |

### Architecture Decision Example

```yaml
architecture_decisions:
  - decision: "使用短期访问令牌和可轮换刷新令牌"
    alternatives:
      - "单一长效 JWT"
      - "服务端 Session"
    tradeoffs:
      - "增加服务端状态"
      - "降低令牌泄漏影响"
```

### Professional Validation Rules

1. Each architecture decision must list at least one alternative considered
2. Tradeoffs must explicitly document both positive and negative impacts
3. `affected_seames` must align with `atomic_change_set.target_scope` (at least partial overlap)
4. `compatibility_constraints` must be verified against existing API contracts

### Evidence Binding Rules

Architectural decisions that affect security posture MUST be accompanied by Evidence from Security Auditor corresponding to threat categories identified in the decision. For example, if choosing a session-based approach over token-based, the Security Auditor must provide evidence validating the session security controls.

Task decomposition references must point to valid TASK_BOARD entries that are currently active or planned.

---

## Excluded Fields (Core Only)

Architect extensions CANNOT modify:
- `hypothesis.class` / `statement` / `falsification`
- `strategy_profile.action_class`
- `atomic_change_set.intent` / `target_scope`
- `risk.level` (may only suggest, not set)
- `verification_plan.validators`

The Architect provides context and justification; the Core determines the actual selection and execution.