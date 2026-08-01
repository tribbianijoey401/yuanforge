---
name: validator-manifest
title: Validator Manifest
description: 'YuanForge Core framework document'
category: schema
stage: published
created_at: 2026-07-31
last_modified: 2026-08-01
author: framework-team
---

# Yuan Core Validator Manifest

**Schema:** `yuan.validator.manifest/v1`  
**Last Updated:** 2026-07-31

## Purpose

This manifest registers all validators that may be referenced in Proposal verification profiles. Each validator entry defines an executable check that produces Evidence.

## Validator Registry

| Validator ID | Schema Version | Description | Target Category | Required |
|--------------|----------------|-------------|-----------------|----------|
| `auth-unit-tests` | v1.0 | Runs authentication unit tests | security / correctness | Optional |
| `refresh-token-reuse-test` | v1.0 | Tests refresh token replay prevention | security | Conditional on risk >= R1 |
| `check-authorized-sides` | v1.0 | Verifies I0: no unauthorized side effects | safety invariant | Mandatory |
| `check-validator-execution` | v1.0 | Verifies I1: all validators executed | safety invariant | Mandatory |
| `check-evidence-revision` | v1.0 | Verifies I2: evidence binds to correct work revision | safety invariant | Mandatory |
| `check-evidence-hash` | v1.0 | Verifies I3: evidence matches artifact hash | safety invariant | Mandatory |
| `check-fingerprint-dup` | v1.0 | Verifies I4: no duplicate strategy execution without new evidence | safety invariant | Mandatory |
| `check-pending-sideeffects` | v1.0 | Verifies I5: pending side effects handled correctly | safety invariant | Mandatory |
| `check-validation-results` | v1.0 | Verifies I6: unknown results fail closed | safety invariant | Mandatory |
| `check-core-boundary-access` | v1.0 | Verifies I7: Core Trust Boundary protected | safety invariant | Mandatory |

## Execution Model

Each validator is invoked with the following inputs:
- The Attempt's artifact hash (pre/post)
- The Evidence record being validated
- The Work Contract context
- The current State

Validators produce Evidence records as output. A validator returning `fail` or causing an exception causes the associated Attempt to be marked failed unless the validation level is `advisory`.

## References

- `PROPOSAL.md` — verification_profile references validator IDs
- `INVARIANTS.md` — each invariant maps to a validator
- `REDUCER.md` — reducer evaluates validator results
