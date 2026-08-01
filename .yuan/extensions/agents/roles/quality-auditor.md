# Yuan Agent Contract: Quality Auditor

**Extension Namespace:** `quality-auditor`
**Extension Schema Version:** `yuan.agent.quality-auditor/v1`

## Proposal Contract

### Base Schema

This contract extends `.yuan/core/schemas/PROPOSAL.md`. All Core Envelope fields apply.

### Extension Namespace

`quality-auditor`

### Extension Schema Version

`yuan.agent.quality-auditor/v1`

### Required Professional Fields

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `performance_checks` | array[object] | Performance-related checks | See example below |
| `db_checks` | array[object] | Database design checks | See example below |
| `code_quality_checks` | array[object] | Code quality checks | See example below |
| `findings` | array[object] | Discovered issues with severity | See example below |
| `module_depth_analysis` | array[object] | Shallow module detection | See example below |

### Performance Checks Example

```yaml
performance_checks:
  - check_id: QC-PERF-001
    description: "热点路径 N+1 查询检测"
    status: executed
    result: fail
    evidence_ref: "E-QA-001"
    finding_ref: "F-QA-001"
  - check_id: QC-PERF-002
    description: "缓存策略有效性"
    status: executed
    result: pass
    evidence_ref: "E-QA-002"
```

### DB Checks Example

```yaml
db_checks:
  - check_id: QC-DB-001
    description: "users 表索引策略"
    status: executed
    result: fail
    evidence_ref: "E-QA-003"
    finding_ref: "F-QA-002"
  - check_id: QC-DB-002
    description: "迁移脚本幂等性"
    status: executed
    result: pass
    evidence_ref: "E-QA-004"
```

### Findings Example

```yaml
findings:
  - finding_id: F-QA-001
    severity: warning
    category: performance
    description: "GET /api/posts 存在 N+1 查询（10 次额外查询）"
    evidence_ref: "E-QA-001"
    remediation: "使用 JOIN 或批量查询替代循环查询"
    module: "post-service"
  - finding_id: F-QA-002
    severity: blocker
    category: database
    description: "users 表缺少 email 唯一索引"
    evidence_ref: "E-QA-003"
    remediation: "添加 UNIQUE INDEX idx_users_email"
    module: "user-service"
```

### Module Depth Analysis Example

```yaml
module_depth_analysis:
  - module: "payment/processor.go"
    assessed: true
    verdict: "ok"
    note: "接口与实现复杂度差异合理，非 shallow module"
  - module: "notification/sender.go"
    assessed: true
    verdict: "shallow"
    note: "接口与实现几乎等价，建议合并或增加抽象价值"
```

### Professional Validation Rules

1. `performance_checks`, `db_checks`, `code_quality_checks` MUST each contain at least 1 entry
2. `findings` severity MUST be one of: `blocker`, `warning`, `advisory`
3. Advisory findings accumulating >= 3 per module trigger automatic escalation to Blocker
4. `module_depth_analysis` MUST assess every non-trivial module in `atomic_change_set.target_scope`
5. All `findings` MUST have a non-empty `evidence_ref`

### Evidence Binding Rules

Quality Auditor conclusions require concrete Evidence:
- Every `executed` check MUST reference specific Evidence IDs
- Every `blocker` finding MUST reference Evidence of the issue
- Shallow module detection must include quantitative complexity assessment

Pure assertions like "code quality is good" without evidence-backed checks are rejected.

---

## Excluded Fields (Core Only)

Quality Auditor extensions CANNOT modify:
- `hypothesis` fields (Auditor evaluates quality, doesn't define hypotheses)
- `strategy_profile.action_class`
- `atomic_change_set.target_scope` (Auditor observes, doesn't modify code)
- `risk.level` (Auditor may recommend elevation based on findings, but Core makes final determination)
- `verification_plan.validators` (Auditor provides quality evidence, but validation is Core-managed)
