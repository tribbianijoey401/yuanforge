---
workflow: complex-bug
required_agents:
  - conductor
  - frontend-dev
  - backend-dev
  - tester
optional_agents:
  - architect
  - spec-reviewer
  - security-auditor
  - quality-auditor
  - ux-reviewer
required_skills:
  - systematic-debugging
  - test-driven-development
---

# Workflow：Complex Bug

```text
读取 Status、Work 与相关 Memory
→ 用普通语言确认 Observed / Expected Behavior
→ 加载 Systematic Debugging Skill
→ 建立 Failing Test 或可重复 Reproduction
→ 区分 Observation、Hypothesis 与 Verified Fact
→ 一个 Implementation Agent 完成 Root-cause Fix
→ Focused Test 与 Regression
→ Risk-driven Review
→ User Acceptance
→ Memory Distillation
```

两种实质不同的 Hypothesis 均失败后停止继续 Patch，由 Architect 或未参与当前 Patch 的相关 Dev 在 Independent Context 中重新分析 Failure Model。Platform 不支持时使用 Persona Switch 并说明限制。

> **Writer 语义：** `frontend-dev` 与 `backend-dev` 至少启用一个作为唯一 Implementation Writer，由 Conductor 按 Bug 涉及的代码域选择。重复失败或 Architecture Signal 命中时才启用 `architect`；其余 `optional_agents` 仅在 Risk Signal 命中时启用。
