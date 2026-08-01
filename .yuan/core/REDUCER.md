---
name: reducer
title: Deterministic Reducer
description: 'YuanForge Core framework document'
category: protocol
stage: published
created_at: 2026-07-31
last_modified: 2026-08-01
author: framework-team
---

# Yuan Core Reducer

**Version:** `yuan.reducer/v0.1`  
**Last Updated:** 2026-07-31

---

## Result Types

The Reducer produces exactly one of these six results, evaluated in strict priority order:

```
1. WAIT_AUTH   — Requires human authorization before proceeding
2. BLOCKED     — Invariant violation or unknown error preventing progress
3. BUDGET_EXIT — Resource budget exhausted before completion
4. COMPLETE    — All ACs satisfied, work finished successfully
5. CORRECT     — Original hypothesis falsified; alternate valid strategy found
6. CONTINUE    — New evidence generated; same strategy needs refinement
```

**Mutual Exclusivity:** Exactly one result applies per Reducer invocation. Evaluation follows the order above; first match wins.

---

## Decision Table

| Condition | Result | Rationale |
|-----------|--------|-----------|
| Any invariant violation detected (I0-I7) | **BLOCKED** | Safety cannot be compromised |
| Unavailable validator required by verification plan returns UNKNOWN/ERROR | **BLOCKED** | Cannot verify correctness without all validators |
| Budget remaining ≤ 0 AND state ≠ final | **BUDGET_EXIT** | Resource exhaustion |
| proposal has WAIT_AUTH flag set by Role Extension | **WAIT_AUTH** | Needs human review (e.g., security-sensitive change) |
| All verification validators return PASS AND all invariants hold AND no pending side effects | **COMPLETE** | Work successfully finished |
| Strategy fingerprint matches existing Attempt with result COMPLETE BUT evidence for this revision is stale (work revision changed) | **CORRECT** | Previous solution invalid; need new approach |
| At least one validator returns FAIL AND new evidence can be generated to address the failure | **CONTINUE** | Same strategy can be corrected |
| No valid proposals remain in selection batch AND work not yet complete | **BUDGET_EXIT** | No more strategies to try |
| Evidence indicates artifact changed mid-attempt (hash mismatch) | **BLOCKED** | Integrity violation detected |

---

## Priority Enforcement Rules

### Rule P1: BLOCKED overrides everything

If any invariant fails, immediately halt and report specific violated invariants. Do not attempt recovery.

### Rule P2: WAIT_AUTH blocks automated progression

When a Role Extension (typically Security Auditor) sets `wait_auth: true`, the Reducer returns `WAIT_AUTH` regardless of other conditions. Human must explicitly approve via Conductor before retry.

### Rule P3: CORRECT supersedes CONTINUE

If the original hypothesis is proven false (e.g., tester finds critical bug that invalidates backend-dev's assumption), switch to a different strategy rather than continuing with the flawed one.

### Rule P4: Deterministic ordering

Given identical inputs (same Proposal set, same Evidence, same State), the Reducer **must** produce the same result. This is guaranteed by:
- Fixed evaluation order (top to bottom in decision table)
- Normalized fingerprint comparison
- Immutable invariant definitions

---

## Example Reduction Trace

```
Input:
  - State: revision=7, status=IN_PROGRESS, current_attempt=A-000018
  - Evidence: E-000043 (validator=refresh-token-reuse-test, result=pass)
  - Invariant checks: I0=PASS, I1=PASS, I2=PASS, I3=PASS, I4=PASS, I5=FAIL(pending migration), I6=PASS, I7=PASS
  - Budget: remaining_calls=5, max_calls=100

Evaluation:
  1. CHECK BLOCKED → I5 FAIL (pending migration side effect) → BLOCKED? 
     Actually I5 says "pending side effects block COMPLETION", not BLOCKED overall
     So continue...
  2. CHECK BUDGET_EXIT → 5 < 100 but work not complete → NO
  3. CHECK WAIT_AUTH → Not set → NO
  4. CHECK COMPLETE → I5 fail prevents COMPLETE → NO
  5. Check hypothesis falsification → No new contradictory evidence → NO CORRECT
  6. Check if we can generate NEW evidence → tester has additional test cases pending → CONTINUE

Result: CONTINUE
Additional info: pending_side_effects=[data_migration], next_action=re-run-with-additional-tests
```

---

## Implementation Notes

The Reducer should be implemented as a **pure function** (no side effects, no external input beyond provided inputs). This allows:

- Deterministic replay for debugging
- Shadow mode comparison during migration
- Formal verification of safety properties

---

**© YuanCore v0.1 | Deterministic State Reduction Specification**
