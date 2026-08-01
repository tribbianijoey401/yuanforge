# Workflow: TDD Loop

> **扩展分类**：workflow（可选）
> **禁用影响**：TDD 纪律不再强制执行，Dev 可直接写实现代码
> **依赖**：无（自主定义，可引用 INVARIANTS 铁律 Ⅱ）

---

## 概述

TDD Loop 是 Build Phase 内的最小执行循环。当此扩展被禁用时，Dev 可以跳过 Red→Green→Refactor 直接进入实现。

## 触发条件

当 Core Reducer 返回 `CONTINUE` 且当前工作涉及代码变更时，TDD Loop 自动激活。

## 循环结构

```
Red    → 写失败测试（编译/运行失败）
Green  → 写最少代码使测试通过
Refactor → 清理重复，保持测试通过
```

## 闸门

| 步骤 | 条件 | 失败处理 |
|------|------|---------|
| Red | 测试可编译且明确失败 | 不得进入 Green |
| Green | 所有新测试通过 | 不得进入 Refactor |
| Refactor | 所有测试仍通过 | 回到 Green |

## 与 Core 的关系

- TDD Loop 是 `workflows/tdd-loop.md`，不是 Core Invariant
- Core 只要求：Attempt 的 `expected_effect` 必须与 `target_scope` 一致
- TDD 失败不影响 Core 完成判定（Reducer 只看 Evidence result）
- 禁用后：Dev 直接写代码，无 Red/Green/Refactor 强制约束

## 与 Evidence 的关系

TDD 完成后，Tester 生成 Evidence：
```yaml
evidence:
  - id: E-TDD-001
    claim: 所有新测试通过
    result: pass
    bound_work_revision: 3
```

---

## 版本

| 字段 | 值 |
|------|-----|
| schema | yuan.workflow.tdd-loop/v1 |
| category | workflow |
| required_in_core | false |
