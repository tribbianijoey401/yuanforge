---
name: protocol
title: Core Protocol
description: 'YuanForge Core framework document'
category: protocol
stage: published
created_at: 2026-07-31
last_modified: 2026-08-01
author: framework-team
---

# Yuan Core Protocol

**Version:** `yuan.core/v0.1`  
**Last Updated:** 2026-07-31

---

## 1. Core Authority and Priority

The `.yuan/core/` directory contains the **minimum authority** that constrains all non-deterministic Agent behavior. All other layers (Extensions, Platform, Legacy) derive their meaning from Core definitions.

Priority order when conflict arises:

```
Core Invariants > Core Schema > Extension Contract > Platform Goal
```

This priority chain ensures that LLM-generated content cannot violate fundamental safety guarantees.

---

## 2. Tick Fixed Steps

Each Core tick executes the following sequence atomically:

```
1. Read Work Contract (work/WORK.md)
2. Read State (work/STATE.md)
3. Collect Proposals (work/proposals/*.md)
4. Apply Core Schema Validation
5. Apply Role Extension Validation
6. Filter by Work Revision match
7. Generate Strategy Fingerprint for each candidate
8. Deduplicate by fingerprint (retain highest selection_rank)
9. Select first valid Proposal by selection_rank
10. Create Attempt (work/attempts/A-XXXXXX.md)
11. Execute Attempt (platform-dependent)
12. Collect Evidence (work/evidence/E-XXXXXX.md)
13. Run Reducer (work/REDUCER.md logic)
14. Update State (work/STATE.md with CAS)
15. Write Journal entry (work/journal/J-XXXXXX.md)
```

If any step returns `WAIT_AUTH`, `BLOCKED`, or results in an invalid state, the tick halts with error reason logged to journal.

---

## 3. Relationship Chain

### Work → Proposal → Attempt → Evidence → State

```
Work Contract (authorizes scope, defines agents, sets policies)
    ↓
Proposal (candidate action plan) --[selection]→ Attempt (executed action)
    ↓                                  ↓
[validation]                       [Evidence] (proves outcome)
                                    ↓
                              Reducer (determines next state)
                                    ↓
                              State (CAS update, persisted)
```

**Key invariant:** Every Evidence must bind to exactly one Attempt, which references exactly one Proposal, which corresponds to exactly one Work Revision.

---

## 4. Authorization Rules

### 4.1 Who Can Create Proposal?

- Any authorized Agent (as declared in Work Contract `extensions.agents.required`)
- Conductor may propose on behalf of human input (with `role: conductor` extension)
- Unauthenticated proposals are rejected at schema validation

### 4.2 Who Can Select Proposal?

**The Harness (automatic, mechanical)** — never a human or Agent directly. Selection is based on:
- Validated status (ADMITTED)
- Matching work revision
- Lowest `selection_rank` among candidates

### 4.3 Who Can Execute Attempt?

Platform-specific agent executing within the sandbox/Goal context defined by the Adapter layer. Execution must read current STATE before starting.

### 4.4 Who Can Create Evidence?

Automatically attached to Attempt post-execution by platform hook or manual assertion by executing Agent (must be signed/verified validator).

---

## 5. Work Revision Rules

Work Revision increments when:
- A Change is approved and applied
- Work Contract is explicitly updated via approved Change Proposal
- Human intervention triggers revision reset (with explicit authorization)

**Rule:** When Work Revision changes, ALL existing Evidence for previous revision becomes `INVALID` unless explicitly re-validated against new artifacts.

---

## 6. Persistence and Recovery

### 6.1 State as Single Source of Truth

`work/STATE.md` is the **only** authoritative source for recovery. All other view files (TASK_BOARD, PROGRESS, SESSION) are generated from STATE + Attempts + Evidence and may not be written to directly.

### 6.2 Recovery Procedure

To recover from interruption:
1. Read latest STATE.md
2. Check if `current_attempt` exists — if so, resume or restart based on atomicity guarantees
3. If no current attempt, check `pending_changes` queue
4. Re-scan proposals matching current work revision
5. Resume tick cycle

### 6.3 Checkpoint Frequency

State is written after every completed Tick (step 14 above). No intermediate state is persisted.

---

## 7. References

- `INVARIANTS.md` — all safety guarantees that must hold at every tick boundary
- `REDUCER.md` — deterministic reduction logic from evidence to state transition
- `schemas/PROPOSAL.md` — proposal envelope structure
- `schemas/ATTEMPT.md` — attempt execution record
- `schemas/EVIDENCE.md` — evidence binding format
- `schemas/STATE.md` — state structure and CAS semantics

---

**© YuanCore v0.1 | Mechanical Constrained Deterministic Engineering Engine**
