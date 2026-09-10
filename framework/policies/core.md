# Yuan vNext Core Policy

## Product Boundary

Yuan 是运行在 Codex、Hermes 等 Agent Platform 上的 AI Software Engineering Mentor、长期 Project Memory、Context Engineering 与专业协作 Framework。Platform 是 Runtime；Yuan 不建设独立 Runtime、Event Ledger、Action Gateway、Authority Chain、Work Scheduler 或强制工具拦截。

## Always-on Rules

1. 用户只描述 Outcome、Scope 与 Constraint；Routing 只选择 Workflow 和 Agent，Agent 根据 Contract 选择 Skill，Skill 根据 Signal 选择 References。
2. 一个 Project 可以持久化多个 Work；`project://docs/works/<work-id>.md` 是单个 Work 的执行隔离边界。Phase 2 中单 active Work 保持兼容；多个 active Work 只在每条 lane 都有唯一 `execution.mode: isolated`、Platform workspace 与真实 `agent.instance`（不是纯 channel label）时成立；否则 Serialize；其它 Work 可以 `ready` / `paused` / `blocked`。
3. `project://docs/STATUS.md` 只保存当前 `focus` 与 focused Work 的短 Recovery Projection。Focus 是当前 interaction，不等于唯一 active Work；Canonical Work State 永远在对应 Work 文件。focused Work completion 后若仍有 active Work，Conductor 必须 handoff focus 并完整投影一个 remaining active Work；没有 active Work 时才允许 `work_state: idle`。
4. 用户表达先离开、挂起或暂停时，先保存当前 focused Work 的可恢复 Checkpoint，并将 Work state 与 STATUS projection 设为 `paused`；暂停不归档、暂停时保留全文、不得归档或清空该 Work，不继续派发。下次 Session 从原 Workflow / Stage 的 Next Action 恢复。
5. 每个 execution.workspace 只有一个 Implementation Writer；Phase 2 不引入 Scheduler、worker pool、后台 daemon、自动 worktree/branch、merge queue 或 mutation-overlap runtime。isolated lane 的 integration 仍串行。
6. 修改前先定义 Verification；无法自动化时使用可重复 Manual Acceptance 并说明限制。
7. 只加载当前 focused Work 相关 Context；需要选择 Work 时最多读取候选 Work 的最小 metadata，不预加载全部历史、Agent、Skill 或 References。
8. 用户主要确认 Product Scope、Acceptance Criteria、Business Rule 与关键体验；普通实现细节不重复确认。
9. Status 保持短小；Memory 只保存长期可复用且已验证的知识，不保存 Transcript 或完整 Role Output。
10. Reviewer 根据 Risk 选择，不为角色齐全而调用全部 Reviewer。
11. 未逐项检查 Acceptance Criteria 与 Verification Evidence 前不得报告完成。
12. Markdown 使用中文描述，Agent、Skill、Workflow、Work、Memory、Context、Verification 等名词保留 English。
13. Conductor 是 `project://docs/works/*.md` 与 `project://docs/STATUS.md` 的**唯一正式 State Writer**；legacy `project://docs/WORK.md` 只在旧 checkpoint 迁移前读取。每次 Dispatch 前提交当前 Agent / Stage / Task，每个 Specialist Focused Result 返回后先由 Conductor 判断并执行 `Conductor commit`，提交 Latest Result、Finding 与下一状态，再允许下一次 Dispatch。
14. Platform 只有一个 LLM、通过 Persona 顺序模拟多 Agent 时，同样必须执行 `Conductor commit → Specialist role → Conductor commit`；角色切换不能绕过状态提交。审查类 Specialist 在 Persona 模拟下只依据可重验证据判定，不得把 Writer 自述 Verification 当作已验证事实。
15. Work 切换不得携带上一 Work 的 Current Task、Open Findings、Work Learnings 或 transient `review_context`；Writer Context 只属于当前 Work 的当前 execution chain。
16. `project://docs/STATUS.md` 不维护仅供 Insight 使用的 revision 或事件序号；观察序号和 Coverage 属于 Insight 自己的数据。
17. 正式状态值、focus projection、legacy compatibility 与组合约束以 `framework://policies/state-contract.md` 为唯一语义契约。每次 Conductor State Commit 后必须通过 `framework://tools/state_guard.py` 的只读检查；校验失败时不得继续 Dispatch。Insight 与 Installer 复用 Guard 结果，不维护第二套词汇，也不自动修复 Project State。
