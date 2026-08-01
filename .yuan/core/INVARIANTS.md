---
name: invariants
title: Safety Invariants
description: 'YuanForge Core framework document'
category: invariant
stage: published
created_at: 2026-07-31
last_modified: 2026-08-01
author: framework-team
---

# Yuan Core Invariants

**Version:** `yuan.invariant/v0.1`  
**Last Updated:** 2026-07-31

---

## Overview

These invariants must hold **before and after every Tick**. Violation of any invariant results in `BLOCKED` state and requires human intervention to resolve.

---

## Universal Invariants (Apply to All Work)

### I0: Unauthorised Side Effects Prohibited

> **未授权副作用不得执行**

Any change not explicitly declared in `atomic_change_set.target_scope` and approved through the Proposal→Attempt→Evidence pipeline is forbidden.

**Enforcement:** Attempt execution environment must be sandboxed; file system writes only permitted within declared target scopes.

---

### I1: Validators Cannot Be Silently Bypassed

> **验证器不得被静默绕过**

Every validator listed in `verification_plan.validators` must produce valid Evidence before the corresponding Attempt can mark as complete. A validator returning failure or UNKNOWN causes the Attempt to fail.

**Exception:** `advisory` validation markers do not block progression but are logged for review.

---

### I2: Evidence Must Bind to Current Work Revision

> **Evidence 必须绑定当前 Work Revision**

Every Evidence record must contain `bound_work_revision` matching the current active Work Revision. Evidence from older revisions is automatically invalid upon revision bump.

---

### I3: Evidence Must Bind to Artifact Hash

> **Evidence 必须绑定当前 Artifact Hash**

Every Evidence must include `artifact_hash` matching the SHA256 of the artifact it validates. This prevents evidence from being reused against different code versions.

---

### I4: No Repeat Execution Without New Evidence

> **相同策略无新证据不得重复执行**

If a Strategy Fingerprint already has a successful COMPLETE evidence entry, attempting to execute the same fingerprint without new distinguishing evidence is rejected (`BLOCKED`).

**Strategy Fingerprint components:**
- hypothesis.class + statement
- normalized atomic_change_set.target_scope
- action_class
- normalized key_parameters
- relevant input hashes
- validator ids and hashes

---

### I5: Pending Side Effects Block Completion

> **存在未决副作用时不得 COMPLETE**

If an Attempt has side_effect_class that indicates pending work (e.g., `requires_manual_review`, `database_migration`), the Reducer cannot return `COMPLETE` until all side effects are resolved or explicitly acknowledged.

---

### I6: Unknown Validation Results Fail Closed

> **未知验证结果必须失败关闭**

If any validator returns status other than `pass` or `fail` (e.g., `unknown`, `timeout`, `error`), the default decision is to treat as failure unless the Work Contract specifies otherwise.

---

### I7: Core Trust Boundary Protection

> **普通 Attempt 不得修改 Core Trust Boundary**

Only proposals with `role: conductor` or explicit administrative privilege may modify files in `.yuan/core/`, `.yuan/VERSION`, or migration/baseline directories. Regular agent attempts are rejected if they target these paths.

---

## Work-Specific Invariants

Additional invariants are defined per-work in `work/WORK.md`. These supplement but never contradict universal invariants.

---

## Invariant Checking Mechanism

Each invariant maps to a validator ID registered in `validators/MANIFEST.md`:

| Invariant | Validator ID | Check Type |
|-----------|-------------|------------|
| I0 | `check-authorized-sides` | Static analysis on attempt target scope |
| I1 | `check-validator-execution` | Evidence verification log scan |
| I2 | `check-evidence-revision` | Schema validation during evidence load |
| I3 | `check-evidence-hash` | Hash comparison against artifact manifest |
| I4 | `check-fingerprint-dup` | Index lookup on strategy fingerprint store |
| I5 | `check-pending-sideeffects` | State transition rule in Reducer |
| I6 | `check-validation-results` | Evidence result value enumeration |
| I7 | `check-core-boundary-access` | File path whitelist validation |

---

**© YuanCore v0.1 | Safety Guarantee Specification**
