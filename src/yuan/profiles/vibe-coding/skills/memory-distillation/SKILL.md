---
name: memory-distillation
description: 从已验证 Work、Evidence 与 Handoff 创建可追溯、追加式的项目长期记忆。
---

# 长期记忆蒸馏

1. 只提取能被当前 Work、PASS Evidence、Artifact 或 Handoff 支持的稳定事实。
2. 选择 `feature`、`decision`、`pitfall`、`module` 或 `convention`；同一知识使用稳定 Memory ID，变化时追加 Revision，不覆盖旧记录。
3. 用 `memory template` 自动绑定 Work Digest、Evidence、Artifact、Ledger Head 和可选文件 Binding；编辑后运行 `memory check`。
4. 运行 `memory record`，再运行 `memory status` 和 `memory rebuild`，确认 JSON 与 Markdown 索引可重建。
5. 没有长期影响时不得制造空洞记录；在 Memory Curator Handoff 中写明 `NO_MEMORY_CHANGE` 和证据化理由。
