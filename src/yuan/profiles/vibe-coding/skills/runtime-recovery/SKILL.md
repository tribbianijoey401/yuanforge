---
name: runtime-recovery
description: 在旧 Runtime、配置或安装记录不可信时，从 Yuan Source 外部强制重建托管框架并保留项目记忆。
---

# Runtime 恢复

1. 收集失败阶段、实际命令、Exit Code、stdout/stderr、目标根目录和写权限；不要求旧 Runtime 成功运行。
2. 运行 `python -B scripts/sync_project.py update <target>`。`update` 不执行旧安装完整性、版本、Active Work、Conformance、Staging 或 Rollback 门禁。
3. 更新只覆盖 `.yuan` 托管 Runtime/Config/Protocol/Adapter/Profile 和 Managed Block；不得修改 `.yuan-run/`、`docs/memory/`、`.yuan/extensions/custom/` 与项目自有内容。
4. 检查返回的 `memory_preserved` 和 Memory 前后指纹。新 Runtime 状态失败属于后续兼容诊断，不恢复旧 Runtime。
5. 若更新失败，只能按“无法构建”“无法写入”“Memory 被改变”分类；保留完整回执，改变假设或策略后才能重试。
