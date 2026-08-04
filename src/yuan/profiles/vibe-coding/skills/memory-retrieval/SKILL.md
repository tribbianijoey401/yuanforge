---
name: memory-retrieval
description: 在 Intake 和设计前检索相关项目长期记忆，并识别过期 Binding。
---

# 长期记忆检索

1. 运行 `memory status`，不能把 stale Memory 当作当前事实。
2. 运行 `memory context --request <原始需求>`，读取匹配记录的最新 Revision、来源 Work/Evidence 与 Relations。
3. 对会改变范围、安全、兼容或验收的历史决策，在 Intake 中明确引用 Memory ID/Digest；冲突时提出 Blocking Question。
4. 发现代码 Binding 已变化时，先以当前 Artifact 重新验证，再追加 Memory Revision；不得静默修改旧记录。
