# Yuan Agent Contract: Design Reviewer

**Extension Namespace:** `design-reviewer`
**Extension Schema Version:** `yuan.agent.design-reviewer/v1`

## Proposal Contract

### Base Schema

This contract extends `.yuan/core/schemas/PROPOSAL.md`. All Core Envelope fields apply.

### Extension Namespace

`design-reviewer`

### Extension Schema Version

`yuan.agent.design-reviewer/v1`

### Required Professional Fields

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `api_contract_review` | array[object] | API design review results | See example below |
| `data_model_review` | array[object] | Data model review results | See example below |
| `architecture_review` | array[object] | Architecture design review results | See example below |
| `boundary_conditions` | array[object] | Boundary condition gaps found | See example below |
| `confrontation_attempts` | array[object] | Non-obvious scenarios tested | See example below |

### API Contract Review Example

```yaml
api_contract_review:
  - endpoint: POST /login
    issue: "缺少 rate limiting 设计"
    severity: blocker
    recommendation: "添加限流策略到 Plan"
  - endpoint: GET /users/:id
    issue: "未标注权限控制"
    severity: blocker
    recommendation: "添加 auth middleware 说明"
```

### Data Model Review Example

```yaml
data_model_review:
  - entity: User
    issue: "缺 email 唯一索引"
    severity: warning
    recommendation: "添加 UNIQUE 约束"
  - entity: Post
    issue: "软删除未设计"
    severity: blocker
    recommendation: "添加 deleted_at 字段"
```

### Architecture Review Example

```yaml
architecture_review:
  - module: "auth-service"
    issue: "与 user-service 存在循环依赖"
    severity: warning
    recommendation: "抽取 shared/user 模块解耦"
```

### Confrontation Attempts Example

```yaml
confrontation_attempts:
  - dimension: "requirement_coverage"
    attempt: "AC 中提到的 OAuth 登录，Plan 里有对应 Task 吗？"
    result: "Plan 仅覆盖邮箱密码登录，OAuth 在 Phase 3 — 已记录为已知限制"
  - dimension: "boundary_condition"
    attempt: "并发请求同时修改同一条记录"
    result: "Plan 未设计乐观锁 — 标注 Advisory"
  - dimension: "security_design"
    attempt: "所有端点的认证/授权是否一致？"
    result: "admin 路由组缺少 auth middleware 设计声明 — 标注 Blocker"
```

### Professional Validation Rules

1. `api_contract_review` MUST cover ALL endpoints in `PLAN.md`
2. `data_model_review` MUST cover ALL entities in `PLAN.md`
3. `confrontation_attempts` MUST contain at least 3 entries
4. Each finding severity MUST be one of: `blocker`, `warning`, `advisory`
5. Blocker findings MUST have a clear, actionable recommendation

### Evidence Binding Rules

Design Reviewer conclusions require concrete Evidence:
- Each review finding MUST reference specific sections of PLAN.md as Evidence
- "No issues found" MUST explicitly state which API endpoints, entities, and modules were checked
- Confrontation attempts MUST have documented results

Pure assertions like "design is sound" without evidence-backed reviews are rejected.

---

## Excluded Fields (Core Only)

Design Reviewer extensions CANNOT modify:
- `hypothesis` fields (Reviewer evaluates design, doesn't define hypotheses)
- `strategy_profile.action_class`
- `atomic_change_set.target_scope` (Reviewer observes design, doesn't modify code)
- `risk.level` (Reviewer may recommend elevation for design defects, but Core makes final determination)
- `verification_plan.validators` (Reviewer provides design evidence, but validation is Core-managed)
