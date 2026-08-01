# Workflow: Atomic Commit

> **扩展分类**：workflow（可选）
> **禁用影响**：每 Task 一个 Commit 不再强制，可合并提交
> **依赖**：无

---

## 概述

Atomic Commit 要求每个 Task 完成后生成一个独立 Commit，Commit message 必须包含 Task ID 和变更摘要。

## 触发条件

当 Dev 完成一个 Task 的代码变更时，Atomic Commit 自动激活。

## 规范

| 要求 | 说明 |
|------|------|
| 粒度 | 每 Task 一个 Commit |
| Message 格式 | `[T-NN] <task_id>: <summary>` |
| 内容 | 只包含当前 Task 相关变更 |
| 不允许 | 跨 Task 合并提交 |

## 示例

```
[T-03] AUTH-05: 添加 JWT refresh token 轮换逻辑
[T-04] AUTH-06: 更新登录接口返回结构以支持双 token
```

## 与 Core 的关系

- Atomic Commit 是工程纪律，不是 Core 完成语义
- Core 只关心 Attempt 的 `result` 和 Evidence
- 禁用后：允许合并提交，但不影响 Core 的 COMPLETE 判定
- Commit 历史用于审计，Core 不依赖它做完成判定

## 禁用时的降级行为

- 允许 Feature 级合并提交
- Commit message 格式放宽为 `<summary>`
- 不强制 Task ID 出现在 message 中

---

## 版本

| 字段 | 值 |
|------|-----|
| schema | yuan.workflow.atomic-commit/v1 |
| category | workflow |
| required_in_core | false |
