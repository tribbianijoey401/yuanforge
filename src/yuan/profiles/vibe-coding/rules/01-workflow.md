# Vibe Coding 工作流规则

## 需求入口

1. 先运行 `status` 与 `capability list`；状态或能力完整性失败时 fail-closed。
2. 用户只需要描述意图、范围、限制或“继续”；不得要求用户在提示词中指定 Intake、Agent 或 Skill。
3. 每个新请求由 Conductor 自动创建 Intake。会改变验收、安全边界或不可逆选择的问题必须询问用户；不得替用户回答。
4. Intake 的答案、可撤销假设、风险理由和 Signals 经用户确认后，才能执行 `capability route`。
5. Routing 是 Agent、Skill 与审查要求的唯一来源；按返回的 Assignment 自动加载内容，不使用用户口头点名替代路由。
6. Work/Verifier 完成后，把 Goal、Scope、Criterion、Grant、Budget 与 Routing 再次展示给用户；确认后才能接受 Work。

## 实施与角色交接

1. 每个 Tick 只推进一个可验证增量；保留用户已有改动，不覆盖无关文件。
2. Conductor 的每个派发包包含 Work Digest、角色、目标、范围、输入、禁止项、产出和验证方法。
3. 角色完成阶段时必须记录 `READY` 或 `NEEDS_WORK` Handoff；Reviewer 不修改被审对象，发现交回实现角色形成 `CORRECT` 闭环。
4. Artifact Reviewer 的旧 Handoff 会在 Artifact 变化后失效，必须重新审查。
5. Required Criterion Evidence 和全部 Required Handoff 同时有效之前，不得 `COMPLETE`。

## 中途需求变更

1. 用户修改已确认的目标、范围、验收、授权或风险时，不得直接编辑 Active Work。
2. 先解析所有 `PREPARED`、`DISPATCHED`、`OBSERVED` 或 `UNKNOWN` Attempt。
3. 对 `CONTINUE/CORRECT` Work 记录 `WORK_SUPERSEDED`，保留旧历史；重新创建 Intake、取得两次确认、生成 Routing，再启动绑定前任 Head 的 Successor。
4. 仅补充不改变契约的上下文可写入下一次派发包；是否改变契约有疑义时按需求变更处理。
