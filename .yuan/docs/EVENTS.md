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

**设计原则**：记录"为什么变"，不记录"变成了什么"（后者在 TASK_BOARD 中）。

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
    "reason": "实现完成，测试全部通过",
    "commit": "a1b2c3d"
  }
}
```

> **优化点**：移除了 `old_status` / `new_status` 字段。TASK_BOARD 才是状态的唯一真相源，Event 只记录变更原因。如果需要状态回放，从 TASK_BOARD + Event reason 联合推断。

> **错误信息**：如果变更伴随错误，在 payload 中添加 `error` 字段：
> ```json
> {"type": "TASK_STATUS_CHANGED", "payload": {"task_id": "T05", "change_type": "BLOCK", "reason": "阻塞", "error": "SDK 端点未配置"}}
> ```

> **注**：conductor.md 中引用的 `DISPATCH`、`COMPLETE`、`REVIEW`、`REWORK`、`BLOCK` 均为本文 `TASK_STATUS_CHANGED` 事件的 `change_type` 子类型。

### 3.2 KNOWLEDGE_UPDATED

**触发**：knowledge/ 文件被创建或修改时（蒸馏或手动更新）。

**优化**：此事件类型已合并到 `DISTILLATION_COMPLETE` 中。仅在**非蒸馏场景**下手动更新 knowledge 时使用（如手动添加 Pitfall）。

```json
{
  "type": "KNOWLEDGE_UPDATED",
  "timestamp": "2026-07-09T17:00:00Z",
  "session": "20260709-用户认证",
  "actor": "conductor",
  "payload": {
    "action": "manual_add",
    "object_id": "PIT-013",
    "object_type": "pitfall",
    "file": "knowledge/pitfalls/PIT-013.md"
  }
}
```

> **注意**：蒸馏产生的知识变更不再单独写 KNOWLEDGE_UPDATED 事件。`DISTILLATION_COMPLETE` 已包含完整的产出列表。
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

**优化**：只记录结论摘要和最重要的 1-2 条对抗发现。完整报告在 TASK_BOARD「审查结果」段。

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
    "top_findings": [
      "对抗测试: 构造了 3 个边界输入（空字符串、null、超长字段），全部通过",
      "合规检查: 验收标准 AC-1 ~ AC-5 全部覆盖"
    ],
    "adversarial_attempts": 3
  }
}
```

> **优化点**：移除了 `issues_found` 字段。改为 `top_findings`（最重要的 1-2 条发现），让人不看 TASK_BOARD 就能知道"这次审查过了没，发现了什么"。
```

### 3.5 DISTILLATION_COMPLETE

**触发**：Workspace Close 蒸馏完成时。

**优化**：此事件已合并 `KNOWLEDGE_UPDATED` 的信息，包含完整的知识产出列表。

```json
{
  "type": "DISTILLATION_COMPLETE",
  "timestamp": "2026-07-09T17:00:00Z",
  "session": "20260709-用户认证",
  "actor": "conductor",
  "payload": {
    "outputs": [
      {"type": "feature", "id": "FEAT-AUTH"},
      {"type": "decision", "id": "ADR-003"},
      {"type": "pitfall", "id": "PIT-012"}
    ],
    "not_distilled": [
      {"source": "BUG-006.md", "reason": "一次性环境问题"}
    ],
    "backlog_items": ["T05"]
  }
}
```
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

### 3.8 ERROR_OCCURRED（已废弃）

> **已合并到其他事件**。错误信息现在作为 `payload.error` 字段附加到对应事件中。
> 例如：TASK_STATUS_CHANGED 的 BLOCK 类型可以携带 error 字段。
> 此事件类型保留仅供向后兼容，新代码不应再使用。
```

### 3.9 SESSION_EXITED

**触发**：会话退出协议执行完成时。

**设计原则**：记录"为什么退出"和"退出了什么状态"，作为下次会话恢复的入口锚点。

```json
{
  "type": "SESSION_EXITED",
  "timestamp": "2026-07-14T18:30:00Z",
  "session": "20260714-用户认证",
  "actor": "conductor",
  "payload": {
    "phase": "Phase 4",
    "completed_tasks": ["T01", "T02"],
    "remaining_tasks": ["T03"],
    "reason": "用户说「明天继续」",
    "last_dispatch": "T03 → backend-dev",
    "review_summary": "4 审查官全部通过"
  }
}
```

> **与 WORKSPACE_CLOSED 的区别**：SESSION_EXITED 是会话级退出（可能还有未完成的任务），WORKSPACE_CLOSED 是 Feature 级完全关闭（所有任务终态 + 蒸馏完成）。一个 Feature 可能有多个 SESSION_EXITED，但只有一个 WORKSPACE_CLOSED。

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

|| 角色 | 写什么事件 | 强制？ |
|------|-----------|:---:|
| Conductor | TASK_STATUS_CHANGED / DISTILLATION_COMPLETE / WORKSPACE_CLOSED / CRASH_RECOVERED / SESSION_EXITED | ✅ 强制 |
| Dev Agent | TASK_STATUS_CHANGED（领取 + 完成时） | — Tier 1/2 自动，Tier 3 由 Conductor 写 |
| Reviewer | REVIEW_RESULT | — Tier 1/2 自动，Tier 3 由 Conductor 写 |
| Architect | API_CHANGED / KNOWLEDGE_UPDATED（契约变更时） | — 按需 |
| Doc Engineer | KNOWLEDGE_UPDATED（归档更新时） | — 按需 |

> **Conductor 的 Event 写入是强制项。** 违反铁律 Ⅵ「文档即代码」—— 状态变更不记录事件 = 事实丢失。每次 Task 状态变更、审查完成、Workspace 关闭、崩溃恢复，Conductor 必须追加对应事件。写入方式见 conductor.md「Event 写入」段。

> **优化**：`ERROR_OCCURRED` 已合并到其他事件的 `error` 字段。`KNOWLEDGE_UPDATED` 仅在非蒸馏场景下手动更新 knowledge 时使用，蒸馏产生的知识变更由 `DISTILLATION_COMPLETE` 统一记录。

---

## 八、生命周期

|| 阶段 | 操作 | 执行者 |
|------|------|--------|
| 任务状态变更 | 追加 TASK_STATUS_CHANGED（只写 reason，不写 old/new status） | Conductor / Dev |
| 审查完成 | 追加 REVIEW_RESULT（只写 verdict + top findings） | Reviewer |
| 蒸馏完成 | 追加 DISTILLATION_COMPLETE（包含知识产出列表） | Conductor |
| Workspace 关闭 | 追加 WORKSPACE_CLOSED | Conductor |
| 崩溃恢复 | 追加 CRASH_RECOVERED | Conductor |
| 会话退出 | 追加 SESSION_EXITED（phase + completed/remaining + reason） | Conductor |
| 每日 | 自动按日期创建新 events.jsonl | Conductor |
