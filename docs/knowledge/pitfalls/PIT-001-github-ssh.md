---
id: PIT-001
object_type: pitfall
lifecycle: knowledge
owner: doc-engineer
status: active
confidence: verified
summary: 在中国网络环境中，GitHub HTTPS 推送可能持续超时，应优先配置 SSH remote。
severity: blocker
type: env
cause: GitHub HTTPS 直连在中国境内不稳定。
fix: 使用 ed25519 密钥并将 origin 切换为 SSH 地址。
---

# PIT-001: GitHub 中国环境推送 443 超时

`git push` 到 GitHub 持续超时。优先使用 SSH remote，避免依赖不稳定的 HTTPS 直连。
