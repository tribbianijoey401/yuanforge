---
name: test-driven-development
description: >
  Dev 写代码时加载。触发：Phase 2 执行 Task、Dev subagent 启动、
  用户说「写测试」「TDD」、需要写实现代码。强制 Red→Green→Refactor 循环，
  禁止先写代码后补测试。读写：features/当前（更新修改文件表）、
  CONVENTIONS（代码规范）、bugs/（测试失败时记录 Bug 文档）。
version: 1.0.0
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
