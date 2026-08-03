---
name: project-lifecycle
description: 从安装后的空 Run、终态历史或中断状态，确定性地启动、继续或继任 Yuan Work。
---

# 项目生命周期

1. 运行固定 Runtime 的 `status`，同时运行 `capability list`。
2. `BLOCKED` 且唯一原因为“没有 Active Work”表示等待 Intake；加载 `requirements-clarification`，再进入 Work Authoring。
3. `CONTINUE` 或 `CORRECT` 时读取 Active Work、Routing Assignment、Attempt、Evidence 与 Handoff，按 Result 选择下一角色和新策略。
4. 用户改变非终态 Work：先解析所有在途/未知副作用，运行 `run supersede`，重新走 Intake → Confirmation → Routing → Work Confirmation → Successor。
5. `WAIT_AUTH`、`BUDGET_EXIT` 或其他可恢复 `BLOCKED` 需要改变 Grant/Budget/前提时，创建绑定前任 Head 的 Successor Work。
6. `COMPLETE` 后的新请求也使用新 Intake 和 Successor，不得修改已完成历史。
7. 状态失败、Integrity Error、未知 Result、能力清单损坏或路由不一致时停止并报告机械原因。
