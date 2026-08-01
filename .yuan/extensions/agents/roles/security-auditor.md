# Yuan Agent Contract: Security Auditor

**Extension Namespace:** `security-auditor`
**Extension Schema Version:** `yuan.agent.security-auditor/v1`

## Proposal Contract

### Base Schema

This contract extends `.yuan/core/schemas/PROPOSAL.md`. All Core Envelope fields apply.

### Extension Namespace

`security-auditor`

### Extension Schema Version

`yuan.agent.security-auditor/v1`

### Required Professional Fields

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `threat_categories` | array[string] | Security threat categories checked | `["injection", "auth_bypass", "xsrf"]` |
| `security_checks` | array[object] | Individual security checks with evidence | See example below |
| `findings` | array[object] | Discovered vulnerabilities | See example below |
| `confrontation_paths` | array[object] | Non-expected input paths attempted | See example below |

### Security Checks Example

```yaml
security_checks:
  - check_id: SC-001
    category: injection
    description: "SQL 参数化查询验证"
    status: executed
    result: pass
    evidence_ref: "E-SEC-001"
  - check_id: SC-002
    category: auth_bypass
    description: "未认证接口访问控制"
    status: executed
    result: fail
    evidence_ref: "E-SEC-002"
    finding_ref: "F-001"
```

### Findings Example

```yaml
findings:
  - finding_id: F-001
    severity: blocker
    category: auth_bypass
    description: "GET /api/admin/users 未验证 session token"
    evidence_ref: "E-SEC-002"
    remediation: "添加 auth middleware 到 admin 路由组"
```

### Confrontation Paths Example

```yaml
confrontation_paths:
  - path: "parameter_injection"
    attempt: "传入 Unicode 混淆的 SQL 注入 payload"
    result: "参数化查询已防御，未发现可利用漏洞"
  - path: "auth_bypass"
    attempt: "未登录直接调用需登录接口"
    result: "发现 401 被误返回为 200 — 标注 Blocker"
```

### Professional Validation Rules

1. `security_checks` MUST include at least one check per threat category in `threat_categories`
2. Every executed check (`status: executed`) MUST have a non-empty `evidence_ref`
3. `findings` severity MUST be one of: `blocker`, `warning`, `advisory`
4. For R0 risk level: ALL threat categories MUST be audited (full audit)
5. For R1 risk level: key path audits only (auth, data access)
6. For R2 risk level: skip audit (document reason in `confrontation_paths`)

### Evidence Binding Rules

Security Auditor conclusions require concrete Evidence:
- Every `executed` security check MUST reference specific Evidence IDs
- Every `blocker` finding MUST reference Evidence of the vulnerability
- "No vulnerabilities found" MUST list all confrontation paths attempted with results

Pure assertions like "security is adequate" without evidence-backed checks are rejected.

---

## Excluded Fields (Core Only)

Security Auditor extensions CANNOT modify:
- `hypothesis` fields (Auditor checks security, doesn't define implementation hypotheses)
- `strategy_profile.action_class`
- `atomic_change_set.target_scope` (Auditor observes, doesn't modify code)
- `risk.level` (Auditor may recommend elevation for found vulnerabilities, but Core makes final determination)
- `verification_plan.validators` (Auditor provides security evidence, but validation is Core-managed)
