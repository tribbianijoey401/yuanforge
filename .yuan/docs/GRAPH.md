---
name: GRAPH
description: >
  文档格式规格书：知识图谱格式
spec_type: document-format
version: "3.0.0"
---

# GRAPH — 知识图谱规格书

> 管辖 `docs/graph/index.json`。Graph 是 Build Artifact，从 Knowledge frontmatter 自动构建。

---

## 一、设计铁律

> **Graph 永不手工维护。** 手工维护的图必定与源数据不同步。

Graph 是幂等的 Build Artifact——任何时候运行 `build-graph`，都产出当前 Knowledge 状态的精确图。

```
Knowledge files (source)
  │
  ▼ parse frontmatter
Nodes + Edges
  │
  ▼ serialize
graph/index.json
```

---

## 二、目录位置

```
docs/
├── knowledge/          ← Source（frontmatter 驱动）
│   ├── features/
│   ├── decisions/
│   ├── pitfalls/
│   └── modules/
│
├── graph/              ← Build Artifact
│   └── index.json      ← 自动生成，不提交 git（.gitignore）
│
└── scripts/
    └── build-graph.py  ← 构建脚本
```

---

## 三、Graph 结构

### 3.1 整体

```json
{
  "generated_at": "2026-07-09T17:00:00Z",
  "generated_by": "build-graph.py",
  "source": "docs/knowledge/",
  "stats": {
    "total_nodes": 12,
    "total_edges": 18,
    "by_type": {
      "feature": 5,
      "decision": 3,
      "pitfall": 2,
      "module": 2
    }
  },
  "nodes": [
    { ... }
  ],
  "edges": [
    { ... }
  ]
}
```

### 3.2 节点（Node）

```json
{
  "id": "FEAT-AUTH",
  "type": "feature",
  "status": "verified",
  "confidence": "verified",
  "summary": "JWT-based authentication with refresh token rotation",
  "owner": "architect",
  "file": "knowledge/features/FEAT-AUTH.md",
  "depends": ["ADR-003"],
  "verified_commit": "a1b2c3d",
  "updated_at": "2026-07-09T17:00:00Z"
}
```

| 字段 | 来源 | 说明 |
|------|------|------|
| `id` | frontmatter.id | 全局唯一标识 |
| `type` | frontmatter.object_type | feature / decision / pitfall / module |
| `status` | frontmatter.status | 当前状态 |
| `confidence` | frontmatter.confidence | 可信度 |
| `summary` | frontmatter.summary | 节点标签 |
| `owner` | frontmatter.owner | 负责角色 |
| `file` | 文件路径 | 相对 docs/ 的路径 |
| `depends` | frontmatter.depends | 依赖的对象 ID |
| `verified_commit` | frontmatter.verified_commit | 验证 commit |
| `updated_at` | frontmatter.updated_at | 最后更新 |

### 3.3 边（Edge）

```json
{
  "from": "FEAT-AUTH",
  "to": "ADR-003",
  "type": "DEPENDS_ON",
  "label": "depends on"
}
```

**边类型和来源**：

| frontmatter 字段 | 边 type | 方向 |
|-----------------|---------|------|
| `depends` | DEPENDS_ON | from → to（每个依赖一条边） |
| `parent` | PARENT_OF | from（parent）→ to（child） |
| `children` | CHILD_OF | from（child）→ to（parent） |
| `supersedes` | SUPERSEDES | from → to（旧→新） |
| Feature 的 `api_endpoints` | EXPOSES | from（Feature）→ to（endpoint id） |
| Module 的 `features` | CONTAINS | from（Module）→ to（Feature） |

### 3.4 置信度标记

| confidence | Graph 中的表示 |
|:---:|------|
| verified | 正常显示，边为实线 |
| stale | ⚠️ 标记，边为虚线 |
| draft | 🏗️ 标记，边为虚线 |
| deprecated | ❌ 标记，节点灰显 |

---

## 四、构建规则

### 4.1 输入

```
扫描 docs/knowledge/**/*.md
解析每个文件的 YAML frontmatter
忽略非 knowledge/ 目录的文件
忽略 frontmatter 解析失败的文件（warn，不中断）
```

### 4.2 节点构建

```
每个 .md 文件 → 1 个 Node
  id         = frontmatter.id
  type       = frontmatter.object_type
  status     = frontmatter.status
  confidence = frontmatter.confidence
  summary    = frontmatter.summary
  owner      = frontmatter.owner
  file       = 相对路径
  depends    = frontmatter.depends || []
```

### 4.3 边构建

```
depends:
  for each item in depends:
    Edge(from=node.id, to=item, type=DEPENDS_ON)

parent:
  Edge(from=frontmatter.parent, to=node.id, type=PARENT_OF)

children:
  for each child in children:
    Edge(from=node.id, to=child, type=PARENT_OF)

supersedes:
  Edge(from=node.id, to=frontmatter.supersedes, type=SUPERSEDES)

Module.features:
  for each feature in features:
    Edge(from=node.id, to=feature, type=CONTAINS)
```

### 4.4 完整性检查

构建后自动检查：

| 检查 | 不通过的处理 |
|------|-------------|
| depends 引用的 ID 是否存在？ | ⚠️ warn，边保留但标记 missing |
| parent/children 是否双向一致？ | ⚠️ warn，单向边保留 |
| 重复 ID？ | ❌ error，拒绝构建 |

---

## 五、使用方式

### 5.1 手动构建

```bash
python scripts/build-graph.py
# 输出: docs/graph/index.json
```

### 5.2 Agent 查询

```
Agent 问"FEAT-AUTH 依赖什么？"
  → 读 graph/index.json
  → 找 nodes[FEAT-AUTH].depends → [ADR-003, FEAT-LOGIN]
  → 找 edges from FEAT-AUTH → 列出所有 DEPENDS_ON 边
  → 如果有 stale 标记 → 提示验证
```

### 5.3 Conductor 触发

- Workspace Close 蒸馏后 → 自动运行 build-graph
- Phase 4 巡检时 → 运行 build-graph → 检查一致性

---

## 六、生命周期

| 阶段 | 操作 | 执行者 |
|------|------|--------|
| Workspace Close | 蒸馏后自动重建 Graph | Conductor |
| Knowledge 更新 | 更新后重建 Graph | 更新者 |
| Phase 4 巡检 | 重建 Graph + 检查一致性 | Conductor |
| 任何时间 | 手动 `python scripts/build-graph.py` | 任何 Agent |

---

## 七、与 Object Model 的关系

Graph 不定义 Schema——Object Model 定义了 Schema。Graph 只是 Schema 实例的可视化索引。

```
object-model.yaml     → 定义什么对象存在、什么字段、什么关系
knowledge/ files      → 对象实例（frontmatter + 正文）
graph/index.json      → 从实例自动构建的关系图
```

改变 Object Model → frontmatter 跟着变 → Graph 自动反映变化。不需要改 Graph 本身。
