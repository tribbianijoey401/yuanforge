# Yuan 产品说明

## Product Positioning

Yuan 是运行在 Codex、Hermes 等现有 Agent Platform 上的、Markdown 驱动的 AI 软件工程 Mentor、长期 Project Memory 与多角色协作 Framework。

Yuan 不替代 Agent Platform。LLM 负责推理，Platform 负责文件、命令与 Agent 能力，Yuan 负责 Mentor、Memory、Context、Orchestration 和 Quality 方法。

## Target User

第一目标用户是不懂编程或技术能力有限、但希望持续完成软件项目的产品用户。交互应以 Product Goal、User Experience、Business Rule 和 Acceptance Result 为中心，不要求用户理解内部 Agent、Skill、Reference 或技术状态机。

## Primary Value

首要目标只有一个：提高 Vibe Coding 的代码质量。五项核心能力均服务于这个目标：

- `GUIDE`：把模糊想法转为清晰 Scope 和 Acceptance，并主动纠正高风险或不合理需求。
- `MEMORY`：跨 Session 保存稳定事实、Decision、Progress、失败经验和 Pitfall。
- `CONTEXT`：只加载当前 Work 相关的 Project Document、Agent、Skill 和 Reference Section。
- `ORCHESTRATION`：由 Conductor 动态选择必要角色，不默认启动完整专家团。
- `QUALITY`：采用 Verification First，并根据 Risk 决定独立 Review。

## Product Rules

1. 一个 Project 默认只有一个 Active Work；无关新需求进入 `BACKLOG.md`。
2. 紧急 Bug 可以中断，但必须先保存原 Work Checkpoint，修复后再恢复，禁止双写并发。
3. 默认只有一个 Implementation Writer；其他 Agent 负责澄清、设计、验证或独立 Review。
4. 用户主要确认 Scope、Acceptance、Business Rule、关键 Experience 和不可逆 Decision。
5. Yuan 应给出明确推荐及主要 Trade-off，不能把所有技术选择抛给非技术用户。
6. 对外只展示 Focused Summary；内部角色全文不默认暴露，也不默认进入长期 Memory。

## Non-goals

vNext MVP 不建设独立 Runtime、Event Ledger、Action Gateway、Capability Token、Authority Chain、强制工具拦截、完整 Hash 证明链或后台 Daemon；不永久保存全部聊天和推理；不要求每个小改动执行固定完整流水线。

## MVP

首个端到端 MVP 是大型现有 Project 中的 Complex Bug：从模糊描述开始，完成有限澄清、复现、失败验证、根因定位、单 Writer 修复、Regression、风险驱动 Review、用户验收和 Memory 沉淀。
