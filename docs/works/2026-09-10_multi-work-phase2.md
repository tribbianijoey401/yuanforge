---
id: 2026-09-10_multi-work-phase2
state: paused
workflow: large-project
stage: verify
agent:
  id: tester
  instance: phase2-contract-writer
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

- [ ] 单 active Work 没有 execution 字段继续通过。
- [ ] 两个 active Work 只在不同 isolated workspace、不同真实 agent.instance 下通过。
- [ ] 缺 execution、workspace 重复、instance 重复或 persona-degraded 伪并发均被拒绝。
- [ ] STATUS.focus 是 active Work 中当前 interaction 的 projection，不再表示唯一 active Work。
- [ ] Insight 在 non-focused active Work 变化时写入该 Work 自己的 trace。
- [ ] Update 在任何 active Work 存在时被阻止。
- [ ] Framework、Installer、Insight、legacy 及 full regression 全绿。

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

**Agent:** tester (phase2-contract-writer)

**Task:** 保留 Phase 2 implementation checkpoint，等待独立 Review。

**Done conditions:**

- 独立 Review 结论已记录；如有 Finding，以本 Work 的唯一 Next Action 修正。

## Latest Result

完成 Phase 2 vertical slice：Guard contract 已由 Framework 文档约束；Insight 增加 Snapshot.works 与 per-work trace；Installer 扫描任一 canonical active Work。

## Open Findings

- 无阻塞 Finding；尚待用户指定的独立 Review。

## Work Learnings

- Phase 2 仅验证独立 Platform execution identity，不分配 workspace、不调度 execution lane，也不自动集成。

## Next Action

等待独立 Review；若需要修正，先恢复此 Work 并从 review Finding 继续。

## Blocker

无。
