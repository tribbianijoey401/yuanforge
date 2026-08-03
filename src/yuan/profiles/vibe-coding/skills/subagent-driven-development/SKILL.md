---
name: subagent-driven-development
description: 当平台支持且任务可独立并行时，按角色和依赖拆分多 Agent 工作并保持证据隔离。
---

# 多 Agent 开发

1. 仅拆分边界明确、输入输出稳定、不会写同一文件的任务。
2. 每个子任务携带目标、范围、禁止项、输出和验证要求，不依赖隐式聊天记忆。
3. 实现者与 Reviewer 不使用同一份未验证结论；Reviewer 读取 Artifact 与 Evidence。
4. 角色和 Skill 必须来自 Routing Assignment；子 Agent 结束时返回结构化 `READY/NEEDS_WORK` Handoff 候选。
5. Conductor 记录 Handoff，检查冲突、遗漏和跨模块集成，再运行整体 Verifier。
6. 平台不支持子 Agent 时顺序切换角色并如实记录隔离级别，不伪装成并行或独立执行。
