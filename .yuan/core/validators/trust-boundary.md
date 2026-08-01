---
name: trust-boundary
title: Core Trust Boundary
description: 核心信任边界定义，保护 Core 文件不被非授权修改
category: invariant
stage: published
created_at: 2026-07-31
last_modified: 2026-08-01
author: framework-team
---

# Yuan Core Trust Boundary

**Last Updated:** 2026-08-01
**Schema:** `yuan.core.trust-boundary/v2`

## Definition

The Core Trust Boundary is the set of files and directories whose integrity must be preserved to ensure the correctness and security of the entire multi-agent engineering system. No Attempt with `role` other than `conductor` or explicitly privileged administrative roles may modify files within this boundary.

## Protected Paths

```
.yuan/core/           ← Core protocol, schemas, invariants, reducer, baseline
.yuan/extensions/     ← Role contracts, workflows, policies, skills (read-only for non-conductor)
.yuan/platforms/      ← Platform adapters
work/STATE.md         ← Single source of truth for state recovery
work/journal/         ← Immutable audit trail (append-only)
work/STATE.md.lock    ← CAS lock file (if present)
```

## Rationale

| Path | Protection Reason |
|------|------------------|
| `.yuan/core/` | Contains the deterministic constraints themselves; modification would break the entire safety model |
| `.yuan/extensions/` | Extension contracts are approved via Change proposals; direct modification bypasses evidence chain |
| `.yuan/platforms/` | Platform adapters define Core-Platform mapping; tampering changes execution semantics |
| `work/STATE.md` | If corrupted or tampered, recovery from interruptions becomes impossible |
| `work/journal/` | Audit trail must be immutable for forensics and replay |

## Enforcement Mechanism

The Core Trust Boundary is enforced at **Proposal submission time** during Core Schema Validation:

1. Extract all paths from `atomic_change_set.target_scope`
2. Check each path against the protected paths list
3. If any match exists AND producer.role ≠ conductor (and not explicitly in allowed_admin_roles), reject Proposal with ADMIT_REJECTED

Violations of this boundary are invariant **I7** ("普通 Attempt 不得修改 Core Trust Boundary") and result in BLOCKED state.

## Exception Process

If an Extension legitimately requires modifying a protected path:

1. Conductor must submit a separate Change proposal with role: conductor
2. Change must describe exactly what is being modified and why
3. All applicable validators must approve the change
4. Work Revision must increment
5. All existing Evidence becomes invalidated per I2

This ensures that even boundary modifications go through the full evidence-driven pipeline.
