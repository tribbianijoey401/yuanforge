# Work Contract Template

> Canonical persisted Work path: `project://docs/works/<work-id>.md`.
> Conductor creates a Work by prepending the canonical frontmatter described in
> `framework://policies/state-contract.md` to this body. `project://docs/WORK.md`
> is retained only as a legacy v4 compatibility file and is not the multi-work
> canonical state source.
>
> Phase 2 keeps a single active Work compatible with Phase 1: omit `execution`
> unless concurrent execution is actually Platform-provided. When two or more
> Works are active, every such Work must include `execution.mode: isolated` and
> a unique `execution.workspace`, plus a unique real `agent.instance`. The
> Framework validates identities only; it never creates worktrees or schedules
> the lanes.

## Goal

## Scope

## Non-goals

## Acceptance

- [ ] 可观察结果与验证方式

## Assumptions and Risks

## Plan

<!-- 只写当前 Work 需要的步骤。Complex Work 可在此增加 Task Board。 -->

---

# Active Workspace

> Active Workspace 是这个 Work 自己的 State，不是 Project History。Current Task 与
> Latest Result 每次覆盖；Open Findings 只保存未解决义务；Work Learnings 只保存后续
> 仍需的当前认知。暂停时保留全文，并把 Current Task / Latest Result / Next Action
> 更新为可直接恢复的 Checkpoint；不得归档或清空这个 Work。完成时 Distill 当前 Work，
> 只移除/归档这个 Work，不影响 `docs/works/` 中其它持久化 Work。

## Current Task

<!-- 当前派发 Agent 的唯一任务：Agent、Done Conditions、Declared Context Refs。新 Agent 派发时覆盖。 -->

## Latest Result

<!-- 上一 Agent Focused Result 被 Conductor 消费后的交接摘要：Outcome、Summary、skills_applied、Verification、Risks、Next。下一 Result 来时覆盖。 -->

## Open Findings

<!-- 当前 Work 完成前仍必须处理的未解决义务。解决并验证后删除；不影响当前 Acceptance 的改善项进 BACKLOG。 -->

## Work Learnings

<!-- 当前 Work 后续步骤仍需依赖的已验证/排除事实。可 merge / replace / compress / discard。 -->

## Next Action

<!-- paused 时必须存在唯一、可直接恢复的下一动作；active / ready 时可为空。 -->

## Blocker

<!-- blocked 时说明无法继续的事实、缺失 Authority 或外部依赖。 -->
