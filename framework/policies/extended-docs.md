# Extended Document Profile

本 Policy 只在 `project://docs/WORK.md` 已无法清晰承载 Complex Work、且 Conductor 明确选择 Extended Profile 时启用。默认 Project Document 仍以 `framework://policies/documents.md` 的七类文件为准。

## Optional Task Board

Complex Work 可以在 `project://docs/WORK.md` 内增加 Task Board，字段最少包含：

| ID | Outcome | Owner Agent | Dependency | Status | Evidence | Next Action |
|---|---|---|---|---|---|---|

Task Board 不是第二个 Work Truth Source。Goal、Scope、Acceptance 与 Risk 仍由 `project://docs/WORK.md` 的主段落定义；Task 完成必须引用 Evidence，不以角色口头状态替代。

## Work Archive

只有满足以下条件的完成摘要才写入 `project://docs/work/archive/`：

- 后续维护需要理解关键实现边界或 Migration；
- 包含可复用的验证路径但不适合放入通用 Memory；
- 需要保留对已 Supersede Decision 的历史解释。

Archive 只保存精炼摘要，不复制完整 Session、Agent Output、Event 或 Tool Log。

## Explicit Non-default Assets

Graph、Event、Proposal、Session Folder、独立 `PROGRESS` 和固定 Frontmatter Schema 不属于 vNext MVP。只有真实 Project 规模证明七类 Document 无法满足检索或协作成本时，才能另行提出 Extended Profile Decision。
