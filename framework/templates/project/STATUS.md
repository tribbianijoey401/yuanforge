---
work: null
work_state: idle
workflow: null
stage: null
agent:
  id: null
  instance: null
  state: null
presentation_contract: n/a
quality:
  test: pending
  review: pending
---

# Current Situation

## Last Completed

## Next

## Blocker

<!--
更新策略：STATUS 是 Session Recovery Index，覆盖当前值，不追加历史。
只在语义状态变化时更新：Work 激活/完成/暂停、Workflow 或 Stage 变化、
Agent 接管/完成、重要结果确认、Blocker 变化、Test/Review 状态变化。
`work_state` 取值：idle / active / paused；暂停时保留 Work、Workflow、Stage，
并将 Agent state 设为 paused。Agent 完成后、下一 Agent 接管前保留
id + state: completed，不要置 none。
Agent state 取值：idle / active / paused / completed / blocked
`stage` 必须来自当前 Workflow frontmatter；`agent.id` 必须是 Agent Contract
文件名。具体动作只写入 WORK 的 Current Task；Persona/Subagent/Session 标签写入
可选 `agent.instance`，不得污染规范 Stage 与 Agent ID。
`presentation_contract` 取值：n/a（无 UI Work）/ pending（有 UI 未冻结）/
frozen（UI Designer 已冻结 Presentation Contract）。涉及 UI 的 New Feature /
Large Project 在 frontend-dev 进入实现阶段前必须为 frozen。
-->
