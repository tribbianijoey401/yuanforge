---
name: project-memory
description: 维护七类 Project Document，支持跨 Session 恢复、长期知识积累和 Work 收尾。
version: 4.0.0
---

# Project Memory Skill

## vNext Reference Routing

- 设计 Memory 生命周期、去重和 Regression 时，读取 `references/01-standards/self-improving-memory.md` 的相关 Section。
- 设计有限 Context Recovery 或处理 Context Loss 时，读取 `references/01-standards/context-engineering.md` 的 JIT、Compaction 和 Scratchpad Section。

## Truth Model

| Document | Memory Type | Update Moment |
|---|---|---|
| `docs/PRODUCT.md` | Stable Product Fact / Rule / Boundary | 事实确认后 |
| `docs/ARCHITECTURE.md` | Current Structure / Interface / Constraint | 实现验证后 |
| `docs/DECISIONS.md` | Confirmed Major Decision | 用户确认后 |
| `docs/BACKLOG.md` | Inactive Request / Deferred Item | 与 Active Work 无关时 |
| `docs/WORK.md` | Single Active Work | Goal、Scope、Plan、Progress 变化时 |
| `docs/STATUS.md` | Short Recovery Checkpoint | 里程碑、中断、阻塞、Session 结束时 |
| `docs/MEMORY.md` | Reusable Finding / Pitfall / Preference / Convention | 有稳定证据时 |

## Resume

1. 先读 `STATUS.md`。
2. 有 Active Work 时读 `WORK.md` 的 Goal、Acceptance、Progress、Verification 和 Next Action。
3. 根据当前 Request 只检索相关 Product、Architecture、Decision 与 Memory Section。
4. 区分 `Verified Fact`、`User-confirmed Decision`、`Hypothesis` 和 `Historical Note`；Hypothesis 不得伪装成长期事实。

## Checkpoint

Checkpoint 保持短小，只写 Current State、Last Verified Result、Next Action、Blocker 和更新时间。不要复制完整 Work、聊天记录或角色输出。

## Distill

Work 结束时：

1. 更新真实 Project Fact，而不是保留过时描述。
2. 合并重复 Memory；保留最小 Reproduction、Verified Cause 和 Prevention Rule。
3. 重大 Decision 写入 `DECISIONS.md`，并标记被 Supersede 的旧 Decision。
4. 未完成且不属于 Active Work 的 Item 写入 `BACKLOG.md`。
5. 只有有长期价值的完成摘要才进入 `docs/work/archive/`。

## Exclusions

默认不保存完整 Session、Chain-of-thought、所有 Agent 输出、全部 Event、Graph、无证据猜测和一次性命令日志。
