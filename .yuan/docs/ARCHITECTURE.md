---
name: ARCHITECTURE
title: 框架架构概览
description: 框架架构概览，提供 YuanForge 系统架构的整体视图
category: architecture-overview
stage: published
created_at: 2026-07-21T10:37:27Z
last_modified: 2026-07-21T10:37:27Z
author: framework-team
verified_by: []
tags: ["architecture", "overview", "design"]
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

# ARCHITECTURE — 架构文档规格书

> 管辖 docs/ARCHITECTURE.md。系统的设计蓝图。

---

## 目的

记录系统架构，Agent 首次接手时必读。保持「宏观理解一页看完」。

---

## 格式

```markdown
# 架构文档

> 最后更新: YYYY-MM-DD

## 项目概述
[一句话描述]

## 技术栈
| 层 | 技术 | 选型原因 | 关联 ADR |
|----|------|---------|---------|
| 语言 | [xxx] | [原因] | ADR-001 |
| 框架 | [xxx] | [原因] | ADR-002 |
| 数据库 | [xxx] | [原因] | ADR-003 |

## 系统架构
```
[架构图：ASCII 或文字描述]
```

## 模块划分
| 模块 | 职责 | 关键文件 | 关联会话 |
|------|------|---------|---------|
| [模块 A] | [职责] | `src/xxx/` | [YYYYMMDD-描述] |

## 数据流
```
[请求] → [路由] → [服务层] → [数据层] → [响应]
```

## 目录结构
```
项目根/
├── src/      # 源码
├── tests/    # 测试
└── docs/     # 文档
```
```

---

## 生命周期

| 阶段 | 操作 | 执行者 |
|------|------|--------|
| Phase 1 | 创建，填技术栈 + 模块划分 | Architect |
| 架构变更时 | 更新对应模块 | Architect |
| Phase 3 | 检查是否与代码一致 | Doc Engineer |

---

## 维护规则

- 每次架构变更必须更新，不留过期内容
- 新增模块 → 追加工模块划分表
- 新增技术 → 追加工技术栈表 + 创建 ADR
