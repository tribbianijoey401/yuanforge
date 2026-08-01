# Yuan Agent Contract: Spec Reviewer

**Extension Namespace:** `spec-reviewer`
**Extension Schema Version:** `yuan.agent.spec-reviewer/v1`

## Proposal Contract

### Base Schema

This contract extends `.yuan/core/schemas/PROPOSAL.md`. All Core Envelope fields apply.

### Extension Namespace

`spec-reviewer`

### Extension Schema Version

`yuan.agent.spec-reviewer/v1`

### Required Professional Fields

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `reviewed_ac` | array[object] | AC review results | See example below |
| `reviewed_api_contract` | array[object] | API contract verification | See example below |
| `boundary_questions` | array[string] | Confrontational questions raised | See example below |
| `confrontation_attempts` | array[object] | Actual confrontation paths tried | See example below |

### Reviewed AC Example

```yaml
reviewed_ac:
  - id: AC-AUTH-01
    status: pass
    note: "实现完全符合 AC 描述"
  - id: AC-AUTH-02
    status: fail
    note: "错误返回缺少具体错误码，仅返回 'invalid_credentials' 字符串"
```

### Reviewed API Contract Example

```yaml
reviewed_api_contract:
  - endpoint: POST /login
    expected: "{token: string, expires_in: int}"
    actual: "{access_token: string, token_type: 'bearer', expires_in: 3600}"
    status: pass
    note: "字段名略有不同但语义等价，已确认与文档一致"
```

### Confrontation Attempts Example

```yaml
confrontation_attempts:
  - dimension: boundary_condition
    question: "当用户同时从两个设备登录时，refresh token 轮换是否安全？"
    result: "发现 token 轮换未处理并发场景 — 已标注 Blocker"
  - dimension: state_machine
    question: "登录中途网络断开，session 状态是否可恢复？"
    result: "实现依赖 HTTP session，断开后无法恢复 — 建议记录为已知限制"
```

### Professional Validation Rules

1. `reviewed_ac` MUST cover ALL ACs listed in `verification_plan.expected_evidence`
2. `confrontation_attempts` MUST contain at least 1 entry (even if "未发现缺陷")
3. Each `boundary_question` must have a corresponding entry in `confrontation_attempts`
4. Blocker findings must include a clear description of the deviation
5. Advisory findings must be justified — personal preference alone is not sufficient

### Evidence Binding Rules

Spec Reviewer conclusions require concrete Evidence:
- Each `fail` in `reviewed_ac` must reference specific Evidence IDs from the implementation
- API contract mismatches must reference actual response samples as Evidence
- "No deviations found" requires explicit statement of which ACs and API contracts were checked

Pure assertions like "ACs are met" without line-by-line evidence are rejected.

---

## Excluded Fields (Core Only)

Spec Reviewer extensions CANNOT modify:
- `hypothesis` fields (Reviewer validates against hypothesis, doesn't define it)
- `strategy_profile.action_class`
- `atomic_change_set.target_scope` (Reviewer observes, doesn't modify code)
- `risk.level` (may recommend elevation based on deviations, but Core makes final determination)
- `verification_plan.validators` (Reviewer proposes findings, but validators are Core-managed)
