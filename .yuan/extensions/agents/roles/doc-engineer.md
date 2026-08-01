# Yuan Agent Contract: Doc Engineer

**Extension Namespace:** `doc-engineer`
**Extension Schema Version:** `yuan.agent.doc-engineer/v1`

## Proposal Contract

### Base Schema

This contract extends `.yuan/core/schemas/PROPOSAL.md`. All Core Envelope fields apply.

### Extension Namespace

`doc-engineer`

### Extension Schema Version

`yuan.agent.doc-engineer/v1`

### Required Professional Fields

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `docs_updated` | array[object] | Documents updated in this pass | See example below |
| `knowledge_distilled` | array[object] | Knowledge artifacts distilled | See example below |
| `cross_reference_check` | object | Dead link and reference validation | See example below |
| `change_type` | string | Type of change triggering documentation | `"incremental"` or `"milestone"` |

### Docs Updated Example

```yaml
docs_updated:
  - document: "docs/API.md"
    change: "added endpoint POST /refresh"
    evidence_ref: "E-DOC-001"
  - document: "docs/ARCHITECTURE.md"
    change: "updated data model section"
    evidence_ref: "E-DOC-002"
```

### Knowledge Distilled Example

```yaml
knowledge_distilled:
  - artifact: "knowledge/pitfalls/PIT-001.md"
    source: "BUG-042.md"
    distillation: "JWT token 轮换需注意并发场景"
    evidence_ref: "E-DOC-003"
  - artifact: "docs/glossary.md"
    change: "added term 'refresh token rotation'"
    evidence_ref: "E-DOC-004"
```

### Cross Reference Check Example

```yaml
cross_reference_check:
  dead_links: 0
  broken_references: 0
  stale_references: 0
  evidence_ref: "E-DOC-005"
```

### Professional Validation Rules

1. `docs_updated` MUST list every document modified in this pass
2. Each entry in `docs_updated` MUST have a non-empty `evidence_ref`
3. `knowledge_distilled` entries MUST reference source BUG/ADR files
4. `cross_reference_check` MUST show zero dead links before marking as complete
5. `change_type` MUST match the trigger condition (incremental for per-task, milestone for phase-end)

### Evidence Binding Rules

Doc Engineer conclusions require concrete Evidence:
- Each `docs_updated` entry MUST reference the actual document as Evidence
- Each `knowledge_distilled` entry MUST reference the source artifact and distilled output
- "No documentation changes needed" MUST be explicitly stated with evidence

Pure assertions like "documentation is up to date" without evidence-backed checks are rejected.

---

## Excluded Fields (Core Only)

Doc Engineer extensions CANNOT modify:
- `hypothesis` fields (Engineer documents, doesn't define hypotheses)
- `strategy_profile.action_class`
- `atomic_change_set.target_scope` (Engineer updates docs, doesn't modify implementation scope)
- `risk.level` (documentation changes are advisory and don't affect risk)
- `verification_plan.validators` (Engineer produces documentation evidence, but validation is Core-managed)
