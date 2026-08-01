---
name: work-schema
title: Work Schema
description: 'YuanForge Core framework document'
category: schema
stage: published
created_at: 2026-07-31
last_modified: 2026-08-01
author: framework-team
---

# Yuan Core Work Contract Schema

**Schema ID:** `yuan.work/v1`  
**Last Updated:** 2026-07-31

## Purpose

The Work Contract defines the scope, objectives, constraints, and agent configuration for a specific engineering task. It serves as the root document from which all Proposals, Attempts, and Evidence derive their context.

## Required Fields

| Field | Type | Description |
|-------|------|-------------|
| `schema` | string | Must be `yuan.work/v1` |
| `work_id` | string | Unique identifier, format: W-XXXXXXXX |
| `revision` | integer | Monotonically incremented on each update |
| `hash` | string | SHA256 of this document's canonical form |
| `title` | string | Human-readable title of the work |
| `description` | string | Detailed description of what needs to be done |
| `acceptance_criteria` | array[string] | List of conditions that define "done" (each must be provable via Evidence) |
| `risk_level` | string | Overall risk severity: R0/R1/R2 |
| `extensions.agents.required` | array[string] | Roles that MUST participate |
| `extensions.agents.conditional` | array[object] | Conditional role inclusion based on criteria |
| `extensions.workflow` | string | Workflow template to follow |
| `extensions.policies` | array[string] | Policy rules applicable to this work |
| `extensions.knowledge.load` | array[object] | Knowledge modules to inject into Agent context |

### Conditional Agent Example

```yaml
extensions:
  agents:
    required:
      - backend-dev
      - tester
    conditional:
      - role: security-auditor
        when:
          risk_at_least: R1
```

## Validation Rules

1. All `acceptance_criteria` must map to at least one validator ID referenced in Proposal verification profiles
2. Every required agent role must have a corresponding Extension contract under `.yuan/extensions/agents/roles/`
3. `risk_level` must not exceed maximum permitted by platform budget/gate policies
4. Once Revision N is completed, only Conductor may increment to Revision N+1 via approved Change

## References

- `PROPOSAL.md` — how proposals bind to Work Revision
- `STATE.md` — state tracks current Work Revision
- `INVARIANTS.md` — invariant I2 binds evidence to Work Revision
