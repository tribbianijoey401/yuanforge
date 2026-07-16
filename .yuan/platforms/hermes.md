# Hermes Agent 平台适配

> 本文件告诉 Hermes Agent 如何执行 YuanForge 的定义。

---

## 加载规则

Hermes 的系统提示会注入 `.yuan/rules/` 下的规则文件：

| 规则 | 加载方式 |
|------|---------|
| iron-rules.md | 系统提示中注入 |
| plan-format.md | 写入 Plan 时参考 |
| .yuan/docs/ | project-bootstrap 读规格书创建 docs/ |

---

## 派发子 Agent（Conductor）

使用 Hermes 的 `delegate_task` 工具，按 12 人专家团合约派发：

```markdown
# Conductor 的标准操作：
1. 读取 Plan 中的 Dispatch Table
2. 解析依赖关系，构建 DAG
3. 按调度循环派发（见 Workflow Protocol「五、Conductor 调度循环」）：
   product-analyst → architect → frontend-dev/backend-dev
   → spec-reviewer/security-auditor/quality-auditor/ux-reviewer (并行)
   → tester → doc-engineer
4. 为每个 ready Task 调用 delegate_task，context 含：
   - Task 详细 spec
   - 对应角色合约（contracts/）
   - 铁律引用
   - 上游产出物路径
```

可选：如配置了 Kanban 系统，用 `kanban_create` 创建持久化任务板。

---

## 加载 Skill

使用 `skill_view(name)` 工具，skill 名称对应 `.yuan/skills/` 下的文件名（不含扩展名）。

示例：
```
skill_view("vibecoding-workflow")
skill_view("test-driven-development")
```

---

## 追踪进度

- `docs/PROGRESS.md` — 项目进度中枢
- `docs/YYYYMMDD-描述/SESSION_LOG.md` — 会话日志
- `docs/YYYYMMDD-描述/TASK_BOARD.md` — 运行时任务板

---

## 平台能力描述符

```yaml
platform: hermes
version: "1.0"

capabilities:
  subagent:
    supported: true
    max_concurrent: 3
    tool: delegate_task
  parallel:
    supported: true
    max_concurrent: 3
  filesystem:
    supported: true
    operations: [read, write, patch, search, list]
    tools: [read_file, write_file, patch, search_files]
  shell:
    supported: true
    background: true
    tool: terminal
  approval:
    supported: true
  patch:
    supported: true
    tool: patch
  persistent_session:
    supported: true
    tool: memory
  knowledge_graph:
    supported: false
    fallback: "grep knowledge/ frontmatter + manual graph build"
  event_store:
    supported: true
    fallback: "JSONL append via terminal"
  git:
    supported: true
    tool: terminal

execution:
  strategies: [parallel, sequential, interactive]
  defaults:
    max_retry: 3
    timeout_buffer_minutes: 5
    checkpoint_interval_minutes: 5

limitations:
  - "delegate_task 是同步的，父 Agent 等待子 Agent 完成"
  - "子 Agent 无父会话记忆，必须通过 context 传递全部信息"
  - "max_concurrent_children=3，可配置 delegation.max_concurrent_children"
  - "无原生 Graph 查询，需 grep + JSON 解析模拟"
```

---

## Action 映射（Adapter Protocol §三）

本平台如何实现 8 个统一 Action：

```yaml
platform: hermes
transport: hermes-subagent

dispatch:
  implementation: delegate_task
  notes: "同步派发子 Agent，父 Agent 等待完成。context 含角色合约 + Knowledge 引用 + 上游产出物"
  max_concurrent: 3

review:
  implementation: delegate_task
  notes: "以对应 Reviewer 角色派发子 Agent，注入验收标准 + diff"

snapshot:
  implementation: write_file
  notes: "写入 agents/<role>.yaml，记录当前步骤 + 文件修改 + 推理摘要"

checkpoint:
  implementation: write_file + terminal(git)
  notes: "Workspace 全量状态写入 archive/"

recover:
  implementation: conductor_loop
  notes: "Conductor 在新会话中执行崩溃检测 → 回退 🔨→🟢 → 通知用户"

archive:
  implementation: terminal(mv)
  notes: "mv docs/YYYYMMDD-描述/ → docs/archive/"

promote:
  implementation: conductor_loop + terminal(python)
  notes: "Conductor 执行蒸馏 Checklist → 写 Knowledge 对象 → 运行 build-graph.py"

limitations:
  - "delegate_task 是同步的，父 Agent 等待子 Agent 完成"
  - "子 Agent 无父会话记忆，必须通过 context 传递全部信息"
  - "max_concurrent_children=3，可配置 delegation.max_concurrent_children"
```

---

## 工具映射

| YuanForge 概念 | Hermes 工具 |
|---------------|------------|
| 派发子 Agent | `delegate_task` |
| 加载 Skill | `skill_view` |
| 项目管理 | `kanban_*` 系列 |
| 终端执行 | `terminal` |
| 文件操作 | `read_file` / `write_file` / `patch` |
| Git 操作 | `terminal` (git 命令) |

---

## 注意事项

- Hermes 的 `delegate_task` 是 **同步**的 — 父 Agent 等待子 Agent 完成
- 最多 3 个并行子 Agent（可配置 `delegation.max_concurrent_children`）
- 子 Agent 没有父会话的记忆 — 必须通过 context 传递全部信息

---

## 会话退出钩子

Hermes 平台的退出信号检测机制。

### 触发方式

| 方式 | 检测逻辑 | 说明 |
|------|---------|------|
| 用户主动 | 消息包含「暂停」「明天继续」「先停了」「save progress」关键词 | 在 AGENTS.md 模式判定中处理 |
| 空闲检测 | Conductor 巡检发现 30 分钟无状态变化 | 见 conductor.md「死循环保护」 |
| 自然结束 | 所有 Phase 完成（TASK_BOARD 全部 ✅） | 调度循环 break 后触发 |
| 平台中断 | cronjob 定时扫描活跃会话 | 后台守护进程触发 |

### 执行流程

```
Hermes 退出钩子:
    1. Conductor 检测到退出信号
    2. 执行退出协议（见 contracts/conductor.md「退出协议」）
    3. 可选：发送通知到用户
       - 如果用户通过 QQ/Telegram 等消息平台接入
       - 发送: "会话已保存进度。下次启动会自动恢复。"
```

### 实现建议

对于 Hermes 平台，退出协议的执行由 Conductor 在消息处理完成后自动触发：

1. **消息级退出**：用户发送包含退出关键词的消息 → 模式判定识别为「暂停类」→ 触发退出协议
2. **会话级退出**：Hermes gateway 检测到会话长时间空闲 → 触发 cronjob 扫描 → 对活跃会话执行 checkpoint
3. **计划退出**：所有 Phase 完成后 → Conductor 自动执行退出协议 → 更新会话日志

> 注意：Hermes 的消息处理是请求-响应模式，不是长会话。退出协议应该在**消息处理完成后**、**返回响应之前**执行。
