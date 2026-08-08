# Active Work

## Goal

按 `yuan-insight.plan` 完成 Phase 1：Yuan Core 语义增强（WORK/STATUS/Focused Result/Conductor/verdict），使 Work State、Agent Handoff、Focused Result、Context、Skill、Finding、Distillation 成为清晰的工程语义；为 Yuan Insight 提供只读可观察的事实基础。原则：Yuan First, Insight Follows——每个字段必须通过"删除 Insight 后仍改善 Yuan"测试。

## Scope

- [x] Workflow 结构化（required/optional_agents + required_skills frontmatter）— 已完成
- [x] STATUS.md Recovery Index + stable frontmatter — 已完成
- [x] WORK Contract + Active Workspace 四段（Current Task / Latest Result / Open Findings / Work Learnings）— 已完成
- [x] Manager Model / Conductor state ownership 显式化 — 已完成
- [x] Handoff minimal contract（Task + Goal + Done + Constraints + Context Refs）— 已完成
- [x] Focused Result contract（outcome 四态 + skills_applied）— 已完成
- [x] verdict-protocol Finding Category 七分类 — 已完成
- [x] Skill Assignment 统一 required/recommended/available 三档 — 已完成
- [x] test_contracts 静态规则同步 — 已完成（Phase 1 完成）
- [x] Phase 2 Insight Headless Collector（yuan-observe + watcher + diff + JSONL）— 已完成
- [x] Phase 3 Expected vs Observed Engine（registry + Missing + Why）— 已完成
- [ ] Phase 4 First Signals（Missing Agent/Skill、Repeated Review、Bug Recurrence、Memory）— 进行中
- [ ] Phase 5 Dashboard MVP（Execution Map + Agent/Skill Matrix + Signals + Why）
- [ ] Phase 6 History（Work history + Summary + Trace retention）

## Non-goals

- 不实现 Insight（Phase 2+）
- 不为 UI 给 Core 增加无工程价值字段
- 不重新建立 Event Ledger / Action Gateway / Checkpoint Runtime
- 不为了 Insight 重构 Workflow schema——只优化对 Yuan 自身流程有价值的语义

## Acceptance

- [ ] 每个新字段通过"删除 Insight 后仍改善 Yuan"测试
- [ ] 删除 `.yuan/insight` 不影响 Yuan 任何流程
- [ ] installer check PASS、全部测试 PASS
- [ ] 项目层 docs/WORK.md 与 docs/STATUS.md 使用新格式

## Assumptions and Risks

- 风险：为 Insight 反向加字段 → 用 Yuan-First 测试拦截
- 风险：STATUS 膨胀成万能状态文件 → 硬约束不放 Skill/Context/Memory/Trace

## Plan

1. Workflow frontmatter 结构化 ✅
2. STATUS Recovery Index + frontmatter ✅
3. WORK Active Workspace 四段
4. Conductor Manager Model / State Owner
5. Focused Result contract（focused-output.md）
6. verdict Finding Category
7. Skill Assignment 三档标注
8. test_contracts 同步 + 全量验证

---

# Active Workspace

> Active Workspace 是 State，不是 History。Current Task 与 Latest Result 每次覆盖；Open Findings 只保存未解决义务；Work Learnings 只保存后续仍需的当前认知。完成时 Distill 后全部清空，回到 no active work。

## Current Task

实现 WORK.md 模板的 Active Workspace 四段结构，并同步项目层 docs/WORK.md 为当前 Phase 1 Work。Agent：Conductor（当前会话）。Done Conditions：模板四段齐全 + 项目层 WORK.md 更新 + test_contracts 通过。

## Latest Result

- Outcome: partial
- Summary: Workflow 结构化与 STATUS frontmatter 已完成并提交（c72638a + STATUS 模板更新）；WORK 模板 Active Workspace 四段已落盘
- skills_applied: N/A（本会话为框架实施）
- Verification: installer check PASS，8/8 测试 PASS
- Risks: 项目层 docs/WORK.md 覆盖旧 vNext Migration 记录——其成果已体现于仓库状态，无信息损失
- Next: 完成 WORK 模板后，转向 conductor.md Manager Model 显式化

## Open Findings

- 无

## Work Learnings

- Yuan-First 测试："删除 Insight 后这个字段是否仍改善 Yuan"是 Core 字段的唯一准入标准
- STATUS 是 Session Recovery Index（覆盖不追加），不是状态历史；WORK 是 Active Work Authority
- frontmatter 列表解析需同时支持内联 `[a, b]` 与展开 `- item` 两种 YAML 形式
