---
name: project-memory
description: 维护长期 Project Document、多个 persisted Work 与恢复索引，支持跨 Session 恢复、Work 切换和收尾。
version: 4.0.0
---

# Project Memory Skill

## vNext Reference Routing

- 设计 Memory 生命周期、去重和 Regression 时，读取 `framework://references/01-standards/self-improving-memory.md` 的相关 Section。
- 设计有限 Context Recovery 或处理 Context Loss 时，读取 `framework://references/01-standards/context-engineering.md` 的 JIT、Compaction 和 Scratchpad Section。

## Truth Model

| Document / Store | Memory Type | Update Moment |
|---|---|---|
| `project://docs/PRODUCT.md` | Stable Product Fact / Rule / Boundary | 事实确认后 |
| `project://docs/ARCHITECTURE.md` | Current Structure / Interface / Constraint | 实现验证后 |
| `project://docs/DECISIONS.md` | Confirmed Major Decision | 用户确认后 |
| `project://docs/BACKLOG.md` | 未激活 Request / Deferred Item | 尚未形成独立 Work 时 |
| `project://docs/works/<work-id>.md` | Persisted Work Contract + Active Workspace | Work create / state / progress 变化时 |
| `project://docs/STATUS.md` | Focus + focused Work Recovery Projection | Focus / checkpoint 变化时 |
| `project://docs/MEMORY.md` | Reusable Finding / Pitfall / Preference / Convention | 有稳定证据时 |
| `project://docs/WORK.md` | Legacy single-work compatibility | 只读恢复直到迁移 |

## Resume

1. 先读 `project://docs/STATUS.md`。
2. 有 `focus` 时只读 `project://docs/works/<focus>.md` 的 Goal、Acceptance、Current Task、Verification、Next Action、Blocker。
3. 用户点名另一个 Work 时，只读取目标 Work 的最小恢复 Context；不要全量加载其它 Works。
4. STATUS 无 focus 且 legacy WORK 有旧 checkpoint 时进入 compatibility resume。
5. 根据当前 Request 只检索相关 Product、Architecture、Decision 与 Memory Section。
6. 区分 Verified Fact、User-confirmed Decision、Hypothesis、Historical Note。

## Work Discovery

`project://docs/works/` 本身就是 registry，不建立第二个 Work Registry 对象。需要帮助用户选择 Work 时，可读取 active-store 中每个文件的 frontmatter + Goal 摘要，但不得默认加载完整 body。

Phase 1 最多一个 active Work；其它 Work 可以 ready / paused / blocked。

## Checkpoint

Checkpoint 属于每个 Work 自己：Current Task、Latest Result、Verification、Open Findings、Next Action / Blocker。STATUS 只保存 focus 与 focused Work 的派生恢复 projection，不复制完整 Work。

## Distill

单个 Work 收尾且尚未报告完成时：

1. 更新真实 Project Fact，而不是保留过时描述。
2. 合并重复 Memory；保留最小 Reproduction、Verified Cause、Prevention Rule。
3. 重大 Decision 写入 DECISIONS，并标记被 Supersede 的旧 Decision。
4. 未激活 Future Item 写入 BACKLOG；其它 persisted Work 不修改。
5. 只有有长期价值的完成摘要才进入 `project://docs/works/archive/`。
6. 在 `Open Findings = 0` 且长期信息已归位后，向 Conductor 返回删除当前 `docs/works/<id>.md` 并更新 STATUS focus 的 Distill 提案。
7. 不再“清空全部 WORK / STATUS”；只完成当前 Work。没有下一个 focus 时 STATUS 回到 no active work。

## Legacy Migration

Legacy v4 的 `project://docs/WORK.md` 不由 Update 自动迁移。下一次 Conductor 能可靠识别 Work id 时，把它的 Goal、Scope、Acceptance、Current Task、Latest Result、Open Findings、Work Learnings、Verification、Next Action 原语义写入 `docs/works/<id>.md`，再切换 STATUS 到新格式。无法可靠识别 identity 时不得猜测。

## State Ownership

本 Skill 可以维护长期 Project Document，但 persisted Work / STATUS 的 Activation、Checkpoint、Pause、Resume、Switch 与 Completion 只产生 `work_updates`，不得由 Specialist 直接提交；Conductor 是唯一正式 State Writer。

## Exclusions

默认不保存完整 Session、Chain-of-thought、所有 Agent 输出、全部 Event、Graph、无证据猜测、一次性命令日志或第二套 Work Registry。