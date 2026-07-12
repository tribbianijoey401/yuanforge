# EVENTS — 事件存储规格书

> 管辖 `docs/events/`。事件是不可变的事实记录，JSONL 格式，Append Only。

---

## 一、设计铁律

| # | 铁律 |
|---|------|
| Ⅰ | **Event 是事实，不是日志。** 每条事件记录一个已发生的事实（发生了什么、谁做的、结果是什么） |
| Ⅱ | **Append Only，永不修改。** 事件写入后不可变更、不可删除 |
| Ⅲ | **结构化，非自由文本。** 每条事件有固定的 type + payload schema |
| Ⅳ | **按日期分桶。** `events/YYYYMMDD/events.jsonl`，每天一个文件 |

---

## 二、目录结构

```
docs/events/
├── 20260709/
│   └── events.jsonl
├── 20260710/
│   └── events.jsonl
└── ...
```

每个 `events.jsonl` 文件是一行一个 JSON 对象：

```jsonl
{"type":"TASK_STATUS_CHANGED","timestamp":"...","session":"...","payload":{...}}
{"type":"REVIEW_RESULT","timestamp":"...","session":"...","payload":{...}}
```

---

## 三、事件类型定义

### 3.1 TASK_STATUS_CHANGED

**触发**：TASK_BOARD 中任务状态变更时。

**枚举的子类型**（`payload.change_type` 字段）：

| change_type | 状态转换 | 含义 |
|------------|---------|------|
| DISPATCH | 🟢→🔨 | Conductor 派发 Task 到 Agent |
| COMPLETE | 🔨→✅ | Agent 完成 Task |
| REWORK | ✅→🔄 | 审查不通过，打回返工 |
| BLOCK | 任意→❌ | Task 被阻塞 |
| UNBLOCK | ❌→🟢 | 阻塞解除 |
| TIMEOUT | 🔨→🟢 | 超时回退 |
| PASS_REVIEW | ✅→✅审查通过 | 审查通过 |
| PASS_TEST | ✅审查通过→✅测试通过 | 测试通过 |
| DEPLOY | ✅测试通过→✅已部署 | 部署完成 |

```json
{
  "type": "TASK_STATUS_CHANGED",
  "timestamp": "2026-07-09T14:30:00Z",
  "session": "20260709-用户认证",
  "actor": "backend-dev",
  "payload": {
    "task_id": "T03",
    "change_type": "COMPLETE",
    "old_status": "🔨进行中",
    "new_status": "✅完成",
    "reason": "实现完成，测试全部通过",
    "commit": "a1b2c3d"
  }
}
```

> **注：** conductor.md 中引用的 `DISPATCH`、`COMPLETE`、`REVIEW`、`REWORK`、`BLOCK` 均为本文 `TASK_STATUS_CHANGED` 事件的 `change_type` 子类型。

### 3.2 KNOWLEDGE_UPDATED

**触发**：knowledge/ 文件被创建或修改时（蒸馏或手动更新）。

```json
{
  "type": "KNOWLEDGE_UPDATED",
  "timestamp": "2026-07-09T17:00:00Z",
  "session": "20260709-用户认证",
  "actor": "conductor",
  "payload": {
    "action": "distilled",
    "object_id": "FEAT-AUTH",
    "object_type": "feature",
    "status": "verified",
    "file": "knowledge/features/FEAT-AUTH.md",
    "source_session": "20260709-用户认证"
  }
}
```

### 3.3 API_CHANGED

**触发**：API 契约变更时（新增/修改/废弃端点）。

```json
{
  "type": "API_CHANGED",
  "timestamp": "2026-07-09T12:00:00Z",
  "session": "20260709-用户认证",
  "actor": "architect",
  "payload": {
    "action": "added",
    "method": "POST",
    "path": "/auth/refresh",
    "feature": "FEAT-AUTH",
    "freeze_commit": "x9y0z1"
  }
}
```

### 3.4 REVIEW_RESULT

**触发**：审查官完成审查时。

```json
{
  "type": "REVIEW_RESULT",
  "timestamp": "2026-07-09T15:00:00Z",
  "session": "20260709-用户认证",
  "actor": "spec-reviewer",
  "payload": {
    "task_id": "T03",
    "gate": "🔴Blocker",
    "verdict": "passed",
    "issues_found": 0,
    "adversarial_attempts": 3
  }
}
```

### 3.5 DISTILLATION_COMPLETE

**触发**：Workspace Close 蒸馏完成时。

```json
{
  "type": "DISTILLATION_COMPLETE",
  "timestamp": "2026-07-09T17:00:00Z",
  "session": "20260709-用户认证",
  "actor": "conductor",
  "payload": {
    "outputs": [
      {"type": "feature", "id": "FEAT-AUTH"},
      {"type": "decision", "id": "ADR-003"}
    ],
    "not_distilled": [
      {"source": "BUG-006.md", "reason": "一次性环境问题"}
    ],
    "backlog_items": ["T05"]
  }
}
```

### 3.6 WORKSPACE_CLOSED

**触发**：Workspace 归档完成时。

```json
{
  "type": "WORKSPACE_CLOSED",
  "timestamp": "2026-07-09T17:05:00Z",
  "session": "20260709-用户认证",
  "actor": "conductor",
  "payload": {
    "archive_path": "archive/20260709-用户认证/",
    "total_tasks": 5,
    "completed_tasks": 4,
    "duration_minutes": 390
  }
}
```

### 3.7 CRASH_RECOVERED

**触发**：崩溃恢复完成时。

```json
{
  "type": "CRASH_RECOVERED",
  "timestamp": "2026-07-09T10:00:00Z",
  "session": "20260709-用户认证",
  "actor": "conductor",
  "payload": {
    "previous_session": "20260708-对抗式审查",
    "recovered_tasks": ["T03", "T04"],
    "dirty_files": ["src/auth/login.py"],
    "git_head_at_recovery": "d4e5f6g"
  }
}
```

### 3.8 ERROR_OCCURRED

**触发**：系统错误时（超时/异常中断/不可恢复错误）。

```json
{
  "type": "ERROR_OCCURRED",
  "timestamp": "2026-07-09T14:45:00Z",
  "session": "20260709-用户认证",
  "actor": "conductor",
  "payload": {
    "error_type": "timeout",
    "task_id": "T03",
    "attempt": 2,
    "details": "超过 30 分钟未完成，回退🟢"
  }
}
```

---

## 四、事件存储规则

### 4.1 写入

- Conductor 每次发生事件时追加一行到当天的 `events.jsonl`
- 不缓存、不批量——逐条追加（每次一条 `>>`）
- 写入后立即 flush

### 4.2 读取

```
查询"FEAT-AUTH 的所有历史事件":
  grep '"FEAT-AUTH"' docs/events/*/events.jsonl

查询"今天的所有 Blocker":
  grep '"🔴Blocker"' docs/events/20260709/events.jsonl

统计"本月蒸馏了多少 Feature":
  grep '"DISTILLATION_COMPLETE"' docs/events/202607*/events.jsonl | wc -l
```

### 4.3 保留策略

- Events 不可删除，永久保留
- 如需清理，归档到 `archive/events/` 而非删除

---

## 五、事件与恢复

### 5.1 State Replay

Events 可以重建历史状态：

```
给定初始状态 + 所有 TASK_STATUS_CHANGED 事件
  → 按时间排序
  → 逐个 apply
  → 任意时间点的 TASK_BOARD 状态
```

### 5.2 崩溃恢复辅助

崩溃恢复时，Conductor 可以读取最近的事件来了解「最近发生了什么」：

```
grep events/$(date +%Y%m%d)/events.jsonl
  → 最后一个 TASK_STATUS_CHANGED 是什么？
  → 最后一个 KNOWLEDGE_UPDATED 是什么？
  → 辅助判断崩溃时的状态
```

> **注意**：Events 是辅助恢复，不是主恢复源。主恢复源仍然是 TASK_BOARD（唯一真相源）。Events 提供时间线上下文。

---

## 六、与 SESSION_LOG 的关系

| | SESSION_LOG | Events |
|----|:---:|:---:|
| 目标读者 | Human | Machine |
| 格式 | Markdown 表格 | JSONL 结构化 |
| 内容 | 摘要 + 描述 | 精确事实 |
| 修改 | 渐进更新（可改） | Append Only（不可改） |
| 用途 | 人类回顾、跨会话桥梁 | 状态回放、统计、恢复辅助 |

> **SESSION_LOG = Human 视图，Events = Machine 视图。两者互补，不互相替代。**

---

## 七、各角色职责

| 角色 | 写什么事件 | 强制？ |
|------|-----------|:---:|
| Conductor | TASK_STATUS_CHANGED / DISTILLATION_COMPLETE / WORKSPACE_CLOSED / CRASH_RECOVERED / ERROR_OCCURRED | ✅ 强制 |
| Dev Agent | TASK_STATUS_CHANGED（领取 + 完成时） | — Tier 1/2 自动，Tier 3 由 Conductor 写 |
| Reviewer | REVIEW_RESULT | — Tier 1/2 自动，Tier 3 由 Conductor 写 |
| Architect | API_CHANGED / KNOWLEDGE_UPDATED（契约变更时） | — 按需 |
| Doc Engineer | KNOWLEDGE_UPDATED（归档更新时） | — 按需 |

> **Conductor 的 Event 写入是强制项。** 违反铁律 Ⅵ「文档即代码」—— 状态变更不记录事件 = 事实丢失。每次 Task 状态变更、审查完成、Workspace 关闭、崩溃恢复、超时/异常，Conductor 必须追加对应事件。写入方式见 conductor.md「Event 写入」段。

---

## 八、生命周期

| 阶段 | 操作 | 执行者 |
|------|------|--------|
| 任务状态变更 | 追加 TASK_STATUS_CHANGED | Conductor / Dev |
| 审查完成 | 追加 REVIEW_RESULT | Reviewer |
| 蒸馏完成 | 追加 DISTILLATION_COMPLETE + KNOWLEDGE_UPDATED | Conductor |
| Workspace 关闭 | 追加 WORKSPACE_CLOSED | Conductor |
| 崩溃恢复 | 追加 CRASH_RECOVERED | Conductor |
| 每日 | 自动按日期创建新 events.jsonl | Conductor |
