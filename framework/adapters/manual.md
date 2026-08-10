# Manual Adapter

当 Platform 不自动读取 `AGENTS.md`、不支持 Skill API 或没有 Subagent 时，Yuan 仍可通过普通文件读取顺序运行。

## Start

1. 把 `project://AGENTS.md` 作为主指令提供给 Agent。
2. 解析 Framework Root：普通 Project 选择 `project://.yuan/framework/`；Yuan Source Repository 自身选择 `project://framework/`。
3. 读取 `project://docs/STATUS.md` 与当前 `project://docs/WORK.md`，再按 Request 加载相关 Document Section。
4. 读取 `framework://policies/core.md`、`framework://policies/routing.md` 和选中的 `framework://workflows/*` Primary Workflow。

## Role Execution

1. Conductor 根据 Routing 选择 Agent Contract。
2. 读取 Agent 顶部的 `Skill Assignment`。
3. 只读取当前动作所需的 Skill。
4. Skill 根据 `Reference Routing` 决定是否读取 Reference Section。
5. 角色结束时输出 Focused Handoff；下一角色只接收 Work、相关 Artifact 和 Handoff。

不支持真正 Independent Agent 时，同一个 LLM 顺序切换 Persona，并明确 Review 不是独立 Context。不要通过用户 Prompt 手工指定每个内部节点；仍由 Conductor 自动决定何时切换。

## Recovery

Manual Mode 不依赖 Daemon、Lock、Ledger 或 Runtime Process。中断前由 Conductor 更新 `project://docs/STATUS.md`，下次从 Status、Active Work 和相关 Memory Section 恢复。
