---
workflow: complex-bug
stages: [orient, reproduce, diagnose, implement, regression, review, distill]
required_agents:
  - conductor
  - tester
required_agent_groups:
  - frontend-dev|backend-dev
optional_agents:
  - architect
  - spec-reviewer
  - security-auditor
  - quality-auditor
  - ux-reviewer
---

# Workflow：Complex Bug

```text
读取 STATUS.focus、focused Work 与相关 Memory
→ 确认 Observed / Expected Behavior
→ 建立 Failing Test 或可重复 Reproduction
→ 区分 Observation、Hypothesis 与 Verified Fact
→ Conductor 提交 focused Work、Stage、Agent 与 Current Task
→ 一个 Implementation Agent 完成 Root-cause Fix
→ Focused Result 后由 Conductor 提交 Result 与下一状态
→ Focused Test 与 Regression
→ Risk-driven Review
→ User Acceptance
→ Memory Distillation
```

两种实质不同的 Hypothesis 均失败后停止继续 Patch，由 Architect 或未参与当前 Patch 的相关 Dev 在 Independent Context 中重新分析 Failure Model。

紧急 Bug 可以成为一个独立 persisted Work：先 Pause 原 active Work，再创建/激活 Bug Work；Bug 完成后可恢复原 Work。不要把两个 Work 同时设为 active。

> **Writer 语义：** `frontend-dev` 与 `backend-dev` 至少启用一个作为唯一 Implementation Writer，由 Conductor 按 Bug 涉及的代码域选择。重复失败或 Architecture Signal 命中时才启用 `architect`；其余 `optional_agents` 仅在 Risk Signal 命中时启用。

## State Commit

每次角色 Dispatch 前和 Focused Result 返回后，必须先回到 Conductor 更新 focused `project://docs/works/<work-id>.md` 与 `project://docs/STATUS.md`；Stage 或 Agent 的变化只有在该 Commit 落盘并通过 `framework://tools/state_guard.py` 后才成立。

## Pause / Resume

Pause 是当前 Workflow 的正交状态，不新增 Stage。用户表达“先离开”“挂起工作”或“暂停”时，Conductor 必须先把 Current Task、已完成结果、Verification、Open Findings 和唯一 **Next Action** 写入 focused Work，再保留当前 Workflow 与**当前 Stage**，将 Work state 与 `project://docs/STATUS.md` projection 写为 `work_state: paused`、Agent state 设为 `paused`，停止继续派发或执行。用户要求继续时，将状态恢复为 `active`，从同一 Stage 的 Next Action 继续。