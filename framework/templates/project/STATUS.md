---
focus: null
work: null
work_state: idle
workflow: null
stage: null
agent:
  id: null
  instance: null
  state: null
quality:
  test: pending
  review: pending
---

# Project Recovery Index

## Current Situation

## Last Completed

## Next

## Blocker

<!--
STATUS 是 Project-level Recovery Index，不是第二份 Work State。

`focus` 指向 `project://docs/works/<work-id>.md` 的文件名 stem；一次交互只 focus 一个 Work。
当 focus 非空时，work/work_state/workflow/stage/agent/quality 只是 focused Work 的派生投影，
用于快速恢复与兼容现有观察工具；Canonical State 永远以对应 Work 文件为准，Conductor
必须在同一逻辑步骤同步写入并由 State Guard 校验一致。

Phase 1 允许 Project 同时持久化多个 Work，但最多一个 Work 为 active。其它 Work 可为
ready / paused / blocked。暂停时保留全文，work_state 投影为 paused，
Agent state 为 paused；完成一个 Work 不清空其它 Work。

`work_state: idle` 只表示当前没有 focus，不是任何 Work 文件的生命周期状态。
STATUS 不保存 visualization revision。
-->