# Active Work

## Work ID

2026-08-11_content-driven-interface-design

## Goal

将本次形成的通用 UI 方法沉淀为 Yuan 正式能力，使 UI Designer 先理解系统故事和内容结构，再选择展示架构、视觉语言与生命力方式。

## Scope

- 新增内容驱动的 Interface Design Skill 与按需加载 Reference。
- 更新 UI Designer，使其输出 System Story、Content Model、View Model、Priority、Detail Strategy 与 Liveness。
- 更新 UX Reviewer，使其审查展示架构、视觉疲劳与真实生命力。
- 更新 Frontend Dev，使状态反馈由语义变化驱动并保留用户上下文。
- 调整 query-ux-pro-max 为条件性行业/风格查询，并明确优先级。
- 增加 Framework Contract 与 Skill Validation 测试。

## Non-goals

- 不固定为单一 Dashboard 布局或视觉风格。
- 不把 Liveness 简化为装饰动画数量。

## Acceptance

- [ ] 设计链路明确为 System Story → Content Model → View Model → Visual Language → Liveness → Verification，且每个下游决策可追溯到上游事实。
- [ ] Skill 能根据内容量、关系、任务、变化频率、设备与上下文连续性，为至少四类内容选择有理由的不同 View Model。
- [ ] 清晰骨架、友好层级、细节克制、有目的的生命力不被硬编码为浅色、Dashboard 或品牌模仿。
- [ ] Liveness 只来自真实操作、状态、进度、成功、失败、同步或恢复；减少动效后语义仍完整。
- [ ] UI Designer、UX Reviewer 与 Frontend Dev 使用同一 Product Truth Source，职责明确且方法不重复膨胀。
- [ ] Project Contract / Presentation Architecture / Visual Absolutes / Project Design System 高于 query-ux-pro-max 推荐。
- [ ] 新 Skill 通过 quick_validate，Contract Test 与完整 Regression 通过。
- [ ] 独立 Forward Test 不统一收敛为 Dashboard、单屏或长滚动。

## Assumptions and Risks

- 通用能力应描述决策方法，不固化本次 Dashboard 的具体布局。
- 需要验证 `LIVENESS` 不会退化为装饰动画评分。
- 本 Checkpoint 根据 Insight 的 FULL coverage transition 恢复；原始 Goal、Scope、Task、Result、Finding 与 Learning 均来自已观测事实，Non-goal 与 Acceptance 按这些事实重建。

## Plan

1. Product Analyst 完成可验证 Product Contract。
2. 设计 Skill、Reference 与 Agent Contract 的职责分层。
3. 由唯一 Writer 实现 Framework 资产和测试。
4. 运行 Contract、Skill Validation 与 Regression。
5. 按风险执行 Review 并 Distill。

---

# Active Workspace

## Current Task

UI Designer 设计新 Skill 的最小方法、Reference Routing、输出 Contract 与示例映射；保持品牌无关、主题无关并避免 Agent Contract 膨胀。

## Latest Result

Product Analyst 已完成 Product Contract：设计必须沿 System Story → Content Model → View Model → Visual Language → Liveness → Verification 推进；Liveness 不是 Motion 评分；查询建议不能覆盖正式约束；不需要用户新增决策。

## Open Findings

- 需要确定 Skill / Reference / Agent Contract 的最小职责分层。
- 需要设计 Forward Test，使成功依赖可迁移推理而非泄漏预期答案。

## Work Learnings

- 通用能力不是 Dashboard 布局，而是根据 System Story 与 Content Topology 选择 View Model。
- 目标设计品质为 Bright Skeleton、Clear Hierarchy、Detail Restraint、Purposeful Liveness。

## Next Action

由 UI Designer 产出可交给唯一 Writer 的能力设计。
