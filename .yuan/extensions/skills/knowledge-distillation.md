# Skill: Knowledge Distillation

> **扩展分类**：skill（可执行）
> **禁用影响**：知识蒸馏不再自动执行
> **依赖**：workflows/promotion.md

---

## 概述

Knowledge Distillation Skill 在 Workspace 关闭时自动提取 Pitfall、Pattern、Convention 和 ADR 到 Knowledge 库。

## 执行步骤

1. **EXTRACT**：扫描 Workspace 中的 BUG 记录、决策日志、重复模式
2. **VALIDATE**：验证知识的有效性（可复用、无时效性）
3. **PROPOSE**：生成知识入库提案
4. **MERGE**：合并到 Knowledge 库（`docs/knowledge/`）

## 知识格式

```markdown
---
id: PIT-001
type: pitfall
created_at: 2026-08-01
source_workspace: auth-feature
---

# JWT 刷新令牌轮换并发竞态

> **触发条件**：同一用户从两个设备同时刷新 token
> **现象**：refresh token 轮换未处理并发场景
> **解决方案**：使用乐观锁或版本戳
> **相关 ADR**：ADR-001
```

## 与 Core 的关系

- 知识蒸馏是 Workspace 关闭后的后置任务
- 不影响 Core 的 COMPLETE 判定
- 禁用后：Workspace 直接归档，Knowledge 不更新

---

## 版本

| 字段 | 值 |
|------|-----|
| schema | yuan.skill.knowledge-distillation/v1 |
| category | skill |
| workflow_dependency | workflows/promotion.md |
| required_in_core | false |
