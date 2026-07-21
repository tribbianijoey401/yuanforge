# Runtime Protocol — 运行时层协议

> **依赖**: workflow-protocol

> **协议定位**：定义 YuanForge 的运行时层——如何让系统持续稳定推进。
> **Runtime 是框架的发动机。** 包含 Task、Loop、Checkpoint、Event 四个核心对象。
>
> **铁律**：Runtime 层是平台无关的。它不关心"用什么工具执行"，只关心"执行了什么、产生了什么结果"。

---

## 一、设计第一性原理

```
Runtime 层回答的问题：
  现在在做什么？（Task）
  下一步为什么发生？（Loop）
  为什么停止？（Checkpoint + Exit Gate）
  为什么以后还能继续？（Checkpoint 恢复）

Runtime 层不回答的问题：
  为什么做？（Goal Protocol — 意图层）
  怎么做？（Workflow Protocol — 方法层）
  在什么平台上跑？（Adapter Protocol — 执行层）
```

---

## 二、Task（工作单元）

> Task 是真正执行的对象。由 Architect 在 Plan 中生成，写入 TASK_BOARD.md。

```yaml
task:
  id: "T02"
  goal: "auth-module"
  description: "实现注册 API"
  owner: "Backend Dev"
  depends_on: ["T01"]
  status: "READY"
  acceptance: "Given 未注册邮箱，When 提交正确信息，Then 返回201并发送邮件"
  output: "src/api/register.go"
```

### Task 字段

| 字段 | 类型 | 必填 | 说明 |
|------|------|:---:|------|
| `id` | string | ✅ | 任务唯一标识 |
| `goal` | string | ✅ | 所属 Goal ID（逻辑分组） |
| `goal_cluster` | string | — | 所属 Goal Cluster（一组关联 Goal） |
| `description` | string | ✅ | 任务描述 |
| `owner` | string | ✅ | 负责角色 |
| `depends_on` | array | — | 依赖的 Task ID |
| `status` | enum | ✅ | READY / RUNNING / DONE / RETURN / BLOCKED |
| `acceptance` | string | ✅ | 验收标准（Given/When/Then） |
| `output` | string | ✅ | 产出文件路径 |

### Goal 推导规则

当 `goal = auth-module` 的所有 Task 均为 `DONE`，且 Security Auditor 无 Blocker，则 Goal DONE。

---

## 三、Loop（执行引擎）

> Loop 是 Conductor 中的固定循环，无业务感知，只机械推进 Task。

```
READ → SELECT → DISPATCH → WAIT → DIGEST → UPDATE → CHECK → (LOOP)
```

### Loop 七步

| 步骤 | 动作 | 说明 |
|------|------|------|
| **READ** | 扫描 TASK_BOARD.md | 获取所有 Task 状态 |
| **SELECT** | 选出 READY Task | 依赖已满足，按优先级排序 |
| **DISPATCH** | 注入合约+铁律+Goal摘要 | 派发给平台执行 |
| **WAIT** | 等待 Agent 完成 | 或超时/失败 |
| **DIGEST** | 比对产出与验收标准 | 通过→DONE，否则→RETURN |
| **UPDATE** | 更新 TASK_BOARD | 写入 Event Log |
| **CHECK** | 检查退出条件 | Goal 完成？Human Gate？Token 耗尽？ |

### Loop 内建收敛闸门

| 条件 | 动作 |
|------|------|
| 同一 Task 连续 2 次返工 | 通知 Architect 复审设计 |
| 同一 Task 连续 3 次返工 | 标记 BLOCKED，触发 Human Gate |
| 连续 3 个不同 Task 返工 | 暂停 Loop，请求用户确认方向 |

**连续推进原则**：获得用户授权后，Loop 必须自主推进直到遇见 Gate，不等用户逐任务驱动。

---

## 四、Checkpoint（恢复点）

> 在 Gate、Pause、Crash 或推理会话结束时强制生成。只存储恢复必需信息。

```yaml
checkpoint:
  goal_id: "auth-module"
  current_task: "T05"
  state: "等待用户确认计划"
  failed_hypotheses:
    - "JWT 为 Bug 源 → 已排除"
  next_action: "继续执行 T05"
```

### Checkpoint 四类信息

| 字段 | 说明 |
|------|------|
| `verified_facts` | 已验证事实（如"API 正常"、"Redis 连接池配置正确"） |
| `current_state` | 当前状态快照（如"Task-17 RUNNING"） |
| `next_action` | 下一步（如"等待 Reviewer"、"执行 TDD Red"） |
| `failed_hypotheses` | 已失败假设（仅保留 ACTIVE 状态的） |

### 失败假设生命周期

```
ACTIVE → VERIFIED_FALSE → DISTILLED → ARCHIVED
```

- **ACTIVE**：当前仍在怀疑的假设（Checkpoint 只保留这个）
- **VERIFIED_FALSE**：已验证不正确，蒸馏到 `knowledge/pitfalls/`
- **DISTILLED**：已从 Checkpoint 中移除
- **ARCHIVED**：随 Workspace 归档

**铁律**：Checkpoint 永远保持几 KB 以内。长期经验进入 Knowledge，不留在 Checkpoint。

---

## 五、Event Log（事件日志）

> 每条记录为不可变的 JSONL 行，用于审计和恢复。

```json
{"type": "TASK_STATUS_CHANGED", "timestamp": "2026-07-17T10:30:00Z", "workspace": "20260717-auth", "actor": "conductor", "payload": {"task_id": "T05", "from": "READY", "to": "RUNNING", "reason": "dispatched to backend-dev"}}
```

### 事件类型

| type | 含义 | 写入时机 |
|------|------|---------|
| `TASK_STATUS_CHANGED` | 任务状态变更 | 每次 Task 状态变化 |
| `REVIEW_RESULT` | 审查结果 | 审查完成后 |
| `DISTILLATION_COMPLETE` | 蒸馏完成 | Workspace Close 时 |
| `WORKSPACE_CLOSED` | 工作区关闭 | 归档时 |
| `CRASH_RECOVERED` | 崩溃恢复 | 跨会话恢复时 |
| `SESSION_EXITED` | 会话退出 | 用户触发暂停/自然结束 |
| `HUMAN_GATE_TRIGGERED` | 人工介入点触发 | 遇到 Gate 时 |
| `LOOP_METRICS` | Loop 遥测数据 | 每次 Loop 结束时 |

---

## 六、与其他协议的关系

| 协议 | 依赖方式 |
|------|---------|
| Goal Protocol | Runtime 层服务于 Goal 层定义的意图 |
| Object Protocol | Runtime 操作的对象（Task/Event/Checkpoint）由 Object Protocol 定义 |
| State Protocol | Runtime 的状态转换由 State Protocol 定义 |
| Action Protocol | Runtime 的 DISPATCH/WAIT/DIGEST 使用 Action Protocol 定义的 8 个标准动作 |
| Workflow Protocol | Runtime 的 Loop 由 Workflow 的 Phase 驱动 |
| Adapter Protocol | Runtime 的 Action 通过 Adapter 翻译为平台实现 |
