# Work Contract Template

**Schema:** `yuan.work/v1`

This file serves as a template for new work contracts. Actual work contracts should be instantiated with specific values when a new engineering task is initiated.

## Required Fields (to be filled per instance)

```yaml
schema: yuan.work/v1
work_id: W-XXXXXXXX   # Unique work identifier
revision: 1           # Starting revision, increment on changes
hash: sha256:...      # Hash of this document's canonical form
title: "Task Title"   # One-line title
description: "..."    # Detailed description
acceptance_criteria:  # List of verifiable conditions
  - "...".         # Each criterion must map to a validator
risk_level: R0        # Risk level: R0/R1/R2
extensions:
  agents:
    required: []      # Roles that must participate
    conditional: []   # Conditional role inclusions
  workflow: ""        # Optional workflow template
  policies: []        # Optional policy references
  knowledge: []       # Optional knowledge modules
```

## Example Minimal Work Contract

```yaml
schema: yuan.work/v1
work_id: W-000001
revision: 1
hash: sha256:d4e1f2a3b4c5d6e7f8g9h0i1j2k3l4m5n6o7p8q9r0s1t2u3v4w5x6y7z8
title: "Implement user authentication"
description: "Add registration, login, and session management features"
risk_level: R1
extensions:
  agents:
    required:
      - backend-dev
      - frontend-dev
      - tester
  workflow: feature-development/v1
  policies:
    - testing/default
    - review/security-sensitive
```
