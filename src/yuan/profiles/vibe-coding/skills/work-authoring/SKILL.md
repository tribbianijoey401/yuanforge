---
name: work-authoring
description: 把自然语言需求转换成 Yuan Work Contract、范围、预算、授权和可执行验收标准。
---

# Work 编写

1. 输入必须是已确认 Intake 和由 `capability route` 生成的完整 Routing；不得从聊天记忆重新猜需求或手改角色。
2. 每条 Criterion 只表达一个可证伪行为，指定独立 Verifier 与最少断言数。
3. Artifact Scope 只包含必要路径；Grant 明确动作、路径和副作用等级。
4. Budget 限制 Tick、Attempt、Tool Call 和命令时间。
5. 检查 Criterion 是否覆盖目标、Safety Invariant 是否覆盖不可破坏条件。
6. 绑定 Verifier Closure 后，向用户展示 Goal、Scope、Criterion、Grant、Budget、Risk 与角色路由。
7. 只有用户最终确认后才能运行 `work confirm` 与 `work accept`；确认绑定后任何字段变化都必须重新确认。
