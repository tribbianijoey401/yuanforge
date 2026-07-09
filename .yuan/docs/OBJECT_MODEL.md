# OBJECT_MODEL — 知识对象模型规格书

> 管辖 `docs/object-model.yaml`。定义所有知识对象的类型、字段、状态机。
> **这是 DocsOS 最底层的规格书——所有其他规格书都建立在它之上。**

---

## 一、第一性原理

### 1.1 Agent 需要回答的问题不是"文件在哪"，而是"事实是什么"

```
文件中心 Agent 问:    "auth.md 在哪个目录？"
对象中心 Agent 问:    "Feature(Auth) 的 depends 是什么？ verified_commit 是否过期？"
```

前者需要 grep 全文 → O(n)。后者读 frontmatter → O(1)。

### 1.2 Knowledge 是对象，Markdown 只是序列化

```
真实存在:  Feature(Auth)
持久化方式: knowledge/features/FEAT-AUTH.md  (Markdown 只是一种选择)
可查询属性: frontmatter 字段
```

换 JSON、YAML 或数据库，Feature(Auth) 不变。文件的含义由它的 frontmatter 定义，不由路径定义。

### 1.3 五层结构的设计原点

| 层 | 根本问题 | 为什么不可缺 |
|----|---------|:-----------:|
| Object Model | 存在什么？ | 没有它，Graph/Proposal/Version/索引都没有建立的基础 |
| Knowledge | 什么是真的？ | 没有它，Agent 不知道项目长什么样 |
| Runtime | 现在在做什么？ | 没有它，Agent 不知道当前任务和 Git 状态 |
| Events | 发生了什么？ | 没有它，崩溃恢复和变更追溯都不可能 |
| Graph | 东西之间有什么关系？ | 没有它，依赖查询是 O(n) |

Object Model 是这五层的最底层——它定义了**"存在什么"。**

---

## 二、对象类型总览

| 类型 | ID 格式 | 生命周期 | 来源 | 去向 |
|------|---------|---------|------|------|
| **feature** | FEAT-NNN | knowledge | FEATURE.md（蒸馏） | knowledge/features/ |
| **decision** | ADR-NNN | knowledge | ADR-NNN.md（蒸馏） | knowledge/decisions/ |
| **pitfall** | PIT-NNN | knowledge | BUG-NNN.md 归档判断 | knowledge/pitfalls/ |
| **module** | MOD-NNN | knowledge | ARCHITECTURE.md 模块表 | knowledge/modules/ |

---

## 三、共用字段

所有 Knowledge 对象的 frontmatter 必须包含以下字段：

| 字段 | 类型 | 必填 | 说明 |
|------|------|:---:|------|
| `id` | string | ✅ | 全局唯一。格式 `{TYPE}-{NNN}`。如 `FEAT-AUTH` |
| `object_type` | enum | ✅ | feature / decision / pitfall / module |
| `lifecycle` | enum | ✅ | 固定 `knowledge`（Runtime 和 Event 不走此模型） |
| `owner` | string | ✅ | 负责角色。architect / product-analyst / backend-dev 等 |
| `status` | string | ✅ | 由各类型状态机决定有效值 |
| `summary` | string | ✅ | 一句话摘要。用于索引、Graph 节点标签 |
| `confidence` | enum | ✅ | verified / stale / draft / deprecated |
| `depends` | array | — | 依赖的其他对象 ID。如 `[ADR-003, FEAT-LOGIN]` |
| `parent` | string | — | 父对象 ID（子功能/子模块） |
| `children` | array | — | 子对象 ID 列表 |
| `verified_commit` | string | — | 最后验证时的 git commit hash |
| `updated_by` | string | — | 最后更新者的 Agent 角色 |
| `updated_at` | datetime | — | 最后更新时间（ISO 8601） |

### confidence 字段语义

| 值 | 含义 | Agent 行为 |
|----|------|-----------|
| `verified` | 已通过 verified_commit 检查，与代码一致 | 直接使用 |
| `stale` | HEAD != verified_commit，可能过期 | 发出警告，重新扫描代码后更新 |
| `draft` | 尚未完成（如 Product Analyst 刚创建） | 只读，不据此做决策 |
| `deprecated` | 已废弃，不再有效 | 跳过，查 superseded_by 替代 |

---

## 四、各类型详解

### 4.1 Feature（功能）

**对象语义**：一个用户可感知的功能单元。

| 独有字段 | 类型 | 说明 |
|---------|------|------|
| `acceptance_criteria` | array | 验收标准列表（Product Analyst 产出） |
| `api_endpoints` | array | 涉及的 API 端点 |
| `files` | array | 关键源文件路径 |
| `session` | string | 实现此功能的会话文件夹名 |

**状态机**：
```
draft → designed → implemented → verified → deprecated
              ↑          │           ↑
              └──────────┘           │
              (返工)                 │
                                     │
              (重新验证)              │
```

**转换规则**：
- `draft → designed`：Architect 完成设计，验收标准冻结
- `designed → implemented`：Dev 完成实现，代码已提交
- `designed → draft`：设计被否决，退回需求分析
- `implemented → verified`：审查通过 + 测试通过，verified_commit 已记录
- `implemented → implemented`：返工重做（状态不变，version 递增）
- `verified → deprecated`：功能废弃
- `verified → implemented`：功能重新实现（version 递增）

### 4.2 Decision / ADR（架构决策）

**对象语义**：一个不可逆的技术选择。

| 独有字段 | 类型 | 说明 |
|---------|------|------|
| `date` | date | 决策日期 |
| `supersedes` | string | 取代的旧 ADR ID |
| `superseded_by` | string | 被某个新 ADR 取代 |
| `alternatives` | array | 被拒绝的备选方案 |
| `consequences` | object | 决策后果（positive / negative） |

**状态机**：
```
proposed → accepted → deprecated
                ↓
           superseded (→ superseded_by 指向新 ADR)
```

**转换规则**：
- `proposed → accepted`：决策被采纳
- `accepted → deprecated`：决策不再适用（无特定新决策取代）
- `accepted → superseded`：被新决策取代，必须填 `superseded_by`

### 4.3 Pitfall（已知陷阱）

**对象语义**：一个已被验证会重复出现的问题模式。

| 独有字段 | 类型 | 说明 |
|---------|------|------|
| `severity` | enum | blocker / warning / info |
| `type` | enum | backend / frontend / db / deploy / process / env |
| `cause` | string | 根因（简短） |
| `fix` | string | 修复方法（简短） |
| `session` | string | 发现此坑的会话文件夹名 |

**状态机**：
```
active → resolved → archived
   ↑        │
   └────────┘ (再次触发)
```

**转换规则**：
- `active → resolved`：陷阱已被修复
- `resolved → active`：陷阱再次出现（视为已修复但回归）
- `resolved → archived`：不再相关的历史教训
- `archived → active`：历史教训再次激活

### 4.4 Module（模块）

**对象语义**：系统中的一个逻辑模块/包。对应 ARCHITECTURE.md 中的模块划分表。

| 独有字段 | 类型 | 说明 |
|---------|------|------|
| `language` | string | 主要编程语言 |
| `framework` | string | 使用的框架 |
| `directory` | string | 模块根目录 |
| `features` | array | 此模块包含的 Feature ID 列表 |

**状态机**：
```
active → deprecated
```

---

## 五、Frontmatter 示例

### Feature 实例

```yaml
---
id: FEAT-AUTH
object_type: feature
lifecycle: knowledge
owner: architect
status: verified
summary: "JWT-based authentication with refresh token rotation"
depends: [ADR-003, FEAT-LOGIN]
verified_commit: a1b2c3d4e5f6
confidence: verified
updated_by: architect
updated_at: "2026-07-09T14:30:00Z"
acceptance_criteria:
  - "用户可以用 email + password 注册并获取 JWT"
  - "Token 过期后可使用 refresh token 刷新"
api_endpoints:
  - POST /auth/register
  - POST /auth/login
  - POST /auth/refresh
files:
  - src/auth/handler.py
  - src/auth/service.py
  - tests/auth/test_login.py
session: "20260709-用户认证系统"
---
```

### Decision 实例

```yaml
---
id: ADR-003
object_type: decision
lifecycle: knowledge
owner: architect
status: accepted
date: "2026-07-08"
summary: "Use bcrypt over argon2 for password hashing — team familiarity outweighs marginal security gain"
depends: []
alternatives:
  - "argon2: 更安全但团队无经验，调试成本高"
  - "scrypt: 内存硬，但 Python 生态不成熟"
consequences:
  positive:
    - "团队已有 bcrypt 经验，实现成本低"
    - "Python bcrypt 库成熟稳定"
  negative:
    - "抗 GPU 攻击弱于 argon2"
    - "未来如需升级需迁移库"
verified_commit: a1b2c3d4e5f6
confidence: verified
updated_by: architect
updated_at: "2026-07-08T10:00:00Z"
---
```

### Pitfall 实例

```yaml
---
id: PIT-012
object_type: pitfall
lifecycle: knowledge
owner: backend-dev
status: active
severity: warning
type: db
summary: "N+1 query in user listing — eager loading misconfigured, 100 users = 101 queries"
cause: "ORM lazy loading triggered in list view loop"
fix: "Use joinedload() on the relationship in the query"
session: "20260708-对抗式审查"
verified_commit: d4e5f6g7h8i9
confidence: verified
updated_by: quality-auditor
updated_at: "2026-07-08T15:00:00Z"
---
```

---

## 六、Graph 自动构建规则

Graph 从所有 Knowledge 文件的 frontmatter **完全自动构建**，永不手工维护。

### 节点

```
每个 Knowledge 文件的 id → 节点
节点属性: object_type, status, confidence, summary
```

### 边

| frontmatter 字段 | 生成的边类型 |
|-----------------|-------------|
| `depends` | DEPENDS_ON |
| `parent` + `children` | PARENT_OF / CHILD_OF |
| `supersedes` / `superseded_by` | SUPERSEDES / SUPERSEDED_BY |
| Module 的 `features` | CONTAINS |
| Feature 的 `api_endpoints` | EXPOSES (API) |

### 构建命令（概念性）

```bash
# 扫描所有 knowledge/ 下的 .md 文件
# 解析每个文件的 frontmatter
# 构建 nodes + edges → graph/index.json
```

Graph 是幂等的——任何时间运行，都产出当前 Knowledge 状态的精确图。

---

## 七、扩展规则

### 新增对象类型

1. 在 `docs/object-model.yaml` 的 `object_types` 下定义新类型
2. 定义 `specific_fields`（独有字段）
3. 定义 `status_machine`（状态机 + 有效转换）
4. 在本文档追加类型说明

### 新增字段

**共用字段**：在 `shared_fields` 下追加 → 所有类型自动继承。
**独有字段**：在该类型的 `specific_fields` 下追加 → 只影响该类型。

---

## 八、与其他规格书的关系

| 规格书 | 如何依赖 OBJECT_MODEL |
|--------|---------------------|
| GLOBAL.md | knowledge/ 下每个文件的 frontmatter 必须符合 Object Model |
| SESSION.md | 蒸馏时 Conductor 必须从 Session 产出物填充 frontmatter 字段 |
| TASK_BOARD.md | 不直接依赖——TASK_BOARD 管理 Runtime，不是 Knowledge |
| GRAPH.md（未来） | 完全依赖——Graph 的节点和边从 frontmatter 构建 |

---

## 九、设计铁律

| # | 铁律 | 违反的后果 |
|---|------|-----------|
| Ⅰ | **Knowledge 是对象，Markdown 是序列化** | 回到文件中心思维，索引退化全文搜索 |
| Ⅱ | **Graph 从 frontmatter 自动构建，永不手工维护** | 手工维护的图必定与源数据不同步 |
| Ⅲ | **frontmatter 字段名跨类型一致** | 同名字段在不同类型中含义不同 → 索引混乱 |
| Ⅳ | **Status 由状态机控制，不随意赋值** | 跳过状态机 → 蒸馏产物不可信 |
