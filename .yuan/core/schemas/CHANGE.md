---
name: change-schema
title: Change Schema
description: 'YuanForge Core framework document'
category: schema
stage: published
created_at: 2026-07-31
last_modified: 2026-08-01
author: framework-team
---

# Yuan Core Change Schema

**Schema ID:** `yuan.change/v1`  
**Last Updated:** 2026-07-31

## Purpose

A Change represents a proposed modification to the Work Contract itself (not just implementation changes). Changes must go through the full Proposal→Attempt→Evidence pipeline before application to Work Revision.

## Required Fields

| Field | Type | Description |
|-------|------|-------------|
| `schema` | string | Must be `yuan.change/v1` |
| `change_id` | string | Format: C-XXXXXXXX |
| `source_work_revision` | integer | Work revision this change targets |
| `target_work_revision` | integer | Resulting revision after change applied |
| `proposal_id` | string | Referenced Proposal that authorized this change |
| `change_type` | string | One of: acceptance_criteria_add / modify / remove / risk_level_update / agent_requirement_add/modify / policy_update / knowledge_load |
| `description` | string | Human-readable summary |
| `approved_by` | array[string] | Validator IDs that approved this change |
| `applied` | boolean | Whether change has been applied to Work Contract |
| `applied_at` | null \| ISO 8601 timestamp | When applied |

## Change Application Flow

1. Proposal submitted with intent to modify Work Contract
2. Proposal selected (higher priority than implementation proposals)
3. Attempt executes Work Contract modification (requires special permission)
4. Evidence produced confirming modification succeeded
5. Change record marked applied=true
6. Work Contract revision incremented
7. Previous Evidence invalidated per invariant I2

## References

- `PROTOCOL.md` — Work Revision change triggers evidence invalidation
- `PROPOSAL.md` — Proposal may include work modification intent
- `INVARIANTS.md` — I2 requires re-validation on revision bump
