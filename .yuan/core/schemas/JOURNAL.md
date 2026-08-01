---
name: journal-schema
title: Journal Schema
description: 'YuanForge Core framework document'
category: schema
stage: published
created_at: 2026-07-31
last_modified: 2026-08-01
author: framework-team
---

# Yuan Core Journal Entry Schema

**Schema ID:** `yuan.journal/v1`  
**Last Updated:** 2026-07-31

## Purpose

The Journal maintains an immutable audit trail of all state transitions, attempt lifecycles, and significant events. Each tick produces at least one Journal entry.

## Required Fields

| Field | Type | Description |
|-------|------|-------------|
| `schema` | string | Must be `yuan.journal/v1` |
| `journal_id` | string | Format: J-XXXXXXXX |
| `timestamp` | ISO 8601 datetime | When event occurred |
| `tick_number` | integer | Global tick counter (monotonic) |
| `event_type` | string | One of: state_update / attempt_created / attempt_started / attempt_completed / attempt_failed / proposal_submitted / proposal_selected / reducer_result / evidence_recorded |
| `subject_type` | string | What affected: state / attempt / proposal / evidence / work |
| `subject_id` | string | ID of subject (e.g., attempt ID, state revision) |
| `previous_state` | null \| object | Snapshot before change (for rollback/debug) |
| `current_state` | object | Snapshot after change |
| `actor` | string | Who triggered: harness / agent:<role> / conductor / platform |
| `details` | object | Event-specific payload |

## Example: State Update Entry

```yaml
schema: yuan.journal/v1
journal_id: J-000001
timestamp: "2026-07-31T10:00:00Z"
tick_number: 1
event_type: state_update
subject_type: state
subject_id: "state"
previous_state: null
current_state:
  current_revision: 7
  status: RUNNING
  attempt_id: A-000018
actor: harness
details:
  transition: "IDLE→RUNNING"
  reason: "Selected proposal P-000042, created attempt A-000018"
```

## References

- `PROTOCOL.md` — journal write at step 15 of each tick
- `STATE.md` — CAS updates logged to journal
- `ATTEMPT.md` — phase transitions journal-logged
