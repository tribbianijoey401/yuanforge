---
name: proposal-schema
title: Proposal Schema
description: 'YuanForge Core framework document'
category: schema
stage: published
created_at: 2026-07-31
last_modified: 2026-08-01
author: framework-team
---

# Yuan Core Proposal Schema

**Schema ID:** `yuan.proposal/v1`  
**Last Updated:** 2026-07-31

---

## Structure

A Proposal represents a **candidate action plan** submitted by an Agent for consideration by the Harness. It consists of two parts:

1. **Core Envelope** — Stable fields understood by the Harness (deterministic selection)
2. **Role Extension** — Agent-specific professional context (non-deterministic, enriched by role)

The Core Envelope is what enters the Strategy Fingerprint and Selection process. The Role Extension is preserved but not used for Core decisions.

---

## Core Envelope Fields

### Required Fields

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `proposal_id` | string | Unique identifier, format: P-XXXXXXXX (8-digit zero-padded) | `P-000042` |
| `selection_batch` | string | Batch identifier this proposal belongs to | `B-000008` |
| `selection_rank` | integer | Priority rank within batch (lower = higher priority) | `20` |
| `work.revision` | integer | Work Contract revision this proposal targets | `7` |
| `work.hash` | string | SHA256 hash of current work document | `sha256:a1b2c3...` |
| `producer.agent_id` | string | Unique identifier of generating Agent | `backend-dev-01` |
| `producer.role` | string | Role category of producer | `backend-dev` |
| `producer.platform` | string | Platform where Agent executed | `codex` / `claude` / `hermes` |
| `hypothesis.class` | string | Category of problem being addressed | `implementation_gap` |
| `hypothesis.statement` | string | Concise description of assumed gap | `"Login interface lacks refresh token rotation"` |
| `hypothesis.falsification` | string | Current evidence that might contradict hypothesis | `"Current implementation already invalidates old refresh tokens"` |
| `strategy_profile.target_scope` | array[string] | Files/directories to be modified | `["src/auth/token.go", "tests/auth/token_test.go"]` |
| `strategy_profile.action_class` | string | Type of atomic action | `code_change` / `config_update` / `test_addition` |
| `strategy_profile.key_parameters` | object | Key parameters affecting strategy fingerprint | `{token_rotation: true, migration_required: false}` |
| `strategy_profile.relevant_input_refs` | array[string] | Artifact hashes or evidence IDs this proposal depends on | `["artifact:sha256:...", "evidence:E-000031"]` |
| `strategy_profile.verification_profile` | array[string] | Validator IDs required for completion | `["auth-unit-tests", "refresh-token-reuse-test"]` |
| `atomic_change_set.intent` | string | Human-readable summary of change intent | `"Add one-time refresh token rotation"` |
| `atomic_change_set.target_scope` | array[string] | Files targeted by the actual change (must overlap with strategy_profile.target_scope) | Same as above |
| `atomic_change_set.expected_effect` | array[string] | Observable outcomes after execution | `["Old refresh tokens become invalidated after use"]` |
| `atomic_change_set.side_effect_class` | class of side effects produced | `local_reversible` / `database_migration` / `external_api_call` | `local_reversible` |
| `verification_plan.validators` | array[string] | List of validator IDs to execute | `["auth-unit-tests", "refresh-token-reuse-test"]` |
| `verification_plan.expected_evidence` | array[string] | Expected Evidence IDs that will validate completion | `["AC-AUTH-04", "INV-SEC-03"]` |
| `risk.level` | string | Risk severity: R0 (low), R1 (medium), R2 (high) | `R1` |
| `risk.reasons` | array[string] | Why this risk level was assigned | `["Modifies auth state transition"]` |
| `extensions` | object | Role-extension namespaces (see below) | See example |

### Optional Fields

| Field | Type | Description |
|-------|------|-------------|
| `proposal.created_at` | timestamp | Auto-generated submission time |
| `proposal.submitted_by` | string | Human operator (if created manually via Conductor) |

---

## Role Extension Namespace

Each Agent role may add an extension namespace under the `extensions` object. These fields:

- Are **ignored** by Core for selection/fingerprinting purposes
- Must match the schema version declared in the Extension contract
- Cannot override any Core Envelope field (Rule One: Core Field Priority)
- Professional conclusions must reference Evidence IDs, not stand alone

### Example Extension: backend-dev

```yaml
extensions:
  backend-dev:
    schema: yuan.agent.backend-dev/v1
    affected_components:
      - auth-service
    data_model_changes:
      changed: true
      entities:
        - refresh_tokens
      migration_required: false
      compatibility_impact: none
    implementation_notes:
      concurrency_considerations:
        - "同一刷新令牌只能成功兑换一次"
      backward_compatibility:
        - "已签发访问令牌不受影响"
```

### Example Extension: security-auditor

```yaml
extensions:
  security-auditor:
    schema: yuan.agent.security-auditor/v1
    threat_categories:
      - token_replay
      - privilege_escalation
    findings:
      - finding_id: F-0004
        severity: medium
        claim: "刷新令牌缺少轮换"
        evidence_ref: E-000037
```

---

## Proposal Lifecycle States

| State | Meaning | Transitions To |
|-------|---------|----------------|
| `SUBMITTED` | Agent has created and submitted proposal | ADMIT_REJECTED or SELECTED |
| `ADMIT_REJECTED` | Failed Core or Role Validation | (terminal) |
| `SELECTED` | Harness chose this proposal for Attempt creation | ATTEMPT_COMPLETED |
| `NOT_SELECTED` | Higher-ranked proposal was selected | (terminal) |
| `SUPERSEDED` | Newer Work Revision made this obsolete | (terminal) |

---

## Strategy Fingerprint Calculation

The Strategy Fingerprint is computed from normalized Core Envelope fields **excluding**:
- `proposal_id`, `selection_batch`, `selection_rank`, timestamps, random strings
- Any content under `extensions.*` (unless explicitly mapped to core key_parameters)

Fingerprint input order (canonical serialization):

```
hypothesis.class + ":" + hypothesis.statement
+ "|" + sorted(normalized(atomic_change_set.target_scope))
+ "|" + strategy_profile.action_class
+ "|" + sorted(normalized(strategy_profile.key_parameters))
+ "|" + sorted(relevant_input_hashes)
+ "|" + sorted(validator_ids_with_hashes)
```

Fingerprint algorithm: `SHA256(serialized_input)` → lowercase hex string

This ensures that semantically identical proposals produce the same fingerprint regardless of wording differences in free-text fields.

---

## Validation Rules

### Core Schema Validation (Mandatory for All Proposals)

Must pass ALL of the following:

1. All required Core Envelope fields present and non-null
2. `work.revision` matches current active Work Revision
3. `proposal_id` follows pattern `P-\d{8}` and is unique within selection_batch
4. `selection_rank` is positive integer within valid range for batch
5. `target_scope` contains at least one valid file path
6. `strategy_profile.action_class` is one of: `code_change`, `config_update`, `test_addition`, `document_update`, `workflow_update`
7. `verification_profile.validators` list is non-empty
8. `atomic_change_set.target_scope` does not contain paths outside declared target scope (whitelist check)
9. No Core Trust Boundary paths appear in `atomic_change_set.target_scope`
10. `risk.level` is one of: `R0`, `R1`, `R2`

### Role Extension Validation (Conditional)

If `producer.role` has a registered Extension contract:
1. `extensions.{role}` object exists
2. `schema` field matches registered schema version for this role
3. All required professional fields per role contract are present
4. No conflict between Extension fields and Core fields (per Conflict Rules)
5. Evidence references in Extension exist in current Evidence store or are pending

---

## Sample Valid Proposal (Truncated)

```yaml
schema: yuan.proposal/v1

proposal_id: P-000042
selection_batch: B-000008
selection_rank: 20

work:
  revision: 7
  hash: sha256:d9f8e7c6b5a4z3x2v1u0t9s8r7q6p5o4n3m2l1k0j9i8h7g6f5e4d3c2b1a0

producer:
  agent_id: backend-dev-01
  role: backend-dev
  platform: codex

hypothesis:
  class: implementation_gap
  statement: "Refresh token rotation missing"
  falsification: "Current implementation already invalidates old refresh tokens"

strategy_profile:
  target_scope:
    - src/auth/token.go
    - src/auth/service.go
    - tests/auth/token_test.go
  action_class: code_change
  key_parameters:
    token_rotation: true
    migration_required: false
  relevant_input_refs:
    - artifact:sha256:a1b2c3d4e5f6...
    - evidence:E-000031
  verification_profile:
    - auth-unit-tests
    - refresh-token-reuse-test

atomic_change_set:
  intent: "Implement one-time refresh token rotation"
  target_scope:
    - src/auth/token.go
    - src/auth/service.go
    - tests/auth/token_test.go
  expected_effect:
    - "Old refresh tokens become invalidated after successful redemption"
  side_effect_class: local_reversible

verification_plan:
  validators:
    - auth-unit-tests
    - refresh-token-reuse-test
  expected_evidence:
    - AC-AUTH-04
    - INV-SEC-03

risk:
  level: R1
  reasons:
    - "Modifies auth state transition"
    - "Potential race condition on concurrent refresh"

extensions:
  backend-dev:
    schema: yuan.agent.backend-dev/v1
    affected_components:
      - auth-service
    data_model_changes:
      changed: true
      entities:
        - refresh_tokens
      migration_required: false
      compatibility_impact: none
    implementation_notes:
      concurrency_considerations:
        - "同一刷新令牌只能成功兑换一次"
      backward_compatibility:
        - "已签发访问令牌不受影响"
```

---

## References

- `schemas/STATE.md` — State document structure and CAS semantics
- `schemas/ATTEMPT.md` — Attempt record format
- `schemas/EVIDENCE.md` — Evidence binding format
- `PROTOCOL.md` — Core tick sequence and authority model
- `INVARIANTS.md` — Safety guarantees enforced by Reducer

**© YuanCore v0.1 | Proposal Specification**
