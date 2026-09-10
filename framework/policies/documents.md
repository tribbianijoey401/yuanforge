# Project Document Policy

Yuan 的 Project Memory 分为长期 Project Truth、多个持久化 Work，以及一个短小 Recovery Index。

| Document / Store | 唯一职责 |
|---|---|
| `project://docs/PRODUCT.md` | 稳定 Product Fact、Target User、Business Rule 与 Boundary |
| `project://docs/ARCHITECTURE.md` | 当前 System Structure、Module、Interface 与 Constraint |
| `project://docs/DECISIONS.md` | 已确认的重大 Product / Architecture Decision |
| `project://docs/BACKLOG.md` | 尚未激活成独立 Work 的 Request 与 Deferred Item |
| `project://docs/works/<work-id>.md` | 一个独立持久化 Work 的 Goal、Scope、Acceptance、Workflow State 与 Active Workspace |
| `project://docs/STATUS.md` | 当前 focus 与 focused Work 的短 Recovery Projection |
| `project://docs/MEMORY.md` | 可复用 Pitfall、Verified Finding、Preference 与 Convention |
| `project://docs/WORK.md` | v4 legacy single-work compatibility；新模型不再作为 canonical Work State |

`project://docs/works/` 本身就是 Work Registry：文件存在表示该 Work 仍是持久化中的当前工作，不再额外维护一个 Work Registry 对象。复杂 Task Board 按需嵌入对应 Work 文件；Event、Graph 和完整 Role Output 不进入默认 Memory。

重大 Product 与 Architecture Decision 写入前需要用户确认。普通 Work State 和已验证技术结论由 Yuan 自动维护。

## Multi-Work Boundary

- 一个 Project 可以同时持久化多个 Work。
- Phase 2 单 active Work 保持 Phase 1 兼容；多个 active Work 仅限每个 Work 都有唯一 `execution.mode: isolated`、Platform workspace 与真实独立 `agent.instance`。
- `STATUS.focus` 必须是其中一个 active Work，表示本次交互正在正式恢复/操作哪个 Work，不代表唯一 active Work，也不关闭其它 Work。
- 与当前 Request 无关但已经形成明确 Goal / Scope / Acceptance 的独立工作，可以成为新的非 focused `ready` Work；只是未来想法或未成形需求仍进入 BACKLOG。
- 不引入 Scheduler、Worker Pool、后台 Daemon、branch/worktree 自动调度或多个并行 Writer。

## Work Activation and State Commit

激活或切换 Work 时，focused `project://docs/works/<work-id>.md` 与 `project://docs/STATUS.md` 必须在**同一逻辑步骤**作为一个 State Commit 维护。STATUS 继续写入兼容恢复投影：Work id、`work_state: active`、Workflow、Stage 和当前 Agent，但这些字段的 Canonical Source 是 focused Work 文件，不是 STATUS 本身。

创建一个不立即执行的非 focused `ready` Work 时，只写新的 Work 文件即可；不得抢占当前 focus。

Conductor 是 `project://docs/works/*.md` 与 `project://docs/STATUS.md` 的**唯一正式 State Writer**。Specialist 可以修改职责内的 Product Artifact、Code、Test 与长期 Document，但只返回 Focused Result 和建议的 `work_updates`，不得直接决定或写入正式 Workflow / Stage / Agent / Current Task / Latest Result / Open Findings 状态。

所有正式字段的 Canonical Source、可选 `agent.instance`、focus projection 与组合约束见 `framework://policies/state-contract.md`。具体动作只写入 focused Work 的 Current Task。Conductor 每次写入后运行 `framework://tools/state_guard.py`；未输出 `STATE_VALID` 的 checkpoint 不构成可继续 Dispatch 的 State Commit。

Conductor 必须在这些 Commit Point 维护当前 Work 与 Status：Work activation、Focus switch、Dispatch 前、Focused Result 返回后、Stage transition、Pause、Resume、Block/Unblock、Completion / Distill。一个 LLM 顺序切换 Persona 时也适用；每次 Specialist role 结束必须先回到 Conductor commit，才能进入下一个 role。

`project://docs/STATUS.md` 不保存 visualization revision。Insight 对已落盘状态维护自己的 transition index、trace、gap 和 coverage，不能反向写 Project State。

## Pause and Resume

- Pause 不是 Completion：**不得归档**当前 Work。
- Pause 前覆盖该 Work 的 Current Task 与 Latest Result，记录已完成内容、Verification、Risk 和唯一 Next Action；未解决义务继续留在 Open Findings。
- 将 Work frontmatter `state` 设为 `paused`，并把 `STATUS.md` 的 focused `work_state` 投影同步设为 `paused`；保留当前 Workflow / Stage，当前 Agent state 设为 `paused`。
- 暂停时保留全文；**不得归档或清空**该 Work。其它 persisted Work 完全不受影响。
- 下次 Session 读取 `STATUS.focus` 与对应 Work；用户继续时在 Dispatch 前恢复为 `active`，从 Next Action 继续。

## Switch

切换 focus 或正式执行到另一个 Work 时：

1. 单 active Work 时，先完成、Pause 或 Block，并形成可恢复 Checkpoint；多个合法 isolated active Work 时可直接在 active Work 间切换 focus。
2. 将 `STATUS.focus` 指向目标 Work 并同步该 Work 的 projection；切换不是 Completion。
3. 目标 Work 可以保持 `ready` / `paused` / `blocked` 用于讨论或恢复；仅在即将 Dispatch 时切到 `active`。
4. 同步 STATUS recovery projection 并通过 State Guard。
5. `review_context`、临时 Writer Context 与未提交 Attempt 不得跨 Work 携带。

## Completion and Distill

一个 Work 满足 Acceptance、必要 Verification、Risk-driven Review 且 `Open Findings = 0` 后：

1. Distill 只处理当前完成的 Work；稳定 Fact / Decision / Pitfall 写回长期 Project Document。
2. 不属于这个 Work 的未来事项进入 BACKLOG；其它 persisted Work 不修改。
3. 只有有长期历史价值的完成摘要才进入 `project://docs/works/archive/`。
4. 移除当前 `project://docs/works/<work-id>.md`，而不是清空整个 Project 的 Work State。
5. 若用户明确继续另一个 persisted Work，可把 `STATUS.focus` 切到它；否则清为 `focus: null` / `work_state: idle`，即 **no active work**。
6. 最后才报告这个 Work 完成。

## Write Standard

长期 Document 只沉淀「看产物本身看不出来」的信息：

- **写入**：设计哲学与心智模型、重大 Decision 及其 Why、跨 Module 契约口径、废弃/禁区约定、非显而易见 Convention、重要历史节点。
- **不写入**：产物可自证的目录清单、Git History 可查变更、一次性 TODO、通用常识、单个 Bug 的完整操作日志。
- **设计边界**：为什么这么“做”归 ARCHITECTURE / DECISIONS；为什么这么“呈现”归 PRODUCT 的 Design Direction 与其引用的设计产物。

## Legacy WORK.md

`project://docs/WORK.md` 保留是为了让旧 v4 Project 能安全 update / resume。新 Work 不再写入该文件。旧 Project 在下一次可可靠识别 Work id 的 Conductor State Commit 时，按 `framework://policies/state-contract.md` 迁入 `project://docs/works/<work-id>.md`；Framework Update 本身不迁移 Project-owned 内容。
