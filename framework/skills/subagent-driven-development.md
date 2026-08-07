---
name: subagent-driven-development
description: Platform 支持 Independent Agent 且 Work 可安全拆分时，提供 Context-isolated Analysis、Review 或顺序 Implementation Slice。
version: 4.0.0
---

# Subagent Collaboration Skill

## vNext Reference Routing

- 控制 Subagent Context 时，读取 `references/01-standards/context-engineering.md` 的 JIT 与 Context Isolation Section。
- 需要 Independent Reviewer 时，读取 `references/01-standards/verifier-critic-pattern.md` 的 Actor / Checker Separation 与 Input Boundary Section。

## Activation

只有满足以下任一条件才使用：

- Complex Bug 需要独立 Failure Model
- Material Change 需要 Independent Review
- Large Work 可拆成无写入冲突的只读分析
- 不同 Implementation Slice 可以严格顺序交接

Small Change、单文件低 Risk 修改或共享 Context 已足够时不启动 Subagent。

## Rules

1. Conductor 选择 Agent Contract，Agent 再加载自己的 Skill。
2. 每个 Subagent 只接收 Work 摘要、相关 Artifact、禁止项、产出和 Verification。
3. 默认只有一个 Writer；多个 Agent 不并行修改同一 Workspace 或耦合 Artifact。
4. Reviewer 不接收 Writer 的完整推理，只接收 Requirement、Diff、Test 和必要 Context。
5. Handoff 使用 Focused Output；不得把全部历史注入下一个 Agent。
6. Platform 不支持真正隔离时改用 `role-switch`，并明确不是 Independent Review。

## Output

- Agent Assignment 与隔离理由
- Focused Context Packet
- Handoff Conclusion / Evidence / Risk / Next Action
