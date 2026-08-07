# Dynamic Routing Policy

Routing 只决定“当前需要谁”。专业方法由 Agent 选择的 Skill 提供，专业知识由 Skill 选择的 References 提供。

## Primary Workflow

| Request Signal | Workflow |
|---|---|
| 文案、格式、注释、局部机械修改，Scope 清楚且 Risk 很低 | `small-change.md` |
| Bug、异常、Regression、间歇失败，或已有修复未解决 | `complex-bug.md` |
| 新增或改变用户可观察 Behavior，可在一个 Work 内确认 | `new-feature.md` |
| 目标模糊、跨多个 Feature、需要分阶段交付或 Architecture 影响广泛 | `large-project.md` |

## Agent Assignment

| Workflow | Required Agent | Conditional Agent |
|---|---|---|
| Small Change | Conductor、一个相关 Dev | Tester 或 Reviewer，仅在 Risk 需要时 |
| Complex Bug | Conductor、相关 Dev、Tester | Architect；按风险选择 Spec / Security / Quality / UX Reviewer |
| New Feature | Conductor、Product Analyst、相关 Dev、Tester | 跨模块时 Architect；涉及 UI 时 UI Designer；按风险选择 Reviewer |
| Large Project | Conductor、Product Analyst、Architect、相关 Dev、Tester | UI Designer、Design Reviewer 与按风险选择的 Reviewer |

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
- Scope 或 Risk 明显增长：升级 Workflow，并在 Work 中记录原因。

## Dependency Enforcement

Conductor 派发 Agent 时只提供 Work、相关 Context 和 Agent Contract。Agent 读取其 `vNext Skill Assignment`，Skill 再按自身 `Reference Routing` 读取 Reference。任何 Agent Contract 中遗留的直接 Reference 指令均不得执行，必须通过对应 Skill。
