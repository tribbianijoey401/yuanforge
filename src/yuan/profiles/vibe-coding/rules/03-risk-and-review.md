# 风险与审查规则

- `R0 高风险`：认证、权限、支付、密钥、数据删除、迁移、生产发布。必须由 Architect、Security Auditor、Spec Reviewer、Tester 独立覆盖。
- `R1 标准风险`：常规功能、API、持久化和依赖升级。至少需要实现者之外的 Spec Review 与 Tester Evidence。
- `R2 低风险`：文档、小型样式、非行为配置。允许同一 Agent 顺序切换角色，但验证步骤必须独立记录。

Reviewer 的目标是尝试证伪，而不是确认实现者的叙述。每份审查至少记录一个边界条件或失败路径。
