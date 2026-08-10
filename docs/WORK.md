# Active Work

## Goal

让 Insight 首屏完整展示当前 Workflow 实际涉及的 Agent 与 Skill，避免把“涉及但超出数量上限”误表示为可选项。

## Scope

- 调整 Agent / Skill 首屏筛选与汇总逻辑。
- 所有 Current、Required、Observed、Missing、Unknown 项完整展示。
- 仅 Optional / Not Required / Catalog 项折叠为可用数量汇总。
- 补充前端回归测试并更新现有远程分支与 PR。

## Non-goals

- 不修改 Insight API、Registry、Workflow 或后端状态推导。
- 不提交当前工作区中的其他 Framework 与后端改动。

## Acceptance

- [ ] 当前 Workflow 涉及的全部 Agent 均可见，不受固定数量上限截断。
- [ ] 当前 Workflow 涉及或已观测的全部 Skill 均可见，不受固定数量上限截断。
- [ ] Optional / Catalog 项只以独立、准确的数量摘要呈现。
- [ ] 相关布局在窄屏无页面级横向溢出。
- [ ] 前端测试、JS 语法检查与差异检查通过。

## Assumptions and Risks

- 涉及项数量可能增多，节点区域允许自然换行和纵向增长，优先保证语义完整。
- 本次改动会更新已推送的 `agent/insight-light-canvas` 分支。

## Plan

1. 复现固定数量截断与混合汇总问题。
2. 添加失败回归测试。
3. 修正筛选、展示和 Optional 汇总逻辑。
4. 运行前端与完整 Regression。
5. 更新远程分支与 PR。

---

# Active Workspace

## Current Task

Tester 复现 Agent 最多 4 个、Skill 最多 3 个造成的必要项截断，并确认当前汇总混入 Optional 项的事实。

## Latest Result

已确认用户期望：省略只能代表当前 Workflow 不涉及；所有涉及项必须完整可见。

## Open Findings

- 当前 `MAX_VISIBLE_AGENTS` / `MAX_VISIBLE_SKILLS` 会截断必要项。
- `hiddenCount` 同时统计必要项溢出与 Optional Catalog，摘要语义不准确。

## Work Learnings

- 首屏语义完整性优先于固定卡片数量；Optional / Catalog 可以折叠，Workflow 涉及项不能静默隐藏。
