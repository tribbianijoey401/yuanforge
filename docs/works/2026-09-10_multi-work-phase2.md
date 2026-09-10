---
id: 2026-09-10_multi-work-phase2
state: paused
workflow: large-project
stage: verify
agent:
  id: tester
  instance: review-fix-writer
  state: paused
quality:
  test: passed
  review: pending
---

# Active Work

## Goal

将 Multi-Work Phase 2 从 isolation Guard 原型闭合为可验证的 concurrent-work contract、per-work Insight evidence 与 Installer safety behavior。

## Scope

- Phase 2 execution identity contract、state validation、Framework/Skill/Workflow templates。
- Insight Snapshot.works 与 per-work semantic diff, trace and observer routing。
- Installer Update 针对任一 active Work 的 precondition。
- Phase 2 regression tests，同时保留 Phase 1 与 legacy compatibility。

## Non-goals

- 不新增 Scheduler、Worker Pool、自动 worktree/branch、merge queue、mutation overlap runtime、Agent 或 Workflow。
- 不实现平台 workspace 或 independent execution 的分配；只验证 Platform 提供的 identity。

## Acceptance

- [x] 单 active Work 没有 execution 字段继续通过。
- [x] 两个 active Work 只在不同 isolated workspace、不同真实 agent.instance 下通过。
- [x] 缺 execution、workspace 重复、instance 重复或 persona-degraded 伪并发均被拒绝。
- [x] STATUS.focus 是 active Work 中当前 interaction 的 projection，不再表示唯一 active Work。
- [x] Insight 在 non-focused active Work 变化时写入该 Work 自己的 trace，focused consumer 只读取 focused trace。
- [x] Update 在任何 active Work 或 canonical Work state 不可判定时被阻止。
- [x] Framework、Installer、Insight、legacy 及 full regression 全绿。

## Assumptions and Risks

- execution.workspace 与 agent.instance 只接受外部 Platform 已提供的 identity；Framework 不分配或调度它们。
- Insight 保留 Snapshot.work 作为 focused compatibility view，并新增 Snapshot.works。

## Plan

1. 定义 canonical Phase 2 contract 与 Guard behavior，并写 regression tests。
2. 实现 per-work Insight snapshot/diff/trace/observer routing。
3. 对齐 Installer、templates、Framework contracts 与 alpha.15 metadata。
4. 执行 focused / full regression、static checks 与 review。

---

# Active Workspace

## Current Task

**Agent:** tester (review-fix-writer)

**Task:** 保留已验证的 Phase 2 review-fix checkpoint，等待独立 Review。

**Done conditions:**

- 独立 Review 结论已记录；如有 Finding，以本 Work 的唯一 Next Action 修正。

## Latest Result

F-01 至 F-08 已闭合：canonical activation 改为条件 isolation；并发 instance 改为 stable identity；Insight 以 focused trace 消费并按任意 removed Work 生成 summary；Installer canonical state fail-closed。Focused suites green，full discovery 150 tests，static/Guard/Framework checks green。

## Open Findings

- 无。F-01 至 F-08 已修复并有 regression evidence；独立 Review 仍 pending。

## Work Learnings

- Phase 2 仅验证独立 Platform execution identity，不分配 workspace、不调度 execution lane，也不自动集成。

## Next Action

等待独立 Review；若有 Finding，恢复此 Work 并从 Finding 继续。

## Blocker

无。
