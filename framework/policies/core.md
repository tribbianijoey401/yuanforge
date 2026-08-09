# Yuan vNext Core Policy

## Product Boundary

Yuan 是运行在 Codex、Hermes 等 Agent Platform 上的 AI Software Engineering Mentor、长期 Project Memory、Context Engineering 与专业协作 Framework。Platform 是 Runtime；Yuan 不建设独立 Runtime、Event Ledger、Action Gateway、Authority Chain 或强制工具拦截。

## Always-on Rules

1. 用户只描述 Outcome、Scope 与 Constraint；Routing 只选择 Workflow 和 Agent，Agent 根据 Contract 选择 Skill，Skill 根据 Signal 选择 References。
2. 一个 Project 默认只有一个 Active Work，无关 Request 进入 Backlog。
3. Work 未完成但需要退出或更新 Framework 时，先保存可恢复 Checkpoint，并将 `STATUS.work_state` 设为 `paused`；暂停不归档、不清空 `WORK.md`，下次 Session 从 Next Action 恢复。
4. 同一时间只有一个 Implementation Writer；其他 Agent 负责分析、Test 或 Review。
5. 修改前先定义 Verification；无法自动化时使用可重复 Manual Acceptance 并说明限制。
6. 只加载当前 Work 相关 Context，禁止预加载全部历史、Agent、Skill 或 References。
7. 用户主要确认 Product Scope、Acceptance Criteria、Business Rule 与关键体验；普通实现细节不重复确认。
8. Status 保持短小；Memory 只保存长期可复用且已验证的知识，不保存 Transcript 或完整 Role Output。
9. Reviewer 根据 Risk 选择，不为角色齐全而调用全部 Reviewer。
10. 未逐项检查 Acceptance Criteria 与 Verification Evidence 前不得报告完成。
11. Markdown 使用中文描述，Agent、Skill、Workflow、Work、Memory、Context、Verification 等名词保留 English。
