# Skill: Test-Driven Development

> **扩展分类**：skill（可执行）
> **禁用影响**：TDD 流程降级为建议，Dev 可直接写实现
> **依赖**：workflows/tdd-loop.md

---

## 概述

TDD Skill 提供 Red→Green→Refactor 的详细执行指引。当 TDD Workflow 被禁用时，此 Skill 仍可手动调用。

## 触发条件

- TDD Workflow 激活时自动执行
- Dev 手动请求时执行

## 执行步骤

1. **Red**：写测试代码，确认编译/运行失败
2. **Green**：写最少实现代码，使测试通过
3. **Refactor**：清理重复，保持测试通过
4. **Commit**：生成一个独立 Commit（如 atomic-commit 启用）

## 与 Workflow 的关系

- TDD Skill 是 tdd-loop workflow 的具体实现
- 禁用 skill 时，workflow 仍可定义 TDD 纪律（仅指引性）
- 启用 workflow 时，skill 自动加载

## 输出

```yaml
skill_result:
  status: completed
  cycles: 3  # Red-Green-Refactor 循环次数
  tests_passed: 12
  tests_new: 5
  evidence_refs: ["E-TDD-001", "E-TDD-002"]
```

---

## 版本

| 字段 | 值 |
|------|-----|
| schema | yuan.skill.tdd/v1 |
| category | skill |
| workflow_dependency | workflows/tdd-loop.md |
| required_in_core | false |
