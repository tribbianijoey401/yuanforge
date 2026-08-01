# Workflow: Role Isolation

> **扩展分类**：workflow（可选）
> **禁用影响**：多角色并行不再自动隔离，共享同一上下文
> **依赖**：无

---

## 概述

Role Isolation 确保每个 Agent 角色在独立上下文中执行，上下文不泄露到其他角色。通过 subagent 或独立进程实现。

## 隔离级别

| 级别 | 实现方式 | 隔离程度 |
|------|---------|---------|
| Tier 1 | `delegate_task` 子 Agent | 完全隔离（独立会话+工作目录） |
| Tier 2 | `terminal(background=true)` | 进程隔离（共享文件系统） |
| Tier 3 | 同一 Agent 角色切换 | 无隔离（共享上下文） |

## 触发条件

当 Conductor 派发多个并行 Task 给不同角色时，Role Isolation 自动激活。

## 规范

- 每个子 Agent 必须有独立的 `context` 字段（不引用其他角色的私有数据）
- 上下文传递只能通过 Conductor 显式声明的 `context_passing` 字段
- Tier 3（角色切换）仅在 Tier 1/2 不可用时降级使用

## 与 Core 的关系

- Role Isolation 是执行策略，不是 Core 完成语义
- Core 不关心 Agent 如何执行，只关心 Proposal 和 Evidence
- 禁用后：所有角色共享同一上下文，效率更高但隔离性降低

## 禁用时的降级行为

- 所有角色在同一会话中执行
- 上下文传递由 Agent 自主管理
- 无强制隔离保证

---

## 版本

| 字段 | 值 |
|------|-----|
| schema | yuan.workflow.role-isolation/v1 |
| category | workflow |
| required_in_core | false |
