# FEAT-NNN: [功能名称]

> **状态:** [规划中 / 开发中 / 已完成 / 已废弃]
> **创建时间:** YYYY-MM-DD
> **完成时间:** YYYY-MM-DD（未完成则不填）
> **负责 Agent:** [Architect / Coder]

---

## 需求描述

[用户要什么？一句话说清]

---

## 设计思路

[整体怎么设计的？关键选择是什么？]

---

## 关联文档

| 关系 | 文档 |
|------|------|
| 📋 Plan | `.yuan/plans/[文件名].md` |
| 📋 决策 | [ADR-xxx 为什么](../decisions/ADR-xxx-xxx.md) |
| 🏗 架构 | [ARCHITECTURE.md 相关模块](../ARCHITECTURE.md#模块-a-名称) |
| 🐛 相关 Bug | [BUG-xxx](../bugs/BUG-xxx-xxx.md) |

---

## 修改的文件

| 文件 | 改动类型 | 说明 |
|------|---------|------|
| `src/xxx/yyy.py` | 新增 | 核心逻辑 |
| `tests/test_xxx.py` | 新增 | 单元测试 |

---

## 接口/数据模型

### API（如有）

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/xxx` | 获取列表 |
| POST | `/api/xxx` | 创建 |

### 数据库变更（如有）

| 表/字段 | 类型 | 说明 |
|---------|------|------|
| `users.email` | VARCHAR | 新增邮箱字段 |

---

## 完成检查

- [ ] Spec Review PASS
- [ ] Quality Review APPROVED
- [ ] 测试全部通过
- [ ] 已合并到 main
- [ ] 文档已更新

---

## 变更日志

| 日期 | 变更 | 操作者 |
|------|------|--------|
| YYYY-MM-DD | 创建文档 | Architect |
| YYYY-MM-DD | 实现完成 | Coder |
