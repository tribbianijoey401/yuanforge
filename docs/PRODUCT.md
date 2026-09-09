# Yuan 产品说明

## Product Positioning

Yuan 是运行在 Codex、Hermes 等现有 Agent Platform 上的、Markdown 驱动的 AI 软件工程 Mentor、长期 Project Memory 与多角色协作 Framework。

Yuan Insight 是官方但可选的只读 Sidecar，用于观察 Framework Expected Behavior 与 Project Observed Behavior；它不是 Control Plane，不修改 Core State，不参与 Routing。

Yuan 不替代 Agent Platform。LLM 负责推理，Platform 负责文件、命令与 Agent 能力，Yuan 负责 Mentor、Memory、Context、Orchestration 和 Quality 方法。

## Target User

第一目标用户是不懂编程或技术能力有限、但希望持续完成软件项目的产品用户。交互应以 Product Goal、User Experience、Business Rule 和 Acceptance Result 为中心，不要求用户理解内部 Agent、Skill、Reference 或技术状态机。

## Primary Value

首要目标只有一个：提高 Vibe Coding 的代码质量。五项核心能力均服务于这个目标：

- `GUIDE`：通过 `deep-requirement-discovery → grilling` 两段式能力链，先判断真正应该解决的问题，再把确认后的 Product Direction 转成清晰 Scope 和 Acceptance。
- `MEMORY`：跨 Session 保存稳定事实、Decision、Progress、失败经验和 Pitfall。
- `CONTEXT`：只加载当前 focused Work 相关的 Project Document、Agent、Skill 和 Reference Section。
- `ORCHESTRATION`：由 Conductor 动态选择必要角色，不默认启动完整专家团。
- `QUALITY`：采用 Verification First，并根据 Risk 决定独立 Review。

## Product Rules

1. 一个 Project 可以同时持久化多个独立 Work；`project://docs/works/` 是 Work Registry，Work 是执行隔离边界。Phase 1 最多一个 `active` Work，`STATUS.focus` 只表示当前 interaction 正在恢复/操作哪个 Work。
2. 已形成明确 Goal / Scope / Acceptance 的独立需求可以成为 `ready` Work；尚未成形的 Future Idea、Deferred Item 仍进入 `BACKLOG.md`，不为了 Multi-Work 把所有想法实例化。
3. 切换正式执行前，当前 `active` Work 必须完成、Pause 或 Block。紧急 Bug 可以成为独立 Work：保存原 Work Checkpoint → 激活 Bug Work → 完成后恢复原 Work。
4. 用户明确说先离开、挂起或暂停时，任何 Workflow 都必须保存当前 Work 的可恢复 Checkpoint、停止派发，并在用户继续时从原 Stage 的 Next Action 恢复。
5. 默认只有一个 Implementation Writer；Phase 1 Multi-Work 不引入并行 Work Scheduler、Worker Pool、后台 Daemon 或自动 branch/worktree 调度。
6. 用户主要确认 Scope、Acceptance、Business Rule、关键 Experience 和不可逆 Decision。
7. Yuan 应给出明确推荐及主要 Trade-off，不能把所有技术选择抛给非技术用户。
8. 对外只展示 Focused Summary；内部角色全文不默认暴露，也不默认进入长期 Memory。
9. Project、Framework 与 Skill-local 文件必须通过无歧义逻辑定位符引用；用户和 Agent 不需要猜测当前目录或同名文件属于哪一层。
10. Project State 文件缺失是安装/状态不可用，不是 Idle；Framework Update 保留全部 Project-owned Work/Memory，不静默迁移或改写 Work State。

## Non-goals

vNext MVP 不建设独立 Runtime、Event Ledger、Action Gateway、Capability Token、Authority Chain、强制工具拦截、完整 Hash 证明链或后台 Daemon；不永久保存全部聊天和推理；不要求每个小改动执行固定完整流水线；Phase 1 不建设多个 Work 的并发执行调度器。

## MVP

首个端到端 MVP 是大型现有 Project 中的 Complex Bug：从模糊描述开始，完成有限澄清、复现、失败验证、根因定位、单 Writer 修复、Regression、风险驱动 Review、用户验收和 Memory 沉淀。Multi-Work 在此基础上提供多个独立 Work 的持久化、切换与恢复，而不改变“单执行通道收敛”的核心纪律。
