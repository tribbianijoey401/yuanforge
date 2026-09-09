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
→ Product Analyst 判断 Goal / Problem / Current Solution
→ 必要时确认 Outcome、Evidence 与 Product Direction
→ 补齐可验证 Product Contract
→ 用户确认 Scope 与 Acceptance
→ 命中 Presentation Design Signal 时执行 Repository Capability Audit、内容/页面边界建模与 Prototype Convergence
→ UI Designer 将 Presentation Contract 作为 `project://docs/design/` 中的 Quality Artifact
→ Architecture / UI 按需设计
→ Verification First
→ Conductor 提交 focused Work、Stage、Agent 与 Current Task
→ 一个 Writer 分 Slice 实现
→ 每个 Focused Result 后由 Conductor 提交 Result 与下一状态
→ Test 与 Risk-driven Review
→ User Acceptance
→ Knowledge Distillation
```

五维 Requirement 是 Product Analyst 的内部 Coverage Model，不是固定问卷。

独立 Feature 可以拥有自己的 `project://docs/works/<work-id>.md`。如果另一个 Work 正在 active，当前 Feature 可先作为 `ready` persisted Work；正式执行前先 Pause / Block / Complete 原 active Work。

> **Writer 语义：** `frontend-dev` 与 `backend-dev` 至少启用一个作为唯一 Implementation Writer，由 Conductor 按 Feature 涉及的代码域选择。跨 Module 时才启用 `architect`；命中 Presentation Design Signal 时启用 `ui-designer`；其余 `optional_agents` 仅在 Risk Signal 命中时启用。

## State Commit

每次角色 Dispatch 前和 Focused Result 返回后，必须先回到 Conductor 更新 focused `project://docs/works/<work-id>.md` 与 `project://docs/STATUS.md`；Stage 或 Agent 的变化只有在该 Commit 落盘并通过 `framework://tools/state_guard.py` 后才成立。

## Pause / Resume

Pause 是当前 Workflow 的正交状态，不新增 Stage。用户表达“先离开”“挂起工作”或“暂停”时，Conductor 必须先把 Current Task、已完成结果、Verification、Open Findings 和唯一 **Next Action** 写入 focused Work，再保留当前 Workflow 与**当前 Stage**，将 Work state 与 `project://docs/STATUS.md` projection 写为 `work_state: paused`、Agent state 设为 `paused`，停止继续派发或执行。用户要求继续时，将状态恢复为 `active`，从同一 Stage 的 Next Action 继续。