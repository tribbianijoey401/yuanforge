# Yuan vNext Framework

本目录是 Yuan 的 Canonical Framework Asset。它包含运行 Yuan 所需的 Agent、Skill、Policy、Workflow、Reference、Template 与 State Guard；Benchmark 等评估资产不属于本目录。

## 唯一依赖方向

```text
Conductor 读取 Policy 与 Workflow
→ Routing 选择 Agent
→ Agent 只加载自己声明的 Skill
→ Skill 只加载自己声明的 References Section
```

禁止以下反向或越层依赖：

- Conductor 直接加载 References；
- Agent 绕过 Skill 直接批量加载 References；
- Skill 调用 Agent；
- References 主动触发 Skill；
- 每轮预加载全部 Agent、Skill 或 References。

## 加载顺序

1. `framework://policies/core.md`；
2. `framework://policies/routing.md`；
3. `framework://policies/state-contract.md` 与只读 `framework://tools/state_guard.py`；
4. 当前 `framework://workflows/*` Primary Workflow；
5. Routing 选中的 `framework://agents/*` Agent Contract；
6. Agent Contract 声明的 `framework://skills/*` Skill；
7. Skill 中 `Reference Routing` 命中的 `framework://references/*` 或 `skill://references/*` Section；
8. `framework://` 解析时自动优先采用相同相对路径的 Project Override。

`project://`、`framework://`、`skill://` 是逻辑定位符，不是目录名、环境变量或 URL。调用文件 Tool 前必须先解析为真实路径。

## Multi-Work State

Phase 1 把 Work 作为执行隔离边界：

```text
project://docs/works/
├── W-101.md
├── W-102.md
└── W-103.md

project://docs/STATUS.md
└── focus + focused Work recovery projection
```

- `docs/works/<work-id>.md` 是一个 persisted Work 的 canonical state；目录本身就是 Registry，不建立第二套 Work Registry。
- 一个 Project 可以存在多个 `ready` / `paused` / `blocked` Work，但 Phase 1 最多一个 `active` Work。
- `STATUS.focus` 只表示本次 interaction 正在恢复/操作哪个 Work；STATUS 中 `work/work_state/workflow/stage/agent/quality` 是 focused Work 的恢复投影，不是第二份 Truth Source。
- `project://docs/WORK.md` 仅保留旧 v4 single-work compatibility；Framework Update 不静默迁移旧状态，下一次可靠 Conductor State Commit 才迁移。
- Multi-Work 不引入 Scheduler、Worker Pool、后台 Daemon、自动 branch/worktree 调度或多个并行 Writer。

## State Commit Guard

Conductor 每次 Work create/focus/activate、Dispatch、Focused Result、Stage/Agent 转换、Pause、Resume、Block/Unblock、Switch 与 Distill 后都运行 `state_guard.py check`。

Guard 从当前 Workflow frontmatter 与 Agent Contract 文件名动态取得合法 Stage / Agent ID，并验证：

- 每个 persisted Work 的 id / state / workflow / stage / agent 组合；
- Phase 1 最多一个 `active` Work；
- 有 active Work 时它必须是 `STATUS.focus`；
- STATUS projection 必须与 focused Work 一致；
- active Work 必须有 Current Task；paused Work 必须有 Next Action；blocked Work 必须有 Blocker。

校验未输出 `STATE_VALID` 时不得继续 Dispatch。具体动作只保存在当前 Work 的 Current Task；Persona/Subagent/Session 标签可使用 `agent.instance`，但不改变规范路由身份。
