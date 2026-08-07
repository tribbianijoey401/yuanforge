---
name: vibecoding-workflow
description: Yuan vNext 的 Dynamic Workflow Coordination。Conductor 在处理开发、修复、重构或继续 Project 时使用。
version: 4.0.0
---

# Dynamic Workflow Coordination Skill

## vNext Reference Routing

本 Skill 不直接加载 Reference。它只负责选择 Workflow 与 Agent；Requirement、Plan、Implementation、Review、Test 和 Memory Skill 各自决定 Reference Routing。

## Inputs

- 用户 Request
- `docs/STATUS.md` 与当前 `docs/WORK.md`
- 相关 Project Fact、Decision 与 Memory Section
- `policies/core.md`、`policies/routing.md`、`policies/review.md`
- 当前 Platform Capability

## Procedure

### 1. Resume

读取最小恢复 Context。Active Work 存在时判断新 Request 是必要补全、无关 Backlog，还是可中断的紧急 Bug；禁止同时推进两个 Writer Work。

### 2. Clarify

根据复杂度执行 Mentor Loop。只提会改变 Scope、Acceptance、Business Rule、关键 Experience、不可逆影响或主要 Risk 的问题。需要确认时先展示完整 Intake 摘要。

### 3. Route

从以下 Workflow 中选择一个：

- `workflows/small-change.md`
- `workflows/complex-bug.md`
- `workflows/new-feature.md`
- `workflows/large-project.md`

然后按 `policies/routing.md` 选择最小充分 Agent 集合，并指定唯一 Implementation Writer。

### 4. Load Capability

```text
Selected Agent
→ Agent Contract 的 Skill Assignment
→ 当前动作需要的 Skill
→ Skill Reference Routing 命中的 Reference Section
```

不要因 Agent 拥有多个 Skill 就全部加载；不要让 Conductor 或 Agent 绕过 Skill 读取 References。

### 5. Execute and Verify

- 实现前先定义 Test 或 Manual Verification。
- Bug 先 Reproduce；Refactor 先确认 Baseline；New Behavior 先定义 Acceptance。
- 一次只由一个 Writer 修改目标 Artifact。
- Reviewer 只在 Risk Signal 命中时加载，且不修改被审对象。

### 6. Close or Continue

未满足 Acceptance 时，基于新 Evidence 形成不同 Strategy；不要机械重复相同 Patch。满足 Completion Checklist 后更新 Status，并通过 Memory Skill 沉淀稳定变化。

## Output

- Primary Workflow 与 Routing 理由
- Active Agent / Writer
- Focused Plan 或当前 Next Action
- Verification 与 Evidence
- Risk、Unknown 和需要用户确认的唯一问题
