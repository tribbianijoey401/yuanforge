# Workflow: Phase Gates

> **扩展分类**：workflow（可选）
> **禁用影响**：固定 Gate（G1-G4, HG1-HG4）不再自动触发，Conductor 可跳过门禁
> **依赖**：无（自主定义，可引用 workflow-protocol 的 DAG 定义）

---

## 概述

Phase Gates 定义标准五阶段流水线及其间的质量门禁。禁用后 Core Tick 不再检查 Gate 条件，直接推进到 CONTINUE/COMPLETE。

## 阶段总览

```
Discover → Plan → Build → Verify → Promote
   │        │      │       │        │
  HG1     HG2    (G1)    (G2→G3)  (G4)
```

## 门禁定义

| 编号 | 类型 | 触发点 | 条件 | 禁用时行为 |
|------|------|--------|------|-----------|
| HG1 | Human Gate | Discover 结束 | 需求确认（用户故事 + AC） | 跳过，直接进入 Plan |
| HG2 | Human Gate | Plan 结束 | Plan + API 契约 + Dispatch Table 完整 | 跳过，直接进入 Build |
| G1 | Quality Gate | Plan 结束 | Plan 确认，API 契约 freeze | 跳过，直接进入 Build |
| G1.5 | Quality Gate | Design Review 结束 | 架构审查通过，无 Blocker | 跳过，直接进入 Build |
| G2 | Quality Gate | Build 结束 | 四审查官并行完成，无 Blocker | 跳过，直接进入 Verify |
| G3 | Quality Gate | Verify 结束 | 全量测试 PASS，所有 Blocker 已解决 | 跳过，直接进入 Promote |
| G4 | Quality Gate | Promote 结束 | 蒸馏提取完成，Workspace 归档 | 跳过，任务标记 COMPLETE |

## 与 Core 的关系

- Phase Gates 是 Conductor 的执行策略，不是 Core Reducer 的判定条件
- Core Reducer 只依赖 STATE 中的 `status` 和 Evidence 结果
- Gate 检查是 Conductor 的行为约束，可以被策略绕过
- 禁用后：Conductor 直接调度下一个 Ready Task，不检查 Gate 条件

## 与 STATE 的关系

Gate 检查更新 STATE：
```yaml
# Gate 通过时
status: RUNNING
pending_changes: [approved_change_id]
# Gate 不通过时
status: BLOCKED
```

---

## 版本

| 字段 | 值 |
|------|-----|
| schema | yuan.workflow.phase-gates/v1 |
| category | workflow |
| required_in_core | false |
