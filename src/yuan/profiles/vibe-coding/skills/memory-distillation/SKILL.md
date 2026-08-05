---
name: memory-distillation
description: 从 Work、Evidence、Attempt 与 Handoff 创建来源强度明确的长期记忆和连续性检查点。
---

# 长期记忆蒸馏

1. 由 Handoff、暂停、阻塞和 Work 收尾节点自动触发；不得依赖用户提醒调用 `memory-curator` 或本 Skill。
2. 先区分信息用途：`checkpoint/handoff` 保存连续性，`project/decision` 保存已确认选择，`feature/module/architecture/convention` 保存已验证知识，`pitfall/incident` 保存问题经验。
3. 连续性在角色交接、会话暂停、阻塞和 Work 收尾前用 `memory checkpoint` 保存；它不等待 PASS，但必须绑定当前 Work、Artifact 与 Ledger Head。
4. 知识只能绑定当前 PASS Evidence；决策绑定用户已确认 Work；经验绑定 FAIL Evidence 或真实 Attempt 历史。推测只能作为待验证线索，不能伪装成 verified。
5. 同一事实使用稳定 Memory ID，变化时追加 Revision，不覆盖旧记录。正常流程运行 `memory template`、`memory check`、`memory record` 和 `memory status`；`memory rebuild` 仅用于索引损坏后的操作员恢复。
6. 检查 `CURRENT.md`、`PROJECT.md` 和 `views/` 是否可由 JSON Records 重建。没有长期事实变化时写明 `NO_MEMORY_CHANGE`，但不能省略连续性检查点。
