---
name: systematic-debugging
description: >
遇到 Bug 或异常时加载。触发：测试失败、用户报 Bug、Agent 遇到错误、
Tester 发现回归、Reviewer 发现代码问题需要追根因。
4 阶段系统调试法：复现→定位→根因→修复。核心价值是追溯 Bug 到
对应的 Feature 文档和 ADR 决策，理解原始设计意图后再修复。
读写：bugs/（创建/补充 Bug 文档）、features/关联（追溯到引入的 Feature）、
pitfalls（新坑记录）、ARCHITECTURE（理解系统结构）。
version: 1.0.0
---

# 系统调试 Skill

> **YuanForge 的系统调试引擎。**
> 4 阶段调试法，核心是**追溯 Bug 到原始文档**。

---

## 触发条件

- 测试失败（Tester / Dev 发现）
- 用户说「有个 Bug」「报错了」「修一下」
- Agent 执行中遇到异常
- Reviewer 发现需要根因分析的问题

---

## 流程：4 阶段调试法

### Phase 1: 复现

1. 读取错误信息/日志
2. 确认复现步骤
3. 最小化复现（最小输入触发 Bug）
4. **创建** 当前会话文件夹中的 BUG-NNN-title.md，填写「现象」

### Phase 2: 定位

1. 读 当前会话文件夹中找到关联 Feature 文档
2. 读 Feature 文档中的「修改文件」表 → 定位可疑代码
3. 读 `knowledge/pitfalls/` → 确认非已知坑
4. 读 当前会话文件夹中的 ADR → 理解相关设计决策
5. 更新 Bug 文档的「关联文档」部分

### Phase 3: 根因

1. 确定深层原因（不是表象，是为什么设计/实现有缺陷）
2. 判断是否有对应的 ADR 导致（设计缺陷 → 反馈到 decisions/）
3. 更新 Bug 文档：根因 + 归档判断

### Phase 4: 修复

1. 写修复方案（最小改动）
2. 写回归测试
3. 更新 Bug 文档：「修复」+「教训」
4. 如果新坑 → 追加 `knowledge/pitfalls/`

---

## 📚 文档读写规则

| 阶段 | 读 | 写 |
|------|-----|-----|
| 复现 | 错误日志 | bugs/BUG-NNN.md（创建+现象） |
| 定位 | features/关联, pitfalls, decisions/关联, ARCHITECTURE | bugs/（关联文档链接） |
| 根因 | - | bugs/（根因分析）, pitfalls（新坑） |
| 修复 | CONVENTIONS | bugs/（修复方案+教训） |

---

## 📤 Bug 文档关联模板

Bug 文档中的「关联文档」表，调试时必须填满：

```markdown
## 关联文档

| 关系 | 文档 |
|------|------|
| 📦 引入此 Bug 的 Feature | [FEAT-003 支付模块](../features/003-payment.md) |
| 📋 相关决策 | [ADR-002 选择 Stripe](../decisions/ADR-002-stripe.md) |
| ⚠️ 相关踩坑 | [pitfalls.md § PIT-005 回调超时](../pitfalls.md) |
| 📝 修复 Commit | `abc1234` |
```

## 关键规则

- **先读文档，再修代码** — 不理解原始设计意图的修复 = 引入新 Bug
- **每个 Bug 必关联 Feature** — Bug 不是孤立的，是某次功能引入的
- **修复后必写教训** — 否则下次同样的人（同样的 Agent）还会再踩
- **新坑必记 pitfalls** — 系统级问题、环境限制立即记录
