---
id: PIT-003
object_type: pitfall
lifecycle: knowledge
owner: doc-engineer
status: resolved
confidence: verified
summary: 框架模板与项目实例文档混放会造成状态和职责混淆，应分离模板规格与项目 DocsOS。
severity: warning
type: process
cause: 设计时未区分框架自身文档与复制给项目的模板。
fix: 将模板保留在 .yuan/docs/ 规格书，项目状态写入 docs/。
---

# PIT-003: Docs 模板与实际文档混淆

模板属于 `.yuan/docs/`，项目运行时状态和长期知识属于 `docs/`。两者不得混写。
