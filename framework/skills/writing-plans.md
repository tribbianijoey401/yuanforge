---
name: writing-plans
description: Complex Bug、New Feature 或 Large Project 需要可执行 Implementation Plan 时使用；Small Change 通常跳过。
version: 4.0.0
---

# Writing Plans Skill

## vNext Reference Routing

- Requirement / Acceptance 需要自包含 Contract：读取 `framework://references/01-standards/spec-as-contract.md` 的 Self-contained Spec 与 E2E Verification Section。
- 存在未决选择：读取 `framework://references/01-standards/open-decisions-register.md` 的 Trigger、Field 与 Resolve Section。
- Plan 可能注入过多 Context：读取 `framework://references/01-standards/context-engineering.md` 的 JIT 与 Compaction Section。
- 涉及 Module Boundary：读取 `framework://references/01-standards/code-organization.md` 的 Layer 与 Dependency Section。

未命中 Signal 时不读取上述 Reference。

## Inputs

- `project://docs/WORK.md` 的 Goal、Scope、Acceptance、Risk 与 Assumption
- 相关 `ARCHITECTURE.md`、`DECISIONS.md` 和 `MEMORY.md` Section
- 当前 Repository Fact、Test Baseline 与 Change Surface

## Procedure

1. 从 Acceptance 反推可验证的 Behavior Slice，不按角色或文件类型机械分阶段。
2. 每个 Slice 定义 Outcome、Affected Artifact、Dependency、Writer 和 Verification。
3. 优先保持每个 Slice 完成后 Project 可运行、可验证、可回退。
4. 明确 Interface、Data Migration、Compatibility、Security 与 Failure Handling。
5. 未决重大选择写入 Work 的 Assumption / Risk，并给出推荐；确认后再写入 Decisions。
6. 根据 Risk 决定 Reviewer，不把所有 Reviewer 固定写进 Plan。
7. Plan 作为 `work_updates` 返回 Conductor，由 Conductor 写入 `project://docs/WORK.md`；只有 Complex Work 才增加 Optional Task Board。

## Plan Shape

```markdown
## Plan

| Slice | Outcome | Artifact | Dependency | Verification | Reviewer Signal |
|---|---|---|---|---|---|

## Interfaces and Migration

## Risk and Rollback

## Manual Acceptance
```

## Quality

- 每个 Acceptance 至少映射一个 Verification。
- 不使用“完善、优化、处理一下”等无法判定完成的 Task。
- 不创建独立 Plan Truth Source；当前 Plan 始终在 Active Work。
- Scope 很小时直接执行最小 Plan，不为了格式增加流程成本。
