---
work: 2026-08-10_insight-workflow-full-entities
work_state: active
workflow: complex-bug
stage: reproduce
agent:
  id: tester
  state: active
quality:
  test: pending
  review: not_required
---

# Current Situation

正在修正 Insight 首屏对 Workflow 涉及 Agent / Skill 的截断与混合汇总问题。

## Current Task

复现固定数量上限会隐藏必要 Agent / Skill，并确认 Optional 汇总计数边界。

## Last Result

用户确认所有 Workflow 涉及项必须完整展示，只有 Optional / Catalog 可以折叠。

## Next

建立失败验收后交给 Frontend Dev 实现。

## Blocker

无。
