# 风险与审查规则

- `R0 高风险`：认证、权限、支付、密钥、数据删除、迁移、生产发布。Routing 必须包含 Architect、Design Reviewer、Spec Reviewer、Security Auditor、Quality Auditor 与 Tester。
- `R1 标准风险`：常规功能、API、持久化和依赖升级。Routing 至少包含 Spec Reviewer 与 Tester。
- `R2 低风险`：文档、小型样式、非行为配置。Routing 仍包含 Tester；允许同一 LLM 顺序切换角色，但必须形成独立 Handoff。

风险来自已确认 Intake，并由 Kernel 根据 Profile Workflow 生成唯一 Routing。LLM 不得手工降级风险或删除角色；如用户要求降低风险，必须修改理由并重新确认 Intake。Reviewer 的目标是尝试证伪，而不是确认实现者的叙述；每份审查至少记录一个边界条件或失败路径。
