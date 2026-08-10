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
- `project://docs/STATUS.md` 与当前 `project://docs/WORK.md`
- 相关 Project Fact、Decision 与 Memory Section
- `framework://policies/core.md`、`framework://policies/routing.md`、`framework://policies/review.md`
- `framework://policies/state-contract.md` 与 `framework://tools/state_guard.py`
- 当前 Platform Capability

## Procedure

### 1. Preflight and Resume

先解析三个逻辑定位符；确认 Core、Routing、Documents、Conductor 与四个 Primary Workflow 可读。检查七类 Project Document，缺失时只复制对应官方空模板，不覆盖已有内容。然后读取最小恢复 Context。Active Work 存在时判断新 Request 是必要补全、无关 Backlog，还是可中断的紧急 Bug；禁止同时推进两个 Writer Work。

### 2. Clarify

根据复杂度执行 Mentor Loop。只提会改变 Scope、Acceptance、Business Rule、关键 Experience、不可逆影响或主要 Risk 的问题。需要确认时先展示完整 Intake 摘要。

### 3. Route

按 `framework://policies/routing.md` 的 Primary Workflow 表选择唯一 Workflow，然后按同一文件的 Agent Assignment 选择最小充分 Agent 集合，并指定唯一 Implementation Writer。Routing 只决定“当前需要谁”，不承载方法内容。Bug、Regression、失败修复或半成品修复信号优先于 Scope 很小。

### 4. Activate and Commit

第一次修改任何 Project Artifact 前，由 Conductor 在同一逻辑步骤写入 `project://docs/WORK.md` 和 `project://docs/STATUS.md`：至少包含 Work id、`work_state: active`、Workflow、Stage、当前 Agent、Current Task 与 Verification。规范值只从 `framework://policies/state-contract.md` 声明的动态来源取得；自由 Activity 与 Agent Instance 不得占用 `stage` / `agent.id`。Platform Task / Todo / Plan / Thread / Subagent 状态不能替代这两个文件。

落盘后运行 `python -B <resolved-state-guard-path> check <project-root>`（即 `state_guard.py check`）。只有输出 `STATE_VALID` 才表示校验通过并允许执行；失败时由 Conductor 修正同一次 Commit，校验通过前不得继续 Dispatch。该门同样适用于后续 Agent/Stage 转换、Focused Result、Pause、Resume 与 Distill。

### 5. Load Capability

```text
Selected Agent
→ Agent Contract 的 Skill Assignment
→ 当前动作需要的 Skill
→ Skill Reference Routing 命中的 Reference Section
```

不要因 Agent 拥有多个 Skill 就全部加载；不要让 Conductor 或 Agent 绕过 Skill 读取 References。

### 6. Execute and Verify

- 实现前先定义 Test 或 Manual Verification。
- Bug 先 Reproduce；Refactor 先确认 Baseline；New Behavior 先定义 Acceptance。
- 一次只由一个 Writer 修改目标 Artifact。
- Reviewer 只在 Risk Signal 命中时加载，且不修改被审对象。
- 每次 Dispatch 前由 Conductor 提交 Agent、Stage、Current Task；每个 Specialist 返回 Focused Result 后，先由 Conductor 提交 Latest Result、Verification、Open Findings 和下一状态，再允许下一次 Dispatch。单 LLM 模拟多 Agent也不能省略。

### 7. Close or Continue

未满足 Acceptance 时，基于新 Evidence 形成不同 Strategy；不要机械重复相同 Patch。满足 Completion Checklist 后通过 Memory Skill 沉淀稳定变化，再由 Conductor 将 `project://docs/WORK.md` 与 `project://docs/STATUS.md` 同时清为 no active work。

## Output

- Primary Workflow 与 Routing 理由
- Active Agent / Writer
- Focused Plan 或当前 Next Action
- Verification 与 Evidence
- Risk、Unknown 和需要用户确认的唯一问题
