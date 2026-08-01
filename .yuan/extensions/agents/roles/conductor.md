---
name: conductor
title: Conductor Agent
description: 'YuanForge Core framework document'
category: role
stage: published
created_at: 2026-07-31
last_modified: 2026-08-01
author: framework-team
---

# Yuan Agent Contract: Conductor

**Extension Namespace:** `conductor`  
**Extension Schema Version:** `yuan.agent.conductor/v1`  

## Proposal Contract

### Base Schema

This contract extends `.yuan/core/schemas/PROPOSAL.md`. All Core Envelope fields apply.

### Extension Namespace

`conductor`

### Extension Schema Version

`yuan.agent.conductor/v1`

### Required Professional Fields

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `intent_summary` | string | High-level summary of what the Work represents | `"Implement user authentication flow"` |
| `agent_selection` | array[string] | Roles recommended for this Work (overrides default batch ranking) | `["backend-dev", "architect"]` |
| `workflow_suggestion` | string | Recommended workflow template | `"feature-development/v1"` |
| `risk_suggestion` | string | Risk level recommendation based on Work scope | `R1` |
| `knowledge_injection` | array[string] | Knowledge modules to load before dispatching Agents | `["auth-pitfalls", "tdd-patterns"]` |

### Professional Validation Rules

1. `intent_summary` must be non-empty and under 200 characters
2. At least one agent must be listed in `agent_selection` if workload exceeds R1 risk
3. `workflow_suggestion` must reference an existing workflow definition in `.yuan/extensions/workflows/`
4. `risk_suggestion` must not exceed the maximum allowed by platform budget constraints

### Evidence Binding Rules

Conductor-generated Proposals do not require professional Evidence binding from other roles, but must include:
- A Journal entry tracing the original user message or requirement that initiated the Work
- Reference to the Conductor's own decision rationale when deviating from standard workflow

---

## Role-Specific Behavior Notes

The Conductor does not generate implementation Proposals directly. Instead, it:
1. Drafts the initial Work Contract
2. Dispatches Agent tasks via subagent/delegation mechanisms
3. Aggregates WAIT_AUTH and BLOCKED reasons for human review
4. Generates human-readable views from STATE + Attempts + Evidence

Conductor may generate security-critical Change Proposals when needed, which must pass all Core validation plus Security Auditor extension validation.