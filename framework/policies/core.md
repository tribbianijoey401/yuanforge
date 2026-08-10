# Yuan vNext Core Policy

## Product Boundary

Yuan 是运行在 Codex、Hermes 等 Agent Platform 上的 AI Software Engineering Mentor、长期 Project Memory、Context Engineering 与专业协作 Framework。Platform 是 Runtime；Yuan 不建设独立 Runtime、Event Ledger、Action Gateway、Authority Chain 或强制工具拦截。

## Always-on Rules

1. 用户只描述 Outcome、Scope 与 Constraint；Routing 只选择 Workflow 和 Agent，Agent 根据 Contract 选择 Skill，Skill 根据 Signal 选择 References。
2. 一个 Project 默认只有一个 Active Work，无关 Request 进入 Backlog。
3. 用户表达先离开、挂起或暂停，或 Work 未完成但需要更新 Framework 时，先保存可恢复 Checkpoint，并将 `project://docs/STATUS.md` 的 `work_state` 设为 `paused`；暂停不归档、不清空 `project://docs/WORK.md`、不继续派发，下次 Session 从原 Workflow / Stage 的 Next Action 恢复。
4. 同一时间只有一个 Implementation Writer；其他 Agent 负责分析、Test 或 Review。
5. 修改前先定义 Verification；无法自动化时使用可重复 Manual Acceptance 并说明限制。
6. 只加载当前 Work 相关 Context，禁止预加载全部历史、Agent、Skill 或 References。
7. 用户主要确认 Product Scope、Acceptance Criteria、Business Rule 与关键体验；普通实现细节不重复确认。
8. Status 保持短小；Memory 只保存长期可复用且已验证的知识，不保存 Transcript 或完整 Role Output。
9. Reviewer 根据 Risk 选择，不为角色齐全而调用全部 Reviewer。
10. 未逐项检查 Acceptance Criteria 与 Verification Evidence 前不得报告完成。
11. Markdown 使用中文描述，Agent、Skill、Workflow、Work、Memory、Context、Verification 等名词保留 English。
12. Conductor 是 `project://docs/WORK.md` 与 `project://docs/STATUS.md` 的唯一正式 State Writer。每次 Dispatch 前提交当前 Agent / Stage / Task，每个 Specialist Focused Result 返回后先由 Conductor 判断并提交 Latest Result、Finding 与下一状态，再允许下一次 Dispatch。
13. Platform 只有一个 LLM、通过 Persona 顺序模拟多 Agent 时，同样必须执行 `Conductor commit → Specialist role → Conductor commit`；角色切换不能绕过状态提交。
14. `project://docs/STATUS.md` 只保存 Yuan 恢复所需的当前状态，不维护仅供 Insight 使用的 revision 或事件序号；观察序号和 Coverage 属于 Insight 自己的数据。
