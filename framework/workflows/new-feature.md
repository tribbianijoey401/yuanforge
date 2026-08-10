---
workflow: new-feature
stages: [discover, clarify, confirm, design, implement, verify, review, distill]
required_agents:
  - conductor
  - product-analyst
  - tester
required_agent_groups:
  - frontend-dev|backend-dev
optional_agents:
  - architect
  - ui-designer
  - spec-reviewer
  - security-auditor
  - quality-auditor
  - ux-reviewer
---

# Workflow：New Feature

```text
Mentor 式 Requirement Discovery
→ Product Analyst 判断用户提出的是 Goal、Problem 还是 Current Solution
→ 必要时确认真正 Outcome、关键 Evidence 与 Product Direction
→ 在已确认方向上补齐具体、可验证的 Product Contract
→ Yuan 给 Recommendation 与 Trade-off
→ 用户确认 Scope 与 Acceptance
→ Architecture / UI 按需设计
→ Verification First
→ Conductor 提交 Active Work、Stage、Agent 与 Current Task
→ 一个 Writer 分 Slice 实现
→ 每个 Focused Result 后由 Conductor 提交 Result 与下一状态
→ Test 与 Risk-driven Review
→ User Acceptance
→ Knowledge Distillation
```

五维 Requirement 是 Product Analyst 的内部 Coverage Model，不是必须全部询问用户的固定问卷。可以从 Repository 与 Document 得到的事实由 Agent 自行读取。

> **Writer 语义：** `frontend-dev` 与 `backend-dev` 至少启用一个作为唯一 Implementation Writer，由 Conductor 按 Feature 涉及的代码域选择。跨 Module 时才启用 `architect`；涉及 UI 时启用 `ui-designer`；其余 `optional_agents` 仅在 Risk Signal 命中时启用。


## State Commit

每次角色 Dispatch 前和 Focused Result 返回后，必须先回到 Conductor 更新 `project://docs/WORK.md` / `project://docs/STATUS.md`；Stage 或 Agent 的变化只有在该 Commit 落盘后才成立。单 LLM Persona Switch 也不得跳过。

## Pause / Resume

Pause 是当前 Workflow 的正交状态，不新增 Stage。用户表达“先离开”“挂起工作”或“暂停”时，Conductor 必须先把 Current Task、已完成结果、Verification、Open Findings 和唯一 Next Action 写入 `project://docs/WORK.md`，再保留当前 Workflow 与当前 Stage，将 `project://docs/STATUS.md` 写为 `work_state: paused`、Agent state 设为 `paused`，停止继续派发或执行。用户要求继续时，将状态恢复为 `active`，从同一 Stage 的 Next Action 继续。
