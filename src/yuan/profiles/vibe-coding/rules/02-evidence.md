# Evidence 规则

1. 每项 Required Criterion 必须绑定可执行 Verifier，并至少产生一项正数断言。
2. Evidence 必须绑定 Work Revision、Attempt、Artifact Digest、Verifier Closure 和真实回执。
3. 测试退出码为零不自动等于功能正确；断言必须覆盖 Criterion 描述的行为。
4. 实现者的自述不是独立 Evidence。高风险或完整档位使用独立 Reviewer/Verifier。
5. Mock 只证明隔离逻辑；涉及数据库、网络、权限、构建或部署的结论需要相应层级的集成验证。
6. 过期、越域、来源不明、断言为空或工作区污染后的 Evidence 一律无效。
7. Role Handoff 不是 Acceptance Evidence；它证明角色职责已履行。Artifact Reviewer 的 Handoff 必须引用当前 Evidence，并随 Artifact 变化而过期。
