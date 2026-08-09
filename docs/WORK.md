# Active Work

## Goal

让所有 Workflow 支持用户主动 Pause，并让高频 Update 明确报告每个未升级的 Project-owned 路径及保留原因。

## Scope

- 定义用户说“先离开、挂起工作”等自然语言时的 Pause/Resume 行为。
- Pause 保存可恢复 Checkpoint、停止派发，不归档、不 Distill、不清空 Work。
- Update 继续直接替换所有 Yuan-managed 资产。
- Update 输出实际存在且被保留的 Project-owned 文件/目录及原因。
- 增加 Installer 与 Framework Contract Regression。

## Non-goals

- 不建立 Runtime、Daemon 或新的状态存储。
- 不迁移、解释或覆盖 Project Documents。
- 不自动把 Active Work 判定为完成。

## Acceptance

- [ ] 四个 Primary Workflow 都声明统一的 Pause/Resume 行为。
- [ ] 用户提出离开或挂起时，Conductor 保存 Checkpoint 并停止继续派发。
- [ ] Update 输出每个保留路径及其原因，同时替换全部 Yuan-managed 资产。
- [ ] Project-owned 内容在 Update 后字节不变。
- [ ] 完整 Test、Framework Check 与真实 Project dry-run 通过。

## Assumptions and Risks

- `STATUS.work_state` 是 Update 唯一读取的 Project 状态字段。
- 保留清单只报告 Yuan 知道且主动保留的 Project-owned 路径，不枚举所有业务源码。

## Plan

1. 建立 Pause 与 Update reporting 的失败测试。
2. 实现统一 Contract 与 Installer 输出。
3. 执行完整 Regression 和真实 Project 验证。
4. Distill 后清空 Active Work。

---

# Active Workspace

## Current Task

Backend Dev：实现 Update preserved-path reporting，并同步统一 Pause Contract。

## Latest Result

已确认当前 Update 会保留 Project 内容，但只输出概括，不逐项说明实际保留路径。

## Open Findings

- Pause 尚未成为所有 Workflow 的显式行为。
- Update 尚未输出逐项保留清单与原因。

## Work Learnings

- `sync_project.py` 只是 `yuanforge-init` 的转发入口，核心行为只需在 Installer 实现一次。
