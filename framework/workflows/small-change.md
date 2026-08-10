---
workflow: small-change
stages: [resume, scope, verify-plan, implement, verify, close]
required_agents:
  - conductor
required_agent_groups:
  - frontend-dev|backend-dev
optional_agents:
  - tester
  - spec-reviewer
  - security-auditor
  - quality-auditor
---

# Workflow：Small Change

```text
恢复相关 Context
→ 确认 Scope 很小
→ 定义 Verification
→ 选择一个 Implementation Agent
→ Conductor 提交 Active Work、Stage、Agent 与 Current Task
→ 修改
→ Focused Check
→ Conductor 提交 Result、Verification 与下一状态
→ Distill 并关闭 Work
```

Scope、Ambiguity 或 Risk 增长时立即升级 Workflow。

> **Writer 语义：** `frontend-dev` 与 `backend-dev` 至少启用一个作为唯一 Implementation Writer，由 Conductor 按任务涉及的代码域选择，不并行修改同一 Workspace。`optional_agents` 仅在 Risk Signal 命中时启用。


## State Commit

每次角色 Dispatch 前和 Focused Result 返回后，必须先回到 Conductor 更新 `project://docs/WORK.md` / `project://docs/STATUS.md`；Stage 或 Agent 的变化只有在该 Commit 落盘并通过 `framework://tools/state_guard.py` 后才成立。单 LLM Persona Switch 也不得跳过。

## Pause / Resume

Pause 是当前 Workflow 的正交状态，不新增 Stage。用户表达“先离开”“挂起工作”或“暂停”时，Conductor 必须先把 Current Task、已完成结果、Verification、Open Findings 和唯一 Next Action 写入 `project://docs/WORK.md`，再保留当前 Workflow 与当前 Stage，将 `project://docs/STATUS.md` 写为 `work_state: paused`、Agent state 设为 `paused`，停止继续派发或执行。用户要求继续时，将状态恢复为 `active`，从同一 Stage 的 Next Action 继续。
