---
name: graph-query
title: 图查询语言规范
description: 图查询语言规范，用于查询知识图谱的 DSL 语法
category: graph-query
stage: published
created_at: 2026-07-14T16:15:22Z
last_modified: 2026-07-14T16:15:22Z
author: team-architect
verified_by: []
tags: ["graph", "query", "analysis"]
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

# Graph Query — 知识图谱查询 Skill

> **让知识图谱从"死数据"变成"活索引"。**
> Conductor 派发 Task 前，查询图谱获取 Feature/ADR/Pitfall 的依赖关系。

---

## 触发条件

- Conductor 派发 Task 前（配合 knowledge-injection 使用）
- 需要查询 Feature 之间的依赖关系
- 需要发现间接相关的知识（跨模块的隐含关联）

---

## 执行步骤

### 步骤 1：调用查询脚本

```bash
python3 scripts/query-graph.py --module <tag> --format short
python3 scripts/query-graph.py --feature FEAT-NNN --format detailed
python3 scripts/query-graph.py --pitfall PIT-NNN --format short
```

### 步骤 2：解析输出

**short 格式**（一行摘要，适合注入 context）：
```
FEAT-AUTH → depends: [ADR-003, PIT-005, PIT-007]
FEAT-TABLE → depends: [PIT-007]
```

**detailed 格式**（完整依赖树，适合人工阅读）：
```
FEAT-AUTH
├── depends:
│   ├── ADR-003 (bcrypt vs scrypt 选型)
│   ├── PIT-005 (阿里云 SDK Endpoint 缺失)
│   └── PIT-007 (前端空白页：dataIndex 缺失)
├── related:
│   └── FEAT-USER (用户管理，共享 User 模型)
└── affected-by:
    └── PIT-006 (API 返回 null nodes 导致渲染崩溃)
```

### 步骤 3：注入 context

将图谱结果追加到 knowledge-injection 的 Pitfall 摘要之后：

```markdown
## 相关知识图谱
FEAT-AUTH → depends: [ADR-003, PIT-005, PIT-007]
FEAT-TABLE → depends: [PIT-007]
```

### 步骤 4：（可选）重建图谱

如果知识文件有变更，先重建图谱：

```bash
python3 scripts/build-graph.py --incremental
```

---

## 查询模式

| 模式 | 参数 | 用途 |
|------|------|------|
| 模块查询 | `--module <tag>` | 查询某模块相关的 Feature/ADR/Pitfall |
| Feature 查询 | `--feature <FEAT-NNN>` | 查询某 Feature 的依赖和影响范围 |
| Pitfall 查询 | `--pitfall <PIT-NNN>` | 查询某 Pitfall 影响的模块 |
| 全量查询 | （无参数） | 列出所有知识对象及其依赖 |

---

## 输出格式

| 格式 | 参数 | 用途 |
|------|------|------|
| short | `--format short` | 一行摘要，适合注入 context |
| detailed | `--format detailed` | 完整依赖树，适合人工阅读 |
| json | `--format json` | JSON 格式，适合程序处理 |

---

## Pitfalls

- **图谱是增量构建的** — 使用 `--incremental` 模式，只扫描新增/修改的文件
- **graph/index.json 不提交 git** — 确保 `.gitignore` 中有 `docs/graph/`
- **图谱和 Pitfall grep 互补** — 不要互相替代：
  - Pitfall grep：精确匹配模块标签，速度快
  - 图谱查询：提供 Feature 之间的依赖关系，发现间接关联
- **查询结果要精简** — 注入 context 时用 short 格式，不超过 10 行
