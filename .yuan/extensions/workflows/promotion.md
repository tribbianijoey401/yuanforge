# Workflow: Promotion

> **扩展分类**：workflow（可选）
> **禁用影响**：Knowledge 蒸馏不再自动执行，知识保留在 Workspace
> **依赖**：无

---

## 概述

Promotion 是 Workspace 关闭时的知识蒸馏流程。将 Project 中产生的 Pitfall、Pattern、Knowledge 提取到 Knowledge 库。

## 触发条件

当 Core Reducer 返回 `COMPLETE` 且 Workspace 标记为归档时，Promotion 激活。

## 流程

```
EXTRACT → 从 Workspace 提取有价值的知识
VALIDATE → 验证知识的有效性（可复用、无时效性）
PROPOSE → 提出知识入库提案
MERGE → 合并到 Knowledge 库
```

## 知识类型

| 类型 | 来源 | 示例 |
|------|------|------|
| Pitfall | Bug 修复经验 | `PIT-001: JWT 轮换并发竞态` |
| Pattern | 成功实现模式 | `PAT-001: refresh_token 双 token 轮换` |
| Convention | 项目规范 | `CONV-001: API 错误码统一格式` |
| Architecture | 设计决策 | `ADR-001: 使用短期 JWT + 可轮换 refresh token` |

## 与 Core 的关系

- Promotion 是 Knowledge 管理流程，不是 Core 完成判定
- Core 在 COMPLETE 时已经完成，Promotion 是后置任务
- 禁用后：Workspace 直接归档，Knowledge 不更新

## 禁用时的降级行为

- Workspace 归档但不提取知识
- Knowledge 库保持原样
- 无 ADR/Pitfall 自动更新

---

## 版本

| 字段 | 值 |
|------|-----|
| schema | yuan.workflow.promotion/v1 |
| category | workflow |
| required_in_core | false |
