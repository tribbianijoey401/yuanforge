---
name: test-driven-development
title: 测试驱动开发规范
description: 测试驱动开发规范，Red-Green-Refactor 流程的详细指引
category: tdd
stage: published
created_at: 2026-07-09T17:47:11Z
last_modified: 2026-07-09T17:47:11Z
author: team-tester
verified_by: ["team-tester"]
tags: ["tdd", "testing", "red-green-refactor"]
priority: medium
metadata:
  read_count: 0
  last_read_by: null
  last_read_at: null
  used_in_conversations: []
  avg_read_duration_s: null
  quality_score: null
  verification_level: basic
---

# TDD Skill

> **YuanForge 的 TDD 纪律执行器。**
> 强制 Red → Green → Refactor，不可跳过。

---

## 触发条件

- Dev subagent 启动（Phase 2 执行 Task）
- 用户说「写测试」「TDD」
- Dev 准备写代码时自动加载

---

## 流程

### Red：写失败的测试

1. 根据 Plan Task 描述写测试代码
2. 运行测试，**确认失败**
3. 记下预期失败原因（功能尚未实现）

```bash
pytest tests/path/test_file.py::test_name -v
# 预期输出：FAILED — {reason}
```

### Green：最小实现

1. 写刚好让测试通过的代码
2. YAGNI：不过度设计
3. 保持简单

```python
# 最小实现，不多写
def function(input):
    return expected_result
```

### Refactor：重构

1. 保持测试通过
2. 消除重复、改善可读性
3. 不改行为

### 验证

```bash
pytest tests/ -q
# 预期：全部 PASS
```

---

## 📚 文档读写规则

| 阶段 | 读 | 写 |
|------|-----|-----|
| 写代码前 | features/当前, CONVENTIONS, pitfalls | - |
| 测试失败 | - | bugs/BUG-NNN-xxx.md（记录现象+复现步骤） |
| 实现完成 | - | features/当前（更新「修改的文件」表） |
| 踩坑时 | - | pitfalls（如果是新坑） |

---

## 强制规则

- ✅ 测试必须**先失败**才算有效
- ✅ 实现必须是最小的
- ✅ 每次提交前全量测试 PASS
- ❌ 禁止先写代码后补测试
- ❌ 禁止写「为了覆盖率而写的无意义测试」
- ❌ 禁止跳过测试直接实现
