---
name: frontend-dev
title: Frontend Developer
description: 'YuanForge Core framework document'
category: role
stage: published
created_at: 2026-07-31
last_modified: 2026-08-01
author: framework-team
---

# Yuan Agent Contract: Frontend Developer

**Extension Namespace:** `frontend-dev`  
**Extension Schema Version:** `yuan.agent.frontend-dev/v1`  

## Proposal Contract

### Base Schema

This contract extends `.yuan/core/schemas/PROPOSAL.md`. All Core Envelope fields apply.

### Extension Namespace

`frontend-dev`

### Extension Schema Version

`yuan.agent.frontend-dev/v1`

### Required Professional Fields

| Field | Type | Description |
|-------|------|-------------|
| `ui_components` | array[string] | UI components affected by the change |
| `css_variables` | object | CSS variable modifications |
| `accessibility_compliance` | boolean | Whether changes maintain WCAG compliance |
| `cross_browser_support` | array[string] | Target browser compatibility list |

### Professional Validation Rules

1. All `ui_components` entries must correspond to actual frontend file paths matching `atomic_change_set.target_scope`
2. If `accessibility_compliance` is false, risk_level must be elevated to at least R1
3. `cross_browser_support` must include browsers mandated by Work Contract or default to ["chrome", "firefox", "safari"]

### Evidence Binding Rules

Frontend implementation claims about visual correctness require Evidence from:
- Visual regression testing tools (e.g., Percy, Chromatic) with reference snapshots
- Accessibility audit evidence (axe-core results, Lighthouse reports)
- Cross-browser test execution logs (Selenium, Playwright, etc.)

Assertions like "UI looks good" without attached Evidence are rejected during validation.

---

## Excluded Fields (Core Only)

Frontend extensions CANNOT modify hypothesis.class, strategy_profile.action_class, atomic_change_set.target_scope (must be subset of declared scope), verification_plan.validators, risk.level (may suggest elevation only), work revision. These Core responsibilities remain exclusive to the Proposal Core Envelope.
