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

## State Ownership and Commit Points

Conductor 是 `project://docs/WORK.md` 与 `project://docs/STATUS.md` 的唯一正式 State Writer。Specialist 可以修改其职责内的 Product Artifact、Code、Test 与长期 Document，但对 Active Work 只返回 Focused Result 和建议的 `work_updates`，不得直接决定或写入正式 Workflow / Stage / Agent / Current Task / Latest Result / Open Findings 状态。

Conductor 必须在这些 Commit Point 同步维护 Work 与 Status：Work activation、Dispatch 前、Focused Result 返回后、Stage transition、Pause、Resume、Completion / Distill。一个 LLM 顺序切换 Persona 时也适用；每次 Specialist role 结束必须先回到 Conductor commit，才能进入下一个 role。

`project://docs/STATUS.md` 不保存 visualization revision。Insight 对已落盘状态维护自己的 transition index、trace、gap 和 coverage，不能反向写 Project State。

## Pause and Resume

- Pause 不是 Completion：不得归档、Distill 或清空 `project://docs/WORK.md`。
- Pause 前覆盖 `Current Task` 与 `Latest Result`，记录已完成内容、Verification、Risk 和唯一 Next Action；未解决义务继续留在 `Open Findings`。
- 将 `STATUS.md` 的 `work_state` 设为 `paused`，保留 Work、Workflow、Stage，并将 Agent state 设为 `paused`。
- 下次 Session 读取该 Checkpoint；用户继续原 Work 时将 `work_state` 恢复为 `active`，从 Next Action 继续。
