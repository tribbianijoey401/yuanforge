---
name: subagent-driven-development
description: 当平台支持且任务可独立并行时，按角色和依赖拆分多 Agent 工作并保持证据隔离。
---

# 多 Agent 开发

1. 仅拆分边界明确、输入输出稳定、不会写同一文件的任务。
2. 每个子任务携带目标、范围、禁止项、输出和验证要求，不依赖隐式聊天记忆。
3. 实现者与 Reviewer 不使用同一份未验证结论；Reviewer 读取 Artifact 与 Evidence。
4. 汇总者检查冲突、遗漏和跨模块集成，再运行整体 Verifier。
5. 平台不支持子 Agent 时顺序切换角色，不伪装成并行或独立执行。
