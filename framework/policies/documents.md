# Project Document Policy

| Document | 唯一职责 |
|---|---|
| `project://docs/PRODUCT.md` | 稳定 Product Fact、Target User、Business Rule 与 Boundary |
| `project://docs/ARCHITECTURE.md` | 当前 System Structure、Module、Interface 与 Constraint |
| `project://docs/DECISIONS.md` | 已确认的重大 Product / Architecture Decision |
| `project://docs/BACKLOG.md` | 未激活 Request 与 Deferred Item |
| `project://docs/WORK.md` | 唯一 Active Work、Scope、Acceptance、Plan 与 Progress |
| `project://docs/STATUS.md` | 短小的跨 Session Recovery Checkpoint |
| `project://docs/MEMORY.md` | 可复用 Pitfall、Verified Finding、Preference 与 Convention |

`STATUS` 的恢复信息进入 Status，`PROGRESS` 进入 Work / Status，复杂 Task Board 按需嵌入 Work。Event、Graph 和完整 Role Output 不进入 vNext 默认 Memory。

重大 Product 与 Architecture Decision 写入前需要用户确认。普通 Status 和已验证技术结论由 Yuan 自动维护。Work 收尾时先 Distill 并去重合并长期信息，再将 `project://docs/WORK.md` / `project://docs/STATUS.md` 同时清为 no active work，最后才报告完成；只有有价值的精炼摘要才进入 `project://docs/work/archive/`。

激活新 Work 时，`project://docs/WORK.md` 与 `project://docs/STATUS.md` 必须在同一逻辑步骤中作为一个状态变更维护：STATUS 至少写入 Work id、`work_state: active`、Workflow、Stage 和当前 Agent。Active Work 不得只写入 WORK，否则恢复与 Insight 只能把缺失字段报告为 Unknown。

## Write Standard

七类 Document 只沉淀「看产物本身看不出来」的长期信息：

- **写入**：设计哲学与心智模型、重大 Decision 及其 Why、跨 Module 契约口径、废弃/禁区约定、非显而易见的 Convention、重要历史节点（带绝对日期）。
- **不写入**：产物可自证的清单与目录结构、Git History 可查的变更、一次性状态（当前 TODO）、通用常识、单个 Bug 的修复细节。
- **触发时机**：出现新心智模型、结构/契约调整或长期约定时主动提议写入；先列修改点，重大内容经用户确认后落盘。
- **设计边界**：为什么这么「做」（方案/结构）归 ARCHITECTURE / DECISIONS；为什么这么「呈现」（视觉/体验方向）归 PRODUCT 的 Design Direction 与其引用的设计产物。

## State Ownership and Commit Points

Conductor 是 `project://docs/WORK.md` 与 `project://docs/STATUS.md` 的唯一正式 State Writer。Specialist 可以修改其职责内的 Product Artifact、Code、Test 与长期 Document，但对 Active Work 只返回 Focused Result 和建议的 `work_updates`，不得直接决定或写入正式 Workflow / Stage / Agent / Current Task / Latest Result / Open Findings 状态。

所有正式字段的 Canonical Source、可选 `agent.instance` 与组合约束见 `framework://policies/state-contract.md`。具体动作只写入 WORK 的 Current Task。Conductor 每次写入后运行 `framework://tools/state_guard.py`；未输出 `STATE_VALID` 的 checkpoint 不构成可继续 Dispatch 的 State Commit。

Conductor 必须在这些 Commit Point 同步维护 Work 与 Status：Work activation、Dispatch 前、Focused Result 返回后、Stage transition、Pause、Resume、Completion / Distill。一个 LLM 顺序切换 Persona 时也适用；每次 Specialist role 结束必须先回到 Conductor commit，才能进入下一个 role。

`project://docs/STATUS.md` 不保存 visualization revision。Insight 对已落盘状态维护自己的 transition index、trace、gap 和 coverage，不能反向写 Project State。

## Pause and Resume

- Pause 不是 Completion：不得归档、Distill 或清空 `project://docs/WORK.md`。
- Pause 前覆盖 `Current Task` 与 `Latest Result`，记录已完成内容、Verification、Risk 和唯一 Next Action；未解决义务继续留在 `Open Findings`。
- 将 `STATUS.md` 的 `work_state` 设为 `paused`，保留 Work、Workflow、Stage，并将 Agent state 设为 `paused`。
- 下次 Session 读取该 Checkpoint；用户继续原 Work 时将 `work_state` 恢复为 `active`，从 Next Action 继续。
