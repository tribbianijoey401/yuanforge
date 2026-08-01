# Policy: Per-Task Commit

> **扩展分类**：policy（可选）
> **禁用影响**：提交粒度放宽为每 Feature 一级，不再强制每 Task 一个 Commit
> **依赖**：INVARIANTS（铁律 Ⅳ 原子提交原则）

---

## 概述

Per-Task Commit 要求每次代码变更必须对应一个独立的 Git Commit，Commit message 包含 Task ID。

## 规范

| 要求 | 说明 |
|------|------|
| 粒度 | 每 Task 一个独立 Commit |
| Message 格式 | `[T-NN] <task_id>: <summary>` |
| 范围 | 只包含当前 Task 相关变更 |
| 不允许 | 跨 Task 合并提交 |

## 与 Core 的关系

- Per-Task Commit 是工程纪律，不是 Core 完成语义
- Core 只关心 Evidence 的 result 和 work_revision 的递增
- 禁用后：允许合并提交，不影响 Core 的 COMPLETE 判定

## 禁用时的降级行为

- 允许 Feature 级合并提交
- Commit message 格式放宽
- 不强制 Task ID 出现在 message 中

---

## 版本

| 字段 | 值 |
|------|-----|
| schema | yuan.policy.per-task-commit/v1 |
| category | policy |
| depends_on | INVARIANTS.IV |
| required_in_core | false |
