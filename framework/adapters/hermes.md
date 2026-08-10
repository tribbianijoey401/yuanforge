# Hermes Adapter

Hermes 使用 Project Root `AGENTS.md` 作为 Yuan 入口，并把 Platform Capability 映射到 vNext Workflow。

## Capability Mapping

| Yuan Capability | Hermes Mapping | Degradation |
|---|---|---|
| 读取 Project Document | File Read | 只读取 Status、Active Work 与相关 Section |
| Implementation | File / Shell Tool | 由一个 Writer 修改当前 Workspace |
| Independent Analysis / Review | Platform 原生 Agent/Fork 能力 | 不可用时顺序 Persona Switch，并声明共享 Context |
| Skill Loading | 读取选中 Skill 文件 | 不依赖特定 Skill API；文件读取即可运行 |
| Verification | Shell / Test / Manual Evidence | 无自动 Test 时记录 Manual Verification 与限制 |
| Session Recovery | `project://docs/STATUS.md` + `project://docs/WORK.md` | 不依赖后台 Process 或 Runtime Lock |

## Rules

- 用户自然描述需求即可，不要求用户点名 Agent、Skill、Phase 或 Gate。
- Hermes 的 System Prompt、Hook 或 Tool 不能改变 `Routing → Agent → Skill → References` 的依赖方向。
- 不运行常驻 Yuan Runtime，不创建用于维持 Framework 状态的后台子进程。
- Platform Tool Timeout 时按 Platform 能力终止完整 Process Tree；结果不明时明确报告 Unknown，不假定成功并重复执行。
- 会话结束或中断前由 Conductor 更新 `project://docs/STATUS.md`；有稳定长期变化时更新对应 Project Document。
