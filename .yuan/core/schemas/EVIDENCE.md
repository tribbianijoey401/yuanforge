---
name: evidence-schema
title: Evidence Schema
description: 'YuanForge Core framework document'
category: schema
stage: published
created_at: 2026-07-31
last_modified: 2026-08-01
author: framework-team
---

# Yuan Core Evidence Schema

**Schema ID:** `yuan.evidence/v1`  
**Last Updated:** 2026-07-31

## Purpose

Evidence provides **verifiable proof** that a particular claim about an artifact has been established through validated execution. Agent self-declarations alone do not constitute Evidence.

## Required Fields

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `schema` | string | Must be `yuan.evidence/v1` | `yuan.evidence/v1` |
| `evidence_id` | string | Format: E-XXXXXXXX | `E-000043` |
| `claim` | string | What this evidence proves | `"Refresh token replay request rejected"` |
| `bound_work_revision` | integer | Work Revision this evidence relates to | `7` |
| `artifact_hash` | string | SHA256 of the artifact being validated | `sha256:...` |
| `attempt_id` | string | The Attempt that produced this evidence | `A-000018` |
| `validator.id` | string | Validator ID that generated this evidence | `refresh-token-reuse-test` |
| `validator.version` | string | Validator version hash | `v1.sha256:...` |
| `validator.hash` | string | Hash of validator code/script | `sha256:...` |
| `environment_hash` | string | SHA256 of execution environment config | `sha256:...` |
| `result` | string | One of: pass / fail / unknown | `pass` |
| `status` | string | One of: valid / invalid / stale | `valid` |
| `raw_output_ref` | null \| string | Path to raw output artifact (optional) | `artifacts/test-output-000043.txt` |

## Key Invariants

1. **I2**: `bound_work_revision` must match current Work Revision at time of validation
2. **I3**: `artifact_hash` must match actual file hash at time of validation
3. **I4**: If another Evidence with same claim, validator, and artifact_hash already marked pass, duplicate is rejected

## Lifecycle

Evidence is created automatically after Attempt completion when validators run:

```
Attempt completes → Run all validators in verification_profile → 
  Produce Evidence records → Attach to Attempt → 
  Reducer evaluates Evidence → Update STATE
```

Manual Evidence (Conductor-submitted) requires manual: true flag and additional approval.

## References

- `INVARIANTS.md` — invariant checks on Evidence binding
- `ATTEMPT.md` — Evidence references stored in Attempt verification section
- `PROPOSAL.md` — Expected Evidence IDs listed in verification_plan
