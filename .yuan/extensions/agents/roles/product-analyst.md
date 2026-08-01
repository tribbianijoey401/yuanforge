# Yuan Agent Contract: Product Analyst

**Extension Namespace:** `product-analyst`
**Extension Schema Version:** `yuan.agent.product-analyst/v1`

## Proposal Contract

### Base Schema

This contract extends `.yuan/core/schemas/PROPOSAL.md`. All Core Envelope fields apply.

### Extension Namespace

`product-analyst`

### Extension Schema Version

`yuan.agent.product-analyst/v1`

### Required Professional Fields

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `user_stories` | array[string] | Structured user stories | `["作为用户，我想要登录，以便访问个性化内容"]` |
| `acceptance_criteria` | array[object] | Given/When/Then AC per 5 dimensions | See example below |
| `risk_label` | string | Risk tag: R0/R1/R2 | `"R1"` |
| `priority` | string | Feature priority: P0/P1/P2/P3 | `"P1"` |
| `clarification_log` | array[object] | Q&A pairs per dimension | See example below |

### Acceptance Criteria Example

```yaml
acceptance_criteria:
  - id: AC-AUTH-01
    dimension: scope
    statement: "用户输入有效邮箱和密码后，系统返回 JWT token"
    given: "用户未登录状态"
    when: "POST /login 携带有效凭据"
    then: "返回 {token, expires_in}，状态码 200"
  - id: AC-AUTH-02
    dimension: interaction
    statement: "登录失败时返回明确错误信息"
    given: "用户输入错误密码"
    when: "POST /login 携带错误凭据"
    then: "返回 {error: 'invalid_credentials'}，状态码 401"
```

### Clarification Log Example

```yaml
clarification_log:
  - dimension: scope
    question: "登录是否支持第三方 OAuth？"
    answer: "Phase 1 仅支持邮箱密码，OAuth 在 Phase 3"
    source: "用户确认"
  - dimension: interaction
    question: "密码强度要求是什么？"
    answer: "最少 8 位，含大小写和数字"
    source: "安全规范要求"
```

### Professional Validation Rules

1. Each `acceptance_criteria` MUST have a non-empty `id`, `dimension`, `statement`, `given`, `when`, `then`
2. `risk_label` MUST be one of: `R0`, `R1`, `R2`
3. `priority` MUST be one of: `P0`, `P1`, `P2`, `P3`
4. `clarification_log` MUST cover at least the 5 dimensions (scope/interaction/exception/data/nonfunctional), even if some are marked as "not applicable"
5. All `user_stories` MUST follow the format: `作为 [角色]，我想要 [功能]，以便 [目的]`

### Evidence Binding Rules

Product Analyst claims must reference concrete Evidence:
- Each `acceptance_criteria` must be traceable to a specific User Story
- `risk_label` must be justified by at least one `clarification_log` entry
- Feature scope boundaries must be documented in `clarification_log`

Pure assertions like "all ACs are clear" without explicit dimension coverage are rejected.

---

## Excluded Fields (Core Only)

Product Analyst extensions CANNOT modify:
- `hypothesis` fields (PA discovers requirements, doesn't hypothesize implementation)
- `strategy_profile.action_class`
- `atomic_change_set.target_scope` (PA defines scope at requirements level, not implementation)
- `risk.level` (PA labels risk, but Core determines final level based on all evidence)
- `verification_plan.validators` (PA provides ACs, but validators are chosen by Core)
