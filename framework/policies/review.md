# Risk-driven Review Policy

Reviewer 不修改被审 Artifact，只输出 `READY` 或 `NEEDS_WORK`、Finding、Evidence、Affected Path 与 Residual Risk。

拼写、注释、格式化、纯文案或已有充分 Verification 的极小机械修改通常不需要独立 Reviewer。

Bug Fix、New Behavior、Multi-file Logic、Public Interface、Data Model、Authentication、Authorization、Concurrency、Cache、Migration、Dependency Upgrade、Architecture Change、Test Modification 或可信 Cross-module Impact 通常需要 Reviewer。

Platform 支持时，Material Review 使用 Independent Context；不支持时进行明确 Persona Switch，并如实说明共享 Context。
