---
name: plan-format
description: Material Change 的可执行 Plan 结构；Small Change 不强制使用完整格式。
version: 4.0.0
---

# Plan Format Policy

Plan 是 `project://docs/WORK.md` 的一部分，不创建独立 Plan Truth Source。

## Required Fields

| Field | Requirement |
|---|---|
| Goal | 一个可观察 Outcome |
| Scope / Non-goal | 明确修改边界和禁止扩张项 |
| Acceptance | 每项可执行或可观察 |
| Slice | 每个 Slice 完成后尽量可运行、可验证 |
| Artifact | 预计修改的 Path / Interface / Data |
| Verification | Test、Command 或 Manual Step |
| Risk | Failure Impact、Migration、Compatibility、Security |
| Reviewer Signal | 为什么需要或不需要 Independent Review |

## Slice Table

```markdown
| Slice | Outcome | Artifact | Dependency | Verification | Writer | Reviewer Signal |
|---|---|---|---|---|---|---|
```

Complex Work 可以按 `framework://policies/extended-docs.md` 在 Work 内增加 Task Board。Task Board 只跟踪执行，不重复 Goal、Acceptance 或 Decision。

## Prohibited

- 无验证的“完成开发、完善功能、优化代码”。
- 默认把所有 Agent 和 Reviewer 写入 Plan。
- 为 Small Change 制造多阶段 Gate。
- 把未确认 Hypothesis 写入 `project://docs/DECISIONS.md`；它只能留在当前 Work 的 Assumption / Risk，确认后才能成为 Decision。
- 通过 Plan 扩大用户未授权 Scope。
