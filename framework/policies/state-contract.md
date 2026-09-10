# Persisted State Contract

本文件是 Yuan Project State 的唯一语义契约。Phase 2 Multi-Work 模型把 **Work 本身作为执行隔离边界**：

```text
Project
├── docs/works/W-101.md
├── docs/works/W-102.md
├── docs/works/W-103.md
└── docs/STATUS.md          # focus + focused-work recovery projection
```

`framework://tools/state_guard.py` 是该契约的只读可执行校验器。Conductor 是唯一正式 State Writer；Insight、Installer Check 与 Specialist 只能复用校验结果或返回 `work_updates`，不得建立第二套状态词汇。

## Canonical Sources

| Field | Canonical source | Rule |
|---|---|---|
| Work identity | `project://docs/works/<work-id>.md` 文件名 stem + frontmatter `id` | 两者必须一致；一个文件就是一个持久化 Work |
| Work `state` | 本契约 | `ready` / `active` / `paused` / `blocked` |
| Work `workflow` | `framework://workflows/*.md` | 使用 Workflow 文件名 stem |
| Work `stage` | 当前 Workflow frontmatter 的 `stages` | 使用列表中的精确值 |
| Work `agent.id` | 当前 Workflow frontmatter + `framework://agents/*.md` | 使用 Agent Contract 文件名 stem，且必须被当前 Workflow 声明 |
| Work `agent.state` | 本契约 | `idle` / `active` / `paused` / `completed` / `blocked` |
| `STATUS.focus` | `project://docs/works/*.md` | null 或一个真实 Work 文件名 stem |
| `STATUS.work/...` | focused Work | 仅为恢复投影，不是第二份 Truth Source |
| `execution` | active Work frontmatter | 单 active Work 可省略；并发 active Work 必须提供 Platform 已分配的隔离执行身份 |

`agent.instance` 是可选自由文本，用于 Persona、Subagent、Session 或执行通道标签，不参与路由。它在只有一个 active Work 时可省略；有多个 active Work 时必须是每条并发 lane 的真实、唯一 independent execution instance，`persona-degraded` 不是独立实例。

## Work File Contract

Conductor 从 `framework://templates/project/WORK.md` 的 body 创建：

```yaml
---
id: W-102
state: active
workflow: complex-bug
stage: implement
agent:
  id: backend-dev
  instance: subagent
  state: active
quality:
  test: pending
  review: pending
---
```

Work body 保存 Goal、Scope、Acceptance、Current Task、Latest Result、Open Findings、Work Learnings、Next Action 与 Blocker。具体动作只写入该 Work 的 Current Task；不得把 Current Task 写进 `stage`。

### Work lifecycle

- `ready`：已形成独立 Work Contract，但当前不执行。Workflow / Stage / Agent 可以尚未选择；若已写入则仍需使用规范值。
- `active`：当前正式执行的 Work；必须有 Workflow、Stage、当前 Agent 与 Current Task。
- `paused`：保留 Workflow / Stage，`agent.state: paused`，且必须有唯一 Next Action。
- `blocked`：保留 Workflow / Stage，`agent.state: blocked`，且必须有可观察 Blocker。
- Completion 不是长期 active-store 状态。Acceptance、Verification、Review 与 `Open Findings = 0` 满足后先 Distill；有长期历史价值时写精炼摘要到 `project://docs/works/archive/`，然后移除当前 `project://docs/works/<id>.md`。其它 Work 不受影响。

## Phase 2 Concurrency Boundary

Phase 2 支持 **Multiple Persisted Works** 与受约束的并发 active Work，但不是并行 Work Scheduler：

- 一个 Project 可以同时存在多个 `ready` / `paused` / `blocked` Work；单个 active Work 完全兼容 Phase 1，`execution` 可省略。
- 两个或以上 `active` Work 时，每一个都必须声明 `execution.mode: isolated`、唯一非空的 `execution.workspace`，以及唯一的真实 `agent.instance`；State Guard 拒绝缺失、重复或 `persona-degraded` 伪并发。
- Framework 只验证 Platform 提供的 identity，绝不分配 workspace、创建 worktree/branch、调度 worker、合并输出或判定 mutation overlap。
- `STATUS.focus` 必须是某个 active Work，且 `STATUS.work/...` 仍只投影该 focused Work；它表示当前 interaction，不再表示唯一 active Work。
- 同一 execution.workspace 始终只有一个 Writer。integration 仍串行且由 Conductor 明确提交。

## STATUS Recovery Index

`project://docs/STATUS.md` 是短小 Recovery Index。新格式至少包含：

```yaml
---
focus: W-102
work: W-102
work_state: active
workflow: complex-bug
stage: implement
agent:
  id: backend-dev
  instance: subagent
  state: active
quality:
  test: pending
  review: pending
---
```

其中 `work / work_state / workflow / stage / agent / quality` 是 focused Work 的**派生投影**。它们存在是为了快速 Resume 与兼容观察工具，Canonical State 仍在 Work 文件。Conductor 每次 State Commit 必须在同一逻辑步骤更新 focused Work 与 STATUS；State Guard 对投影逐字段校验，任何漂移都返回 `STATE_FOCUS_PROJECTION_MISMATCH`。

没有 focus 时：

```yaml
focus: null
work: null
work_state: idle
workflow: null
stage: null
agent:
  id: null
  instance: null
  state: null
```

这里 `idle` 只表示 Project 当前没有 focused Work，不是 Work 文件允许的 state。

## Focus and Switching

Focus 是 Project 的唯一恢复锚点，表示本次 Conductor interaction 正式操作哪个 Work，不表示其它 Work 不存在。

- 单 active Work 时，focus switch 仍须先 complete / pause / block 当前 Work。
- 多个合法 isolated active Work 时，focus 可在这些 active Work 间切换；切换只更新 STATUS projection，不暂停、归档或完成任一 Work。
- 当前没有 active Work 时，focus 可以指向 `ready` / `paused` / `blocked` Work 用于讨论或恢复；正式 Dispatch 前再切为 `active`。
- 用户明确开始一个独立的新工作：可创建新的非 focused `ready` Work；若要与现有 active Work 并发，必须先满足本节 isolation contract。
- 与当前目标无关、尚未形成明确 Goal / Scope / Acceptance 的未来想法仍进入 BACKLOG，不为了“多 Work”把所有想法都实例化。

## Execution Identity

规范路由身份与执行标签必须分开：

```yaml
workflow: complex-bug
stage: implement
agent:
  id: frontend-dev
  instance: frontend-fixer
  state: active
```

并发 lane 还必须由 Platform 提供不可复用的 mutable workspace：

```yaml
execution:
  mode: isolated
  workspace: platform://workspace/W-102
```

- `agent.id` 决定 Agent Contract、Skill Assignment 和 Insight Registry 映射。
- `agent.instance` 不得提升为动态 Agent Registry 条目。
- `execution.mode` 当前唯一允许并发的值是 `isolated`；`shared` 不能用于多个 active Work。
- `execution.workspace` 是 identity，不是 Framework 要创建、扫描或管理的目录。
- Writer 的 transient `review_context` 只属于当前 Work 的当前 execution chain；不得跨 Work relay，也不得写入任何 Work、STATUS、Memory 或 Project Truth。

## State Commit Gate

每次 Work create/focus/activate、Dispatch、Focused Result、Stage/Agent 转换、Pause、Resume、Block/Unblock、Switch 与 Distill 都执行：

1. 从本契约和当前 Workflow / Agent Contract 选择规范值。
2. Conductor 在同一逻辑步骤写入当前 `project://docs/works/<id>.md` 与 `project://docs/STATUS.md`；创建非 focused `ready` Work 时只需写该 Work 文件，STATUS focus 不变。
3. 解析 `framework://tools/state_guard.py` 为真实路径并运行：

   `python -B <resolved-state-guard-path> check <project-root>`

4. 只有输出 `STATE_VALID` 才算 State Commit 完成，才允许继续 Dispatch 或修改下一项 Project Artifact。
5. 校验失败时，Conductor 根据 issue 的 canonical source 与 repair 修正同一次 Commit；不得由 Specialist、Insight 或 Installer 自动改写。

需要查看合法 Workflow / Stage / Agent 时：

`python -B <resolved-state-guard-path> catalog <project-root> --workflow <workflow-id>`

## Legacy Single-Work Compatibility

v4 Project 可能仍只有 `project://docs/WORK.md` 与旧 STATUS（没有 `focus` 字段）。Framework Update **不自动迁移 Project-owned State**。

- State Guard 继续读取旧格式，避免升级后无法 Resume。
- Conductor 在下一次有足够 identity 的正式 State Commit，把 legacy Work 原样语义迁入 `project://docs/works/<work-id>.md`，再把 STATUS 改成 focus + projection。
- 迁移必须保留 Goal、Scope、Acceptance、Current Task、Latest Result、Open Findings、Work Learnings、Verification 与 Next Action；不得借迁移重写 Product Truth。
- 若旧文件缺少稳定 Work id 或结构无法可靠解释，保持 legacy compatibility 并披露 identity gap，不猜测创建新 id。
- `project://docs/WORK.md` 在新模型中仅为 legacy compatibility 文件，不再是 canonical multi-work state。

## Compatibility

Framework Update 原样保留 `project://docs/` 和 `project://docs/works/`。Update 后的 Check 只报告状态问题，不静默修复。旧 STATUS 中额外的非规范字段不参与路由；新的 Work 状态只能使用上述 canonical values。
