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
required_skills: []
---

# Workflow：Small Change

```text
恢复相关 Context
→ 确认 Scope 很小
→ 定义 Verification
→ 选择一个 Implementation Agent
→ 修改
→ Focused Check
→ 必要时更新 Status
```

Scope、Ambiguity 或 Risk 增长时立即升级 Workflow。

> **Writer 语义：** `frontend-dev` 与 `backend-dev` 至少启用一个作为唯一 Implementation Writer，由 Conductor 按任务涉及的代码域选择，不并行修改同一 Workspace。`optional_agents` 仅在 Risk Signal 命中时启用。
