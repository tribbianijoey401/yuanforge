---
name: project-lifecycle
description: 从安装后的空 Run、终态历史或中断状态，确定性地启动、继续或继任 Yuan Work。
---

# 项目生命周期

1. 运行固定 Runtime 的 `status`，同时运行 `capability list`。
2. `BLOCKED` 且唯一原因为“没有 Active Work”表示等待 Work Authoring，不是安装故障；加载 `work-authoring` 与 `verifier-authoring`。
3. `CONTINUE` 或 `CORRECT` 时读取 Active Work、Attempt 与 Evidence，按 Result 选择新策略。
4. `WAIT_AUTH`、`BUDGET_EXIT` 或可恢复 `BLOCKED` 需要用户改变 Grant/Budget/前提时，创建绑定前任的 Successor Work。
5. `COMPLETE` 后，新需求同样使用 Successor Work；不得把新需求写入已完成历史。
6. 状态命令失败、Integrity Error、未知 Result 或能力清单损坏时停止并报告机械原因。
