# RUNTIME_MODEL — 运行时对象模型规格书

> 定义 Runtime 层所有对象的类型、状态机、生命周期。全部确定性规则，禁止依赖 LLM 推理。

---

## 一、设计原则

```
Knowledge Object Model 回答了「项目知道什么」
Runtime Object Model   回答了「项目正在做什么」
```

| | Knowledge | Runtime |
|----|:---:|:---:|
| 生命周期 | 长期 | 会话级（TTL） |
| 修改方式 | Proposal（事务保护） | 直接写（状态机驱动） |
| 驱动方式 | 蒸馏（Conductor） | 规则引擎（确定性） |
| 过期 | verified_commit 检测 | TTL 自动归档 |

---

## 二、Runtime 对象总览

| 对象 | 作用 | 状态机 | 生命周期 |
|------|------|:---:|------|
| **Task** | 一个可派发的工作单元 | 11 状态 | Workspace 存活期间 |
| **Workspace** | 一个事务边界 | 4 状态 | 创建 → 执行 → 蒸馏 → 归档 |
| **Snapshot** | Agent 在某个时刻的状态快照 | 4 状态 | Agent 存活期间 |
| **Event** | 一个已发生的事实 | 无状态（不可变） | 永久 |
| **Proposal** | 一个 Knowledge 变更请求 | 5 状态 | 提交 → 合并/拒绝/过期 |
| **Checkpoint** | Workspace 的完整状态存档 | 2 状态 | Workspace 关闭后 |

---

## 三、Task 对象

### Schema

```yaml
task:
  id: "T03"
  role: "backend-dev"
  priority: P2                     # P0/P1/P2/P3
  status: "🔨进行中"               # 见状态机
  summary: "实现 JWT token 刷新端点"
  depends_on: ["T02"]
  timeout_minutes: 30
  output_files: ["src/auth/refresh.py"]
  attempts: 1                      # 当前是第几次尝试
  created_at: "2026-07-09T10:00:00Z"
  started_at: "2026-07-09T10:05:00Z"
  completed_at: null
  dispatch_context:                # 派发时注入的最少上下文
    required_knowledge: ["ADR-003", "FEAT-AUTH"]
    input_from: ["T02"]
    acceptance_criteria:
      - "refresh token 必须轮转"
      - "旧 token 必须在刷新后失效"
```

### 状态机（确定性转换）

```
⏳等待 ──[依赖满足]──→ 🟢就绪
🟢就绪 ──[Agent 领取]──→ 🔨进行中
🔨进行中 ──[完成]──→ ✅完成
🔨进行中 ──[超时]──→ 🟢就绪（attempts++）
🟢就绪 ──[attempts≥3]──→ ❌阻塞
✅完成 ──[审查通过]──→ ✅审查通过
✅完成 ──[审查不通过]──→ 🔄返工
🔄返工 ──[修复]──→ 🔨进行中
🔄返工 ──[≥3次]──→ ❌阻塞
✅审查通过 ──[测试通过]──→ ✅测试通过
✅测试通过 ──[部署]──→ ✅已部署
任意非终态 ──[取消]──→ ❌取消
任意非终态 ──[崩溃恢复]──→ 🟢就绪（attempts保留）
```

### 确定性规则

| 规则 | 触发条件 | 动作 |
|------|---------|------|
| **Promote** | Task 的 depends_on 全部终态 | ⏳→🟢 |
| **Timeout** | now - started_at > timeout_minutes | 🔨→🟢 + attempts++ |
| **Block** | attempts ≥ 3 | 🟢→❌阻塞 |
| **Cancel cascade** | 上游 ❌取消 | 本 Task → ❌阻塞（原因=上游取消） |
| **Crash recover** | 崩溃恢复触发 | 🔨→🟢，写入故障记录类型=崩溃恢复 |

---

## 四、Workspace 对象

### Schema

```yaml
workspace:
  id: "20260709-用户认证"
  status: "executing"              # created/executing/distilling/archived
  created_at: "2026-07-09T09:00:00Z"
  last_active_at: "2026-07-09T15:30:00Z"
  ttl_days: 7
  git_head_at_create: "a1b2c3d"
  tasks:
    total: 5
    completed: 3
    in_progress: 1
    blocked: 0
  distillation:
    completed: false
    outputs: []
```

### 状态机

```
created ──[Phase 1 开始]──→ executing
executing ──[所有 Task 终态]──→ distilling
distilling ──[蒸馏完成]──→ archived
executing ──[TTL 过期]──→ distilling（强制蒸馏）
```

### 确定性规则

| 规则 | 触发 | 动作 |
|------|------|------|
| **Auto-distill** | 所有 Task 终态 | 自动触发蒸馏流程 |
| **TTL-expire** | now - last_active_at > ttl_days | 通知用户 → 强制蒸馏归档 |
| **Crash-reopen** | 崩溃恢复 | 从 archive 或活跃 Workspace 恢复 |

---

## 五、Snapshot 对象

### Schema

```yaml
snapshot:
  agent_role: "backend-dev"
  task_id: "T03"
  status: "checkpoint"             # executing/checkpoint/completed/failed
  checkpoint_time: "2026-07-09T14:25:00Z"
  current_step: "正在写 refresh token 的数据库查询逻辑"
  step_index: 4
  files_modified: ["src/auth/service.py"]
  files_created: ["tests/auth/test_refresh.py"]
  git_staged: false
  reasoning_summary: "选择 service 层做 refresh token 验证——便于复用"
  next_action: "完成 DB 查询后写单元测试"
  last_commit: "d4e5f6g"
```

### 状态机

```
executing ──[写 checkpoint]──→ checkpoint
checkpoint ──[恢复执行]──→ executing
executing ──[完成]──→ completed
executing ──[失败]──→ failed
```

---

## 六、Event 对象

### Schema

```yaml
event:
  type: "TASK_STATUS_CHANGED"      # 8 种事件类型
  timestamp: "2026-07-09T14:30:00Z"
  workspace: "20260709-用户认证"
  actor: "backend-dev"
  payload:
    task_id: "T03"
    old_status: "🔨进行中"
    new_status: "✅完成"
```

### 事件类型（8 种）

| type | payload 关键字段 | 触发者 |
|------|-----------------|--------|
| TASK_STATUS_CHANGED | task_id, old_status, new_status | Agent / Rule Engine |
| KNOWLEDGE_UPDATED | object_id, object_type, action | Conductor (蒸馏) |
| API_CHANGED | method, path, action | Architect |
| REVIEW_RESULT | task_id, gate, verdict | Reviewer |
| DISTILLATION_COMPLETE | outputs, not_distilled | Conductor |
| WORKSPACE_CLOSED | archive_path, total_tasks | Conductor |
| CRASH_RECOVERED | recovered_tasks, dirty_files | Conductor |
| ERROR_OCCURRED | error_type, task_id, details | Rule Engine |

---

## 七、Proposal 对象

### Schema

```yaml
proposal:
  id: "prop-042"
  status: "submitted"              # draft/submitted/merged/rejected/expired
  target_object: "FEAT-AUTH"
  target_file: "knowledge/features/FEAT-AUTH.md"
  author: "architect"
  created_at: "2026-07-09T18:00:00Z"
  change_type: "update_status"
  summary: "标记 FEAT-AUTH 为 deprecated"
  depends_on: []
```

### 状态机

```
draft ──[提交]──→ submitted
submitted ──[合并]──→ merged
submitted ──[拒绝]──→ rejected
submitted ──[7天过期]──→ expired
```

### 确定性规则

| 规则 | 触发 | 动作 |
|------|------|------|
| **Conflict detect** | 两个 Proposal 同一 target | 排队，先到先处理 |
| **Auto-expire** | submitted > 7天 | submitted → expired |
| **Dependency wait** | depends_on 未处理 | 等待 |

---

## 八、Checkpoint 对象

### Schema

```yaml
checkpoint:
  workspace_id: "20260709-用户认证"
  created_at: "2026-07-09T17:05:00Z"
  status: "archived"               # created/archived
  snapshot:
    git_head: "a1b2c3d"
    task_states:
      T01: "✅测试通过"
      T02: "✅完成"
      T03: "✅审查通过"
    knowledge_outputs: ["FEAT-AUTH", "ADR-003"]
  archive_path: "archive/20260709-用户认证/"
```

### 状态机

```
created ──[Workspace 归档]──→ archived
```

Checkpoint 是 Workspace 归档时生成的不可变快照。它与 Events 互补——Events 是增量事实，Checkpoint 是全量快照。

---

## 九、对象间关系

```
Workspace ──contains──→ Task[]
                      ├──→ Snapshot[] (per Agent)
                      └──→ Event[]

Task ──produces──→ Snapshot (Agent writes)
Task ──triggers──→ Event (status change)
Task ──references──→ Knowledge (via dispatch_context)

Workspace ──closes──→ Checkpoint
Checkpoint ──references──→ Knowledge outputs
Checkpoint ──archives──→ archive/

Proposal ──modifies──→ Knowledge
Proposal ──produces──→ Event (KNOWLEDGE_UPDATED)

Event ──feeds──→ Rule Engine
Rule Engine ──drives──→ Task state transitions
```

---

## 十、与现有规格书的关系

| 规格书 | 如何关联 |
|--------|---------|
| OBJECT_MODEL.md | Runtime Model 定义 Runtime 对象，Object Model 定义 Knowledge 对象 |
| TASK_BOARD.md | Task 的状态机实现为 TASK_BOARD.md 的运行时行为 |
| SESSION.md | Workspace 的生命周期定义 |
| EVENTS.md | Event 的 Schema 定义 |
| PROPOSAL.md | Proposal 的 Schema 和生命周期 |
