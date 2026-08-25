# Persisted State Contract

本文件是 `project://docs/STATUS.md` 规范状态值的唯一语义契约。它约束 Conductor 的正式 State Commit；`framework://tools/state_guard.py` 是该契约的只读可执行校验器。Insight 和 Installer Check 只能复用校验结果，不得定义第二套状态词汇或自动改写 Project State。

## Canonical Sources

| Field | Canonical source | Rule |
|---|---|---|
| `work_state` | 本契约 | 只能是 `idle`、`active`、`paused` |
| `workflow` | `framework://workflows/*.md` | 使用 Workflow 文件名 stem |
| `stage` | 当前 Workflow frontmatter 的 `stages` | 使用列表中的精确值，不创造别名或执行动作名 |
| `agent.id` | 当前 Workflow frontmatter + `framework://agents/*.md` | 使用当前 Workflow 已声明且确有 Agent Contract 的文件名 stem |
| `agent.state` | 本契约 | 只能是 `idle`、`active`、`paused`、`completed`、`blocked` |
| `presentation_contract` | 本契约 | 只能是 `n/a`、`pending`、`frozen` |

`work_state: active` 时，`agent.state` 只能是 `active`、`completed` 或 `blocked`；`work_state: paused` 时，`agent.state` 必须为 `paused`。完成并 Distill 后使用 `work_state: idle`，同时清空 Work、Workflow、Stage 和 Agent 引用，不新增 `completed` Work state。

`presentation_contract` 是 UI 设计冻结信号：`n/a`（无 UI Work）、`pending`（有 UI 但 Presentation Contract 尚未冻结）、`frozen`（UI Designer 已产出并冻结 Presentation Contract）。涉及 UI 的 New Feature / Large Project 在 `frontend-dev` 进入实现阶段前必须为 `frozen`；同时 `WORK.md` 的 `Presentation Contract` Section 必须包含 `Status: frozen`、可用的 Product Truth、Contract Locator 与 Prototype / Verification evidence。状态字段不能作为空壳替代设计内容。该硬门由 `framework://tools/state_guard.py` 校验。纯后端或 Bug 修复 Work 使用 `n/a`，不触发硬门。

## Execution Identity

规范路由身份与一次执行中的标签必须分开：

```yaml
workflow: complex-bug
stage: implement
agent:
  id: frontend-dev
  instance: frontend-fixer
  state: active
```

- `agent.id` 决定 Agent Contract、Skill Assignment 和 Insight Registry 映射，必须规范，并且必须出现在当前 Workflow 的 `required_agents`、`required_agent_groups` 或 `optional_agents` 中。
- `agent.instance` 是可选自由文本，用于 Persona、Subagent、Session 或执行实例标签，不参与路由。
- 当前具体动作以 `project://docs/WORK.md` 的 Current Task 为唯一 Project State 真相源；Insight 等观察工具从该事实派生展示，不在 STATUS 中维护第二份动作标签。
- 不得将 `agent.instance` 提升为动态 Agent Registry 条目，也不得将 Current Task 写入 `stage`。

## State Commit Gate

每次 Work 激活、Dispatch、Focused Result、Stage/Agent 转换、Pause、Resume 和 Distill 都执行：

1. 从上述 Canonical Sources 选择值；不凭记忆创造名称。
2. Conductor 在同一逻辑步骤写入 `project://docs/WORK.md` 与 `project://docs/STATUS.md`。
3. 解析 `framework://tools/state_guard.py` 为真实路径并运行：

   `python -B <resolved-state-guard-path> check <project-root>`

4. 只有输出 `STATE_VALID` 才算 State Commit 完成，才允许继续 Dispatch 或修改下一项 Project Artifact。
5. 校验失败时，Conductor 根据错误中的 canonical source 和 repair 修正同一次 Commit；不得由 Specialist、Insight 或 Installer 自动改写。

需要在写入前查看合法值时运行：

`python -B <resolved-state-guard-path> catalog <project-root> --workflow <workflow-id>`

## Compatibility

- `agent.instance` 是可选字段；不增加它的旧 Project 继续有效。旧 STATUS 中额外的非规范字段不参与路由、恢复或 Guard 判定。
- Framework Update 原样保留 Project Document，不迁移既有状态。Update 后的 Check 只报告不规范值。
- 旧状态不规范时，Conductor 在 Resume 后、下一次 Dispatch 前完成一次规范 State Commit；不得让 Update 或 Insight 静默猜测映射。
