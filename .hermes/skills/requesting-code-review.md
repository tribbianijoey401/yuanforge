---
name: requesting-code-review
description: >
  审查代码时加载。触发：Phase 2 的 G2 Gate、Coder 完成 Task 后、
  用户说「审查」「review」「检查代码」、Reviewer Agent 激活。
  执行两阶段审查：Spec Compliance → Code Quality，不通过打回修复。
  读写：features/当前（对照需求）、ARCHITECTURE（对照设计）、
  bugs/（发现问题创建 Bug 文档）、CONVENTIONS（检查规范）。
version: 1.0.0
---

# 代码审查 Skill

> **YuanForge 的两阶段审查执行器。**
> Stage 1 对需求 → Stage 2 对质量，不可跳过或颠倒。

---

## 触发条件

- G2 Gate：Coder 完成一个 Task，Conductor 触发审查
- 用户说「审查」「review」「检查这段代码」
- Reviewer Agent 激活时自动加载

---

## 流程

### Stage 1: Spec Compliance Review

> **问题：实现是否符合 Plan 定义的需求？**

对照 Plan 中当前 Task 的规格，逐项检查：

| 检查项 | 方法 |
|--------|------|
| 功能完整性 | 所有需求是否实现？ |
| 文件路径 | 是否符合 Plan？ |
| 接口签名 | 函数签名是否匹配？ |
| 行为预期 | 行为是否与预期一致？ |
| Scope Creep | 有没有超出范围的改动？ |
| 遗漏 | 有没有遗漏的需求？ |

**输出：`PASS` 或 `REQUEST_CHANGES`（具体差距列表）**

**PASS → 进入 Stage 2**  
**FAIL → 退回 Coder + 差距列表**

### Stage 2: Code Quality Review

> **问题：代码质量是否过关？**（仅在 Stage 1 PASS 后执行）

| 维度 | 检查项 |
|------|--------|
| 代码风格 | 是否符合 CONVENTIONS.md？ |
| 错误处理 | 异常是否被正确处理？ |
| 命名 | 变量/函数/类名是否清晰？ |
| 测试覆盖 | 充分覆盖正常+异常路径？ |
| 安全性 | 是否有注入/XSS/泄露等风险？ |
| 简洁性 | 代码是否简洁可读？ |

**输出：`APPROVED` 或 `REJECT`（具体问题列表）**

### 退回三次规则

同一 Task 连续 3 次不通过 → 触发架构复盘。

---

## 📚 文档读写规则

| 阶段 | 读 | 写 |
|------|-----|-----|
| 审查前 | features/当前, ARCHITECTURE, CONVENTIONS, Plan | - |
| 发现 Bug | - | bugs/BUG-NNN-xxx.md（记录问题） |
| 发现新坑 | - | pitfalls（如是系统级问题） |

---

## 📤 输出模板

```markdown
## 🔍 审查：Task {编号}

### Stage 1: Spec Review
| 检查项 | 预期 | 实际 | 判定 |
|--------|------|------|------|
| {项目} | {Plan 要求} | {实现情况} | ✅/❌ |

**Verdict:** ✅ PASS / ❌ REQUEST_CHANGES

### Stage 2: Quality Review
**Critical:**
- [ ] {问题} — {建议}

**Important:**
- [ ] {问题} — {建议}

**Verdict:** ✅ APPROVED / ❌ REJECT

### 文档更新
- [ ] bugs/BUG-{NNN}-{title}.md — {描述}
```
