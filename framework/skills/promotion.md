---
name: promotion
description: 把已验证的临时 Work 结论提升为稳定 Project Fact、Decision、Regression 或长期 Memory。
version: 4.0.0
---

# Memory Promotion Skill

## vNext Reference Routing

Candidate Knowledge 需要形成长期 Memory 或 Regression 时，读取 `references/01-standards/self-improving-memory.md` 的 Delta Evolution 与 Local Regression Section。

## Promotion Criteria

只有满足至少一个条件的信息才 Promotion：

- 用户确认的重大 Product / Architecture Decision
- Test、Repository Fact 或独立 Evidence 支持的稳定结论
- 已复现并验证 Cause 的可重复 Pitfall
- 后续 Work 会持续依赖的 Interface、Convention 或 User Preference
- 能防止同类 Regression 的最小测试或检查规则

## Destination

- Product Fact → `docs/PRODUCT.md`
- System Fact → `docs/ARCHITECTURE.md`
- Confirmed Decision → `docs/DECISIONS.md`
- Reusable Finding / Pitfall / Preference / Convention → `docs/MEMORY.md`
- Deferred Item → `docs/BACKLOG.md`

## Rejection

一次性日志、完整对话、无证据 Hypothesis、已被其他条目覆盖的信息和纯角色意见不 Promotion。Promotion 不建设 Graph、Event Ledger 或复杂 Proposal Pipeline。
