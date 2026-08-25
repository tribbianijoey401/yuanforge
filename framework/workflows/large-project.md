---
workflow: large-project
stages: [discover, clarify, confirm, plan, build, verify, review, distill]
required_agents:
  - conductor
  - product-analyst
  - architect
  - tester
required_agent_groups:
  - frontend-dev|backend-dev
optional_agents:
  - ui-designer
  - design-reviewer
  - spec-reviewer
  - security-auditor
  - quality-auditor
  - ux-reviewer
---

# Workflow：Large Project

```text
Product Analyst 建立 Problem Model
→ 确认真正 Outcome、Problem、Facts、Constraints、Assumptions 与 Reframe
→ 同一 Product Analyst 将已确认方向转成具体 Product Contract
→ Recommend
→ Confirm Product Contract
→ Plan by Slice
→ 涉及 UI 的 Slice 先执行 Repository Capability Audit 与内容/页面边界建模
→ UI Designer 通过 Prototype Convergence 冻结可定位的 Presentation Contract
→ Independent Review 同一 Contract
→ Conductor 提交 Active Work、Stage、Agent 与 Current Task
→ Build
→ 每个 Focused Result 后由 Conductor 提交 Result 与下一状态
→ Verify
→ Review
→ Accept
→ Distill
```

复杂 Work 可以在 `project://docs/WORK.md` 内嵌 Task Board。出现紧急 Bug 时，保存 Goal、Progress、Changed Path、Unfinished Edit、Verification、Git Checkpoint 与 Risk，暂停原 Work；Bug 完成后检查 API、Data、Architecture、Business Rule 与 Dependency Impact，再恢复原 Work。

> **Writer 语义：** `frontend-dev` 与 `backend-dev` 至少启用一个作为唯一 Implementation Writer，由 Conductor 按当前 Slice 涉及的代码域顺序切换，不并行修改同一 Workspace。涉及 UI 时必须先启用 `ui-designer` 冻结 Presentation Contract（`presentation_contract: frozen`），之后才能 dispatch `frontend-dev`；`design-reviewer` 在 Plan 编码前启用；其余 `optional_agents` 仅在 Risk Signal 命中时启用。


## State Commit

每次角色 Dispatch 前和 Focused Result 返回后，必须先回到 Conductor 更新 `project://docs/WORK.md` / `project://docs/STATUS.md`；Stage 或 Agent 的变化只有在该 Commit 落盘并通过 `framework://tools/state_guard.py` 后才成立。单 LLM Persona Switch 也不得跳过。

## Pause / Resume

Pause 是当前 Workflow 的正交状态，不新增 Stage。用户表达“先离开”“挂起工作”或“暂停”时，Conductor 必须先把 Current Task、已完成结果、Verification、Open Findings 和唯一 Next Action 写入 `project://docs/WORK.md`，再保留当前 Workflow 与当前 Stage，将 `project://docs/STATUS.md` 写为 `work_state: paused`、Agent state 设为 `paused`，停止继续派发或执行。用户要求继续时，将状态恢复为 `active`，从同一 Stage 的 Next Action 继续。
