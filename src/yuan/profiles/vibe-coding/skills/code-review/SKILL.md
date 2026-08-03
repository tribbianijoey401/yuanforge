---
name: code-review
description: 独立审查变更的规格符合性、缺陷、安全、回归和测试充分性。
---

# 代码审查

读取已确认 Work、当前 Artifact Digest、diff、相关调用链和测试。优先报告会导致错误结果、数据损坏、安全问题或不可恢复行为的发现。每项发现必须包含位置、触发条件、影响和证据；不把个人风格偏好当缺陷。逐条映射 Acceptance Criteria，并记录至少一个已尝试的对抗场景。存在必需修正时输出 `NEEDS_WORK` Handoff；否则输出绑定当前 Artifact 和 Evidence 的 `READY` Handoff。Artifact 变化后旧审查不得复用。
