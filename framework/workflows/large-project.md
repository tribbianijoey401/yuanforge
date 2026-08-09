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
→ Build
→ Verify
→ Review
→ Accept
→ Distill
```

复杂 Work 可以在 `WORK.md` 内嵌 Task Board。出现紧急 Bug 时，保存 Goal、Progress、Changed Path、Unfinished Edit、Verification、Git Checkpoint 与 Risk，暂停原 Work；Bug 完成后检查 API、Data、Architecture、Business Rule 与 Dependency Impact，再恢复原 Work。

> **Writer 语义：** `frontend-dev` 与 `backend-dev` 至少启用一个作为唯一 Implementation Writer，由 Conductor 按当前 Slice 涉及的代码域顺序切换，不并行修改同一 Workspace。`ui-designer` 在涉及 UI 时启用；`design-reviewer` 在 Plan 编码前启用；其余 `optional_agents` 仅在 Risk Signal 命中时启用。
