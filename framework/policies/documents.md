# Project Document Policy

| Document | 唯一职责 |
|---|---|
| `PRODUCT.md` | 稳定 Product Fact、Target User、Business Rule 与 Boundary |
| `ARCHITECTURE.md` | 当前 System Structure、Module、Interface 与 Constraint |
| `DECISIONS.md` | 已确认的重大 Product / Architecture Decision |
| `BACKLOG.md` | 未激活 Request 与 Deferred Item |
| `WORK.md` | 唯一 Active Work、Scope、Acceptance、Plan 与 Progress |
| `STATUS.md` | 短小的跨 Session Recovery Checkpoint |
| `MEMORY.md` | 可复用 Pitfall、Verified Finding、Preference 与 Convention |

`STATUS` 的恢复信息进入 Status，`PROGRESS` 进入 Work / Status，复杂 Task Board 按需嵌入 Work。Event、Graph 和完整 Role Output 不进入 vNext 默认 Memory。

重大 Product 与 Architecture Decision 写入前需要用户确认。普通 Status 和已验证技术结论由 Yuan 自动维护。Work 完成时先更新 Status，再去重、合并 Memory；只有有价值的精炼摘要才进入 `docs/work/archive/`。
