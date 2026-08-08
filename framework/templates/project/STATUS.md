---
work: null
work_state: idle
workflow: null
stage: null
agent:
  id: null
  state: null
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
Agent 完成后、下一 Agent 接管前保留 id + state: completed，不要置 none。
State 取值：idle / clarifying / designing / implementing / verifying / blocked
-->
