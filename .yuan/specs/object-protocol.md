# Object Protocol — 对象协议

> **依赖**: 无（意图层起点）

> **协议定位**：定义 YuanForge 系统中所有的对象类型。
> 这是 5 份协议中最底层的一份——所有其他协议都建立在它之上。
>
> **本协议只定义「存在什么」。**
> 不定义状态怎么变（那是 State Protocol）、不定义动作怎么做（那是 Action Protocol）。

---

## 一、设计第一性原理

```
YuanForge 不构建 Runtime。
YuanForge 只定义 Object。

LLM 自己就是 Runtime——Object 是它操作的数据。
```

**铁律**：任何 Agent 平台实现 Adapter 时，必须能读写本文义的所有对象。不允许平台自己发明字段。

---

## 二、对象分层

| 层 | 生命周期 | 修改方式 | 驱动 |
|----|---------|---------|------|
| **Knowledge** | 长期（永不过期） | Proposal（事务保护） | 蒸馏（Conductor） |
| **Runtime** | 会话级（TTL） | 直接写（状态机驱动） | 工作流（Conductor） |
| **Event** | 永久（不可变） | Append Only | 事实发生 |

---

## 三、Knowledge 对象

Knowledge 对象回答了「项目知道什么」。它们存放在 `docs/knowledge/` 下。

### 3.1 Feature（功能）

**语义**：一个用户可感知的功能单元。

| 字段 | 类型 | 必填 | 说明 |
|------|------|:---:|------|
| `id` | string | ✅ | `FEAT-NNN` |
| `object_type` | enum | ✅ | `feature` |
| `status` | enum | ✅ | draft / designed / implemented / verified / deprecated |
| `summary` | string | ✅ | 一句话摘要 |
| `owner` | string | ✅ | 负责角色 |
| `confidence` | enum | ✅ | verified / stale / draft / deprecated |
| `depends` | array | — | 依赖的对象 ID |
| `verified_commit` | string | — | 最后验证时的 commit hash |
| `acceptance_criteria` | array | — | 验收标准 |
| `api_endpoints` | array | — | 涉及的 API |
| `files` | array | — | 关键源文件路径 |
| `session` | string | — | 实现此功能的会话 |

**状态机**：draft → designed → implemented → verified → deprecated

### 3.2 Decision / ADR（架构决策）

**语义**：一个不可逆的技术选择。

| 字段 | 类型 | 必填 | 说明 |
|------|------|:---:|------|
| `id` | string | ✅ | `ADR-NNN` |
| `object_type` | enum | ✅ | `decision` |
| `status` | enum | ✅ | proposed / accepted / deprecated / superseded |
| `summary` | string | ✅ | 决策摘要 |
| `owner` | string | ✅ | architect |
| `confidence` | enum | ✅ | verified / stale / draft / deprecated |
| `date` | date | ✅ | 决策日期 |
| `supersedes` | string | — | 取代的旧 ADR |
| `superseded_by` | string | — | 被取代 |
| `alternatives` | array | — | 备选方案 |
| `consequences` | object | — | 后果（positive / negative） |

**状态机**：proposed → accepted → deprecated / superseded

### 3.3 Pitfall（已知陷阱）

**语义**：一个已被验证会重复出现的问题模式。

| 字段 | 类型 | 必填 | 说明 |
|------|------|:---:|------|
| `id` | string | ✅ | `PIT-NNN` |
| `object_type` | enum | ✅ | `pitfall` |
| `status` | enum | ✅ | active / resolved / archived |
| `summary` | string | ✅ | 陷阱摘要 |
| `owner` | string | ✅ | 发现者角色 |
| `confidence` | enum | ✅ | verified / stale |
| `severity` | enum | ✅ | blocker / warning / info |
| `type` | enum | ✅ | backend / frontend / db / deploy / process / env |
| `cause` | string | ✅ | 根因 |
| `fix` | string | ✅ | 修复方法 |
| `session` | string | — | 发现此坑的会话 |

**状态机**：active → resolved → archived（resolved 可回 active）

### 3.4 Module（模块）

**语义**：系统中的一个逻辑模块。

| 字段 | 类型 | 必填 | 说明 |
|------|------|:---:|------|
| `id` | string | ✅ | `MOD-NNN` |
| `object_type` | enum | ✅ | `module` |
| `status` | enum | ✅ | active / deprecated |
| `summary` | string | ✅ | 模块摘要 |
| `owner` | string | ✅ | architect |
| `confidence` | enum | ✅ | verified / stale |
| `language` | string | ✅ | 主要语言 |
| `framework` | string | — | 框架 |
| `directory` | string | ✅ | 模块根目录 |
| `features` | array | — | 包含的 Feature ID |

**状态机**：active → deprecated

---

## 四、Runtime 对象

Runtime 对象回答了「项目正在做什么」。它们存放在 `docs/YYYYMMDD-描述/` 下或从 Events 派生。

### 4.1 Task（任务）

**语义**：一个可派发的工作单元。

| 字段 | 类型 | 必填 | 说明 |
|------|------|:---:|------|
|| `id` | string | ✅ | `T01` |
|| `role` | enum | ✅ | 12 角色之一 |
|| `priority` | enum | ✅ | P0 / P1 / P2 / P3 |
|| `status` | enum | ✅ | 见 State Protocol |
|| `summary` | string | ✅ | 任务描述 |
|| `depends_on` | array | — | 依赖的 Task ID |
|| `goal` | string | ✅ | Task 所属 Goal（逻辑分组，非独立对象） |
|| `goal_cluster` | string | — | Task 所属 Goal Cluster（一组相关 Goal） |
|| `acceptance` | string | ✅ | 验收标准（Given/When/Then 格式） |
|| `timeout_minutes` | int | ✅ | 超时阈值 |
|| `attempts` | int | ✅ | 当前尝试次数 |
|| `output_files` | array | — | 产出文件路径 |
|| `dispatch_context` | object | — | 派发注入的上下文 |

**状态机**：11 状态 — 详见 State Protocol §二

**生命周期**：Workspace 存活期间

### 4.2 Workspace（工作区）

**语义**：一个事务边界。对应 `docs/YYYYMMDD-描述/` 目录。

| 字段 | 类型 | 必填 | 说明 |
|------|------|:---:|------|
| `id` | string | ✅ | `20260709-描述` |
| `status` | enum | ✅ | created / executing / distilling / archived |
| `created_at` | datetime | ✅ | 创建时间 |
| `last_active_at` | datetime | ✅ | 最后活跃时间 |
| `ttl_days` | int | ✅ | 过期天数 |
| `git_head_at_create` | string | ✅ | 创建时的 commit |
| `task_summary` | object | — | total / completed / in_progress / blocked |

**状态机**：4 状态 — 详见 State Protocol §三

### 4.3 Snapshot（快照）

**语义**：Agent 在某个时刻的执行状态。崩溃恢复的微级数据。

| 字段 | 类型 | 必填 | 说明 |
|------|------|:---:|------|
| `agent_role` | string | ✅ | 角色 |
| `task_id` | string | ✅ | 正在执行的 Task |
| `status` | enum | ✅ | executing / checkpoint / completed / failed |
| `current_step` | string | — | 当前步骤描述 |
| `files_modified` | array | — | 已修改文件 |
| `last_commit` | string | — | 最后的 commit |

**状态机**：4 状态 — 详见 State Protocol §四

### 4.4 Proposal（变更请求）

**语义**：一个 Knowledge 层的变更请求。Knowledge 写保护的事务机制。

| 字段 | 类型 | 必填 | 说明 |
|------|------|:---:|------|
| `id` | string | ✅ | `prop-NNN` |
| `status` | enum | ✅ | draft / submitted / merged / rejected / expired |
| `target_object` | string | ✅ | 目标 Knowledge 对象 ID |
| `change_type` | enum | ✅ | distill / update / deprecate |
| `summary` | string | ✅ | 变更摘要 |

**状态机**：5 状态 — 详见 State Protocol §五

### 4.5 Checkpoint（检查点）

**语义**：Workspace 归档时的全量状态存档。不可变。

| 字段 | 类型 | 必填 | 说明 |
|------|------|:---:|------|
| `workspace_id` | string | ✅ | 来源 Workspace |
| `status` | enum | ✅ | created / archived |
| `git_head` | string | ✅ | 归档时的 commit |
| `task_states` | object | ✅ | 所有 Task 的最终状态 |
| `knowledge_outputs` | array | ✅ | 蒸馏产出的 Knowledge ID |
| `archive_path` | string | ✅ | 归档路径 |

**状态机**：2 状态 — created → archived

### 4.6 Workspace Metrics（循环遥测）

**语义**：Workspace 级别的 Loop 执行质量观测。不参与决策，只负责回答三个问题：是否在收敛？哪些环节最容易卡住？哪些协议真正提升了长期运行能力？

| 字段 | 类型 | 必填 | 说明 |
|------|------|:---:|------|
| `workspace_id` | string | ✅ | 所属 Workspace |
| `loop_count` | int | ✅ | 总 Loop 执行次数 |
| `avg_loop_duration_seconds` | float | — | 平均 Loop 持续时间 |
| `avg_dispatches_per_loop` | float | — | 每次 Loop 平均派发数 |
| `review_reject_rate` | float | — | 审查驳回率（返工次数/总审查次数） |
| `retry_count` | int | — | 修复回路触发次数 |
| `human_gate_count` | int | — | 人工介入点触发次数 |
| `blocked_duration_seconds` | float | — | 总阻塞时间 |
| `checkpoint_recovery_count` | int | — | Checkpoint 恢复次数 |
| `knowledge_promotions` | int | — | 知识晋升次数 |
| `failed_hypotheses_distilled` | int | — | 已蒸馏到 Knowledge 的失败假设数 |

**写入时机**：Workspace Close 时由 Doc Engineer 计算并写入 `docs/YYYYMMDD-描述/workspace-metrics.md`。

**用途**：仅用于评估协议效果，Conductor 不做基于 Metrics 的决策。

---

## 五、Event 对象

Event 回答了「发生了什么」。**不可变、Append Only。**

| 字段 | 类型 | 必填 | 说明 |
|------|------|:---:|------|
| `type` | enum | ✅ | 8 种事件类型 |
| `timestamp` | datetime | ✅ | 发生时间 |
| `workspace` | string | ✅ | 所属 Workspace |
| `actor` | string | ✅ | 触发者 |
| `payload` | object | ✅ | 事件数据 |

**事件类型（8 种）**：

| type | 含义 |
|------|------|
| TASK_STATUS_CHANGED | 任务状态变更 |
| KNOWLEDGE_UPDATED | 知识对象变更 |
| API_CHANGED | API 契约变更 |
| REVIEW_RESULT | 审查结果 |
| DISTILLATION_COMPLETE | 蒸馏完成 |
| WORKSPACE_CLOSED | 工作区关闭 |
| CRASH_RECOVERED | 崩溃恢复 |
| ERROR_OCCURRED | 错误发生 |

---

## 六、对象间关系

```
Workspace ──contains──→ Task[]
                      ├──→ Snapshot[] (per Agent)
                      └──→ Event[]

Task ──triggers──→ Event (status change)
Task ──references──→ Knowledge (via dispatch_context)
Task ──belongs_to──→ Goal (derived: group by Task.goal)
Task ──clustered_by──→ Goal Cluster (derived: group by Task.goal_cluster)

Workspace ──closes──→ Checkpoint
Checkpoint ──references──→ Knowledge outputs

Proposal ──modifies──→ Knowledge
Proposal ──produces──→ Event (KNOWLEDGE_UPDATED)

Workspace ──measured_by──→ Workspace Metrics (computed at Close)
```

### Goal 推导规则（Loop Engineering）

> **Goal 不是 Runtime 对象，是 Task 的逻辑分组。**

| 规则 | 推导方式 |
|------|---------|
| Goal 列表 | `group by Task.goal` 从 TASK_BOARD 导出 |
| Goal DONE | 该 Goal 下所有 Task 均为终态 |
| Goal ACTIVE | 至少一个 Task 处于非终态且非阻塞 |
| Goal BLOCKED | 至少一个 Task 为 ❌阻塞 且无阻塞解除条件 |
| Goal Cluster | `group by Task.goal_cluster` 导出 |

**铁律**：禁止在代码中维护 `Goal.state` 字段。Goal 状态必须每次从 Task 状态实时推导。

---

## 七、扩展规则

**新增对象类型**：
1. 在本文档追加类型定义
2. 定义 `fields`（必填字段）
3. 在 State Protocol 追加状态机

**新增字段**：在该对象类型下追加，不改变已有字段语义。

---

## 八、与其他协议的关系

| 协议 | 依赖方式 |
|------|---------|
| State Protocol | 定义本文每个对象的状态如何变化 |
| Action Protocol | Action 操作的对象由本文定义 |
| Workflow Protocol | Workflow 中的角色操作本文的对象 |
| Adapter Protocol | Adapter 必须能读写本文定义的所有对象 |
