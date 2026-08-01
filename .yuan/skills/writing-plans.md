---
name: writing-plans
title: Plan 工程化写作指南
description: Plan 工程化写作指南，为 Architect 提供的 Plan 编写规范
category: plan-writing
stage: published
created_at: 2026-07-09T15:30:19Z
last_modified: 2026-07-09T15:30:19Z
author: team-architect
verified_by: ["team-architect"]
tags: ["plan", "writing", "api-contract"]
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

# 写 Plan Skill

> **YuanForge 的 Plan 工程化引擎。**
> 将架构设计转化为可执行的 Pipeline-as-Code Plan。

---

## 触发条件

用户说以下任何一句 + 当前处于 Phase 1 架构阶段：

- 「写计划」「做方案」「设计架构」「Plan」
- 「开始规划 XX」「给我一个实现计划」

或：Architect 完成需求分析和架构设计后，自动加载。

---

## 流程

### Step 1: 加载上下文

**必须加载：**
- `docs/ARCHITECTURE.md` — 架构全景
- 当前会话文件夹 — 已有功能文档（避免冲突）
- `knowledge/pitfalls/` — 已知陷阱
- `.yuan/rules/plan-format.md` — Plan 格式规范

### Step 2: 分解 Task

原则：
- 每个 Task 2-5 分钟可完成
- 每个 Task 单文件或紧密关联的 2-3 个文件
- Task 顺序遵循渐进式交付（前一个 Task 做完项目可运行）

### Step 3: 定义 Stage 和 Gate

每个 Stage 出口定义 Gate：
- **G1 (Plan Gate):** Plan 完整 + 用户确认 → 进入 Phase 2
- **G2 (Task Gate):** 每个 Task 后 Spec Review + Quality Review
- **G3 (Integration Gate):** Stage 全部完成，全量测试 PASS

### Step 4: 保存 Plan

路径：`.yuan/plans/YYYY-MM-DD_HHMMSS-feature-name.md`

### Step 5: 更新文档

```
→ 更新 docs/PROGRESS.md：「当前 Plan」指向刚创建的 Plan
→ 在当前会话文件夹中创建 FEATURE.md（如 Architect 尚未创建）
```

---

## 📚 文档读写规则

| 阶段 | 读 | 写 |
|------|-----|-----|
| 上下文加载 | ARCHITECTURE, pitfalls, plan-format 规范 | - |
| Plan 产出后 | - | PROGRESS（当前 Plan） |
| 新 Feature | - | features/NNN-xxx.md（如未创建） |

---

## 📤 输出模板

```markdown
## 📋 Plan：{Feature 名称}

### Stage 1: {名称} — `[G1]`
| Task | 目标 | 文件 | 测试 |
|------|------|------|------|
| 1.1 | {目标} | `src/xxx.py` | `tests/test_xxx.py` |
| 1.2 | {目标} | `src/yyy.py` | `tests/test_yyy.py` |

### Stage 2: {名称} — `[G2]`
| Task | 目标 | 文件 | 测试 |
|------|------|------|------|
| 2.1 | {目标} | - | - |

### Gate 定义
| Gate | 阶段 | 通过条件 |
|------|------|---------|
| G1 | Plan → 执行 | Plan 确认 |
| G2 | 每个 Task | Spec + Quality PASS |
| G3 | Stage → 下一个 | 全量测试 PASS |

### 已知风险（来自 pitfalls）
| 风险 | 来源 | 缓解 |
|------|------|------|
| {风险} | PIT-{NNN} | {措施} |
```
