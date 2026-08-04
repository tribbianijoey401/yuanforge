---
name: memory-retrieval
description: 在 Intake 和设计前检索相关项目长期记忆，并识别过期 Binding。
---

# 长期记忆检索

1. 运行 `memory resume --request <原始需求>`，先读取最新 `checkpoint/handoff` 的已完成、阻塞、下一步、待确认问题和恢复命令。
2. 检查 `memory_status`；不能把 stale Memory 当作当前事实，也不能把 `observed` 或 `hypothesis` 当作 `verified`。
3. 读取匹配记录的最新 Revision、类型、来源 Work/Evidence/Attempt 与 Relations；连续性说明“从哪里继续”，Ledger 说明“发生过什么”，长期 Memory 说明“以后应记住什么”。
4. 对会改变范围、安全、兼容或验收的历史决策，在 Intake 中明确引用 Memory ID/Digest；冲突时提出 Blocking Question。
5. 发现代码 Binding 已变化时，先以当前 Artifact 重新验证，再追加 Memory Revision；不得静默修改旧记录或派生 Markdown。
