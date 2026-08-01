---
name: runtime-readme
title: YuanCore Runtime
description: 'YuanForge Core framework document'
category: documentation
stage: published
created_at: 2026-07-31
last_modified: 2026-08-01
author: framework-team
---

# runtime/ — 动态沉淀区

YuanForge 框架的动态运行时数据沉淀目录。此目录下的内容由框架运行时自动创建和管理，**请勿手动修改**。

## 目录结构

### knowledge/ — 待审核知识池
Agent 在执行技能过程中发现的有用知识点暂存区，等待人工审核后再合并到正式 docs/skills。
- 命名格式：`new_<主题>_<时间戳>.md`
- 示例：`new_cache_strategy_20260724.md`

### context/ — 会话上下文存储
为长周期任务、多轮对话保存中间状态和决策笔记。
- 格式：`<task-id>/session-YYYYMMDD-HHMMSS.md`

### review/ — 评审暂存区
文档修改提案、争议讨论的草稿区。
- `doc-change-proposals/` — 待合并的修改提案
- `discussion-threads/` — 讨论记录

### log/ — 审计日志（只追加）
记录所有文档访问和操作，用于追溯和统计分析。
- `read_access.log` — 文件读取记录
- `execution.log` — Skill 调用日志
- `audit_YYYY-MM-DD.log` — 按日归档

### metadata/ — 数据统计
- `usage_stats.json` — 全局读写统计和热门文档排名
- `skill_scores/` — Skill 评分卡结果
- `spec_scores/` — 协议评分卡结果

## 访问权限
此目录由框架自动管理，用户和 Agent 仅能通过指定接口读取和写入。
