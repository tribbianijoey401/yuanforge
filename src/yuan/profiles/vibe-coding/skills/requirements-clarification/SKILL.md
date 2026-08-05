---
name: requirements-clarification
description: 在 Work 接受前持久化需求、待决问题、答案、假设、风险和用户确认。
---

# 需求澄清与确认

1. 由 Conductor 在新需求入口自动触发；用户的原始话语只表达目标、范围和限制，不要求包含 Intake、Agent 或 Skill 名称。
2. 用 `intake template --request <原始需求>` 创建 Intake 草稿，保存到 `.yuan/drafts/intake.json`。
3. 检查目标、用户、范围、非目标、失败影响、兼容性和不可逆选择；每个会改变验收标准或安全边界的问题标记为 Blocking。
4. 使用平台原生对话把 Blocking Question 原样问给用户，不替用户编造答案；答案和可撤销假设写回 Intake。
5. 根据影响分类 `R0/R1/R2`，填写具体理由和 Routing Signal；用 `seal` 重新计算草稿 Digest，再运行 `intake check`。返回 `NEEDS_INPUT` 时停止 Work 接受。
6. `intake check` 返回 `NEEDS_CONFIRMATION` 时，必须把返回的 `summary` 展示给用户，至少包含需求、问题答案、假设、风险、Signals 与 Subject Digest。用户明确确认后运行 `intake confirm`；没有确认不得进入 Work Authoring。
7. 运行 `capability route --risk <level> --signal <signal>`，把返回的 Routing 原样绑定到 Work，不手工删减风险要求。
8. Work 草案完成后再次向用户展示 Goal、范围、Criterion、Grant、Budget 和角色路由；仅在用户确认后运行 `work confirm` 与 `work accept`。

Intake Confirmation 在开放 Agent 平台属于 `AUDITED` 对话回执，不冒充不可伪造的人类签名；它的作用是固定本次会话实际采用的用户意图。
