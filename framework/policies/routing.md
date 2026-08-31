# Dynamic Routing Policy

Routing 只决定“当前需要谁”。专业方法由 Agent 选择的 Skill 提供，专业知识由 Skill 选择的 References 提供。

## Primary Workflow

| Request Signal | Workflow |
|---|---|
| 文案、格式、注释、局部机械修改，Scope 清楚、Risk 很低，且不修复错误行为 | `framework://workflows/small-change.md` |
| Bug、异常、Regression、间歇失败、已有修复未解决或上次只完成一部分 | `framework://workflows/complex-bug.md` |
| 新增或改变用户可观察 Behavior，可在一个 Work 内确认 | `framework://workflows/new-feature.md` |
| 目标模糊、跨多个 Feature、需要分阶段交付或 Architecture 影响广泛 | `framework://workflows/large-project.md` |

## Agent Assignment

> 权威源：每个 Primary Workflow 文件（`framework://workflows/*.md`）的 frontmatter 只声明 `required_agents / required_agent_groups / optional_agents`。下表是快速参考，供 Conductor 开场恢复与人工浏览；发生冲突时以 Workflow 文件为准。Workflow 和 Routing 不选择 Skill。

### Signal Precedence

Bug、Regression、Failed Attempt、Partial Previous Fix 信号高于“文件少、改动小、先简单处理”等 Scope 信号；命中任一前者时不得选择 Small Change。Small Change 只适用于不改变用户可观察 Behavior、不修复错误行为、没有遗留半成品且可以局部机械验证的修改。

| Workflow | Required Agent | Conditional Agent |
|---|---|---|
| Small Change | Conductor、一个相关 Dev | Tester 或 Reviewer，仅在 Risk 需要时 |
| Complex Bug | Conductor、相关 Dev、Tester | Architect；按风险选择 Spec / Security / Quality / UX Reviewer |
| New Feature | Conductor、Product Analyst、相关 Dev、Tester | 跨模块时 Architect；涉及 UI 时 UI Designer；按风险选择 Reviewer |
| Large Project | Conductor、Product Analyst、Architect、相关 Dev、Tester | UI Designer、Design Reviewer 与按风险选择的 Reviewer |

### Presentation Design Signal

完整 `content-driven-interface-design` 仅在高影响 UI、新产品、重要改版、数据密集界面、关键旅程，或没有可复用设计时触发。此时 UI Designer 负责 Repository Capability Audit、Content / View Model 与 Artifact-local Presentation Contract；UX Reviewer 按同一 Artifact 做 traceability review，Frontend Dev 只消费该 Artifact。普通 UI New Feature 不因 UI 身份自动进入完整设计流程，也不使用 State Guard 作为冻结门禁。

Frontend 与 Backend 同时涉及代码时仍保持一个 Writer，按可验证 Slice 顺序切换，不并行修改同一 Workspace。

## Reviewer Routing

- Scope、Business Rule、Acceptance：Spec Reviewer；
- Architecture Plan 在编码前的高影响缺陷：Design Reviewer；
- Trust Boundary、Permission、Sensitive Data、Dependency：Security Auditor；
- Maintainability、Boundary、Performance、Regression：Quality Auditor；
- User Journey、Accessibility、Critical Experience：UX Reviewer。

## Work Relation

- 属于当前 Acceptance Criteria 的必要补充：纳入 Active Work；
- 与当前 Work 无关：进入 Backlog；
- 紧急 Bug：先保存 Work Checkpoint，再暂停、修复、验证并恢复；
- 用户主动 Pause：不重新 Routing，不新增 Workflow Stage；保存 Checkpoint 后停止派发，Resume 时回到原 Workflow 与 Stage；
- Scope 或 Risk 明显增长：升级 Workflow，并在 Work 中记录原因。

## Dependency Enforcement

Conductor 派发 Agent 时只提供 Work、相关 Context 和 Agent Contract，不选择或指定 Skill。Agent 根据自己的 `Skill Assignment` 和当前任务 Signal 判断需要的 Skill，Skill 再按自身 `Reference Routing` 读取 Reference。任何 Agent Contract 中遗留的直接 Reference 指令均不得执行，必须通过对应 Skill。
