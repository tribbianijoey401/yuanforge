# 能力边界规则

1. 用户意图是 Work 的来源，Work Contract 是当前执行边界，工具输出是事实来源。
2. 用户意图必须先固化为已确认 Intake；完整 Work 必须再次确认。开放平台中的确认是可审计对话回执，不冒充密码学签名。
3. 不得用 Rules、Agent 结论或 Skill 步骤替代 Attempt、Evidence、Role Handoff 或 Reducer。
4. 只在声明的 Artifact Scope、Grant 和 Budget 内行动；越界返回 `WAIT_AUTH` 或 `BLOCKED`。
5. 不得伪造命令、测试、截图、哈希、确认、审查或外部系统结果。
6. 遇到未知副作用，记录 `UNKNOWN` 并执行只读 Reconciliation；不得盲目重试。
7. 项目自身规则可以补充工程偏好，但不能降低 Core 的完成条件。
