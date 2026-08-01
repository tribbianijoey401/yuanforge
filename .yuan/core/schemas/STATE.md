---
name: state-schema
title: State Schema
description: 'YuanForge Core framework document'
category: schema
stage: published
created_at: 2026-07-31
last_modified: 2026-08-01
author: framework-team
---

# Yuan Core State Schema

**Schema ID:** `yuan.state/v1`  
**Last Updated:** 2026-07-31

## Purpose

`work/STATE.md` is the **single authoritative source** for persistent state recovery. All other view documents (TASK_BOARD, PROGRESS, SESSION) are derived from STATE + Attempts + Evidence and must NOT be written directly.

## Required Fields

| Field | Type | Description |
|-------|------|-------------|
| `schema` | string | Must be `yuan.state/v1` |
| `current_revision` | integer | Current active Work Revision |
| `current_artifact_hash` | string | SHA256 of workspace at this revision |
| `status` | string | One of: IDLE / RUNNING / PAUSED / COMPLETE / FAILED |
| `attempt_id` | null \| string | Currently executing Attempt ID (null if idle) |
| `pending_changes` | array[object] | Approved changes awaiting application |
| `side_effect_trackers` | array[object] | Tracking ongoing non-reversible operations |
| `journals_start` | string | First Journal ID in chain |
| `journals_end` | string | Most recent Journal ID |

## CAS (Compare-And-Swap) Updates

All STATE updates must use CAS semantics:

```yaml
# Read current state
old_state = read("work/STATE.md")

# Compute new state based on reducer result
new_state = old_state.with_changes(...)

# Verify no concurrent modification
if new_state.expected_revision == old_state.current_revision:
    write("work/STATE.md", new_state)
else:
    reject("Concurrent modification detected")
```

This prevents race conditions between concurrent ticks or recovery scenarios.

## State Transition Table

| From → To | trigger | condition |
|-----------|---------|-----------|
| IDLE → RUNNING | Harness selects Proposal, creates Attempt | Valid proposal + all preconditions met |
| RUNNING → PAUSED | External interrupt or WAIT_AUTH decision | Human intervention needed |
| RUNNING → COMPLETE | Reducer returns COMPLETE | All ACs satisfied |
| RUNNING → FAILED | Reducer returns BLOCKED or unrecoverable error | Invariant violation |
| RUNNING → CONTINUE | Reducer requires refinement | New evidence generated same strategy |
| IDLE → RUNNING (recovery) | Restore from persistent storage | Read STATE, resume attempt if incomplete |

## References

- `PROTOCOL.md` — tick sequence reads STATE before each iteration
- `ATTEMPT.md` — attempt records link to STATE revision
- `REDUCER.md` — reducer output determines next STATE transition
