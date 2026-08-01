# Yuan Agent Contract: UX Reviewer

**Extension Namespace:** `ux-reviewer`
**Extension Schema Version:** `yuan.agent.ux-reviewer/v1`

## Proposal Contract

### Base Schema

This contract extends `.yuan/core/schemas/PROPOSAL.md`. All Core Envelope fields apply.

### Extension Namespace

`ux-reviewer`

### Extension Schema Version

`yuan.agent.ux-reviewer/v1`

### Required Professional Fields

| Field | Type | Description | Example |
|-------|------|-------------|---------|
| `wcag_level` | string | WCAG compliance target | `"AA"` |
| `interaction_checks` | array[object] | UI interaction verification | See example below |
| `state_coverage` | array[string] | UI states checked | `["loading", "empty", "error", "success"]` |
| `design_parameters` | object | V/M/D knobs from UI Designer | See example below |
| `findings` | array[object] | UX issues with severity | See example below |
| `destructive_tests` | array[object] | Abuse/edge-case tests attempted | See example below |

### Design Parameters Example

```yaml
design_parameters:
  variance: 6
  motion: 4
  density: 3
  source: "UI Designer prototype"
```

### Interaction Checks Example

```yaml
interaction_checks:
  - check_id: UX-001
    description: "表单键盘导航"
    status: executed
    result: pass
    evidence_ref: "E-UX-001"
  - check_id: UX-002
    description: "屏幕阅读器兼容性"
    status: executed
    result: fail
    evidence_ref: "E-UX-002"
    finding_ref: "F-UX-001"
```

### Destructive Tests Example

```yaml
destructive_tests:
  - dimension: text_overflow
    attempt: "所有文本 ×2 长度，检查截断与溢出"
    result: "长文本正确截断，无布局破坏"
  - dimension: rapid_click
    attempt: "提交按钮连续点击 5 次"
    result: "发现重复提交漏洞 — 标注 Blocker"
  - dimension: keyboard_focus
    attempt: "Tab 键跳转 100+ 次"
    result: "焦点追踪正确，无焦点陷阱"
```

### Findings Example

```yaml
findings:
  - finding_id: F-UX-001
    severity: warning
    category: accessibility
    description: "登录表单缺少 aria-label"
    evidence_ref: "E-UX-002"
    remediation: "为每个输入添加 aria-label"
    wcag_criterion: "1.3.1"
  - finding_id: F-UX-002
    severity: blocker
    category: accessibility
    description: "提交按钮不可键盘激活"
    evidence_ref: "E-UX-003"
    remediation: "确保按钮元素可聚焦并可 Enter 激活"
    wcag_criterion: "2.1.1"
```

### Professional Validation Rules

1. `interaction_checks` MUST cover all four states: loading, empty, error, success
2. `design_parameters` MUST be read from UI Designer output (V/M/D knobs)
3. `destructive_tests` MUST contain at least 3 entries
4. `findings` severity MUST be one of: `blocker` (accessibility blocker), `warning`, `advisory`
5. Each finding MUST reference a WCAG criterion if applicable

### Evidence Binding Rules

UX Reviewer conclusions require concrete Evidence:
- Every `executed` interaction check MUST reference specific Evidence IDs
- Every `blocker` accessibility finding MUST reference Evidence of the violation
- "No issues found" MUST list all destructive tests attempted with results

Pure assertions like "UI looks good" without evidence-backed checks are rejected.

---

## Excluded Fields (Core Only)

UX Reviewer extensions CANNOT modify:
- `hypothesis` fields (Reviewer evaluates UX, doesn't define hypotheses)
- `strategy_profile.action_class`
- `atomic_change_set.target_scope` (Reviewer observes, doesn't modify code)
- `risk.level` (Reviewer may recommend elevation for accessibility blockers, but Core makes final determination)
- `verification_plan.validators` (Reviewer provides UX evidence, but validation is Core-managed)
