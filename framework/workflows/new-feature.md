---
workflow: new-feature
required_agents:
  - conductor
  - product-analyst
  - frontend-dev
  - backend-dev
  - tester
optional_agents:
  - architect
  - ui-designer
  - spec-reviewer
  - security-auditor
  - quality-auditor
  - ux-reviewer
required_skills:
  - grilling
  - test-driven-development
---

# Workflow：New Feature

```text
Mentor 式 Requirement Discovery
→ Product Analyst 使用 Grilling Skill 动态检查关键维度
→ Yuan 给 Recommendation 与 Trade-off
→ 用户确认 Scope 与 Acceptance
→ Architecture / UI 按需设计
→ Verification First
→ 一个 Writer 分 Slice 实现
→ Test 与 Risk-driven Review
→ User Acceptance
→ Knowledge Distillation
```

五维 Requirement 是 Product Analyst 的内部 Coverage Model，不是必须全部询问用户的固定问卷。可以从 Repository 与 Document 得到的事实由 Agent 自行读取。

> **Writer 语义：** `frontend-dev` 与 `backend-dev` 至少启用一个作为唯一 Implementation Writer，由 Conductor 按 Feature 涉及的代码域选择。跨 Module 时才启用 `architect`；涉及 UI 时启用 `ui-designer`；其余 `optional_agents` 仅在 Risk Signal 命中时启用。
