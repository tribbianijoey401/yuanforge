# Skill: Subagent-Driven Development

> **扩展分类**：skill（可执行）
> **禁用影响**：子 Agent 派发降级为手动调度
> **依赖**：无

---

## 概述

Subagent-Driven Development Skill 定义 Conductor 如何向子 Agent 派发任务。包含 Tier 1/2/3 调度策略和上下文传递规范。

## Tier 调度优先级

| Tier | 实现 | 适用场景 | 禁用后行为 |
|------|------|---------|-----------|
| 1 | `delegate_task` | 独立子 Agent，完全隔离 | 降级到 Tier 2 |
| 2 | `terminal(background=true)` | 后台进程，共享文件系统 | 降级到 Tier 3 |
| 3 | `role-switch` | 同一 Agent 切换角色 | 手动执行 |

## 执行步骤

1. Conductor 读取 Dispatch Table
2. 识别所有 READY Task
3. 按 Tier 优先级选择派发方式
4. 注入角色合约 + 铁律摘要 + 上下文
5. 等待结果
6. 更新状态

## 与 Core 的关系

- 子 Agent 派发是执行策略，不是 Core 完成语义
- Core 不关心 Task 由谁执行，只关心 Evidence
- 禁用后：Conductor 直接执行或手动派发

---

## 版本

| 字段 | 值 |
|------|-----|
| schema | yuan.skill.subagent-dev/v1 |
| category | skill |
| workflow_dependency | workflows/role-isolation.md |
| required_in_core | false |
