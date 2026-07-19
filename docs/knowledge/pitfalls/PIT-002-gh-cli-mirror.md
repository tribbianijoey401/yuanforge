---
id: PIT-002
object_type: pitfall
lifecycle: knowledge
owner: doc-engineer
status: active
confidence: verified
summary: 中国网络环境下载 gh-cli 可能很慢或校验失败，应优先使用可信国内镜像。
severity: warning
type: env
cause: GitHub 在中国境内没有稳定 CDN。
fix: 优先使用可信镜像源，必要时手动下载安装。
---

# PIT-002: gh-cli 国内下载极慢

`gh-cli` 下载速度可能极低，并出现 Content-Length mismatch。优先采用可信国内镜像。
