# 📚 YuanForge 项目说明书

> **YuanForge（元锻造）** — 可复制的 Vibecoding 项目母体。平台无关的 Agent 协作框架。
> 
> **DocsOS** — 对象中心的 Agent 文档系统。Knowledge 是对象，Markdown 只是序列化。

---

## ⚡ 30 秒速览

- **项目是什么:** 一套纯 Markdown 规则体系，让任何 Agent 平台都能按统一的工作流协作开发
- **技术栈:** 无代码 — Markdown + Git
- **当前状态:** DocsOS v1 与框架逻辑审计均已完成
- **当前会话:** —（无活跃 Workspace）
- **下一步:** 用真实项目验证工作流

---

## 🚀 快速导航

| 你想… | 读这个 |
|--------|--------|
| 了解当前状态 | → [PROGRESS.md](./PROGRESS.md) |
| 了解框架设计理念和架构 | → [ARCHITECTURE.md](./ARCHITECTURE.md) |
| 了解知识对象定义 | → [object-model.yaml](./object-model.yaml) |
| 了解所有功能 | → [knowledge/features/](./knowledge/features/) |
| 了解所有技术决策 | → [knowledge/decisions/](./knowledge/decisions/) |
| 避坑（Agent 必读） | → [knowledge/pitfalls/](./knowledge/pitfalls/) |
| 了解模块结构 | → [knowledge/modules/](./knowledge/modules/) |
| 看历史会话 | → [archive/](./archive/) |
| 查看待办和路线图 | → [workspace/backlog.md](./workspace/backlog.md) |
| 了解系统规则 | → [policies/](./policies/) |
| 搭建环境 | → [SETUP.md](./SETUP.md) |
| 写代码的规范 | → [CONVENTIONS.md](./CONVENTIONS.md) |
| 查术语 | → [glossary.md](./glossary.md) |

---

## 📚 文档地图

### DocsOS 七层

| 层 | 目录 | 内容 | 何时读 |
|----|------|------|--------|
| Object Model | [object-model.yaml](./object-model.yaml) | 知识对象 Schema | 需要了解对象定义时 |
| Knowledge | [knowledge/](./knowledge/) | 长期知识（Feature/ADR/Pitfall/Module） | 每次必读 |
| Runtime | [YYYYMMDD-描述/](./) | 活跃 Workspace（唯一真相源 TASK_BOARD） | 当前工作时 |
| Events | events/（未来） | 结构化事件日志 | 崩溃恢复、变更追溯 |
| Graph | graph/（未来） | 自动生成的知识索引 | 依赖查询 |
| Policy | [policies/](./policies/) | 系统规则（平台无关） | 需要了解规则时 |
| Archive | [archive/](./archive/) | 已关闭的 Workspace 快照 | 回顾历史 |

### 全局文档

| 文档 | 何时读 | 优先级 |
|------|--------|--------|
| [PROGRESS.md](./PROGRESS.md) | 每次必读 | 🔴 |
| [ARCHITECTURE.md](./ARCHITECTURE.md) | 首次接手 | 🔴 |
| [knowledge/pitfalls/](./knowledge/pitfalls/) | 每次必读 | 🔴 |
| [SETUP.md](./SETUP.md) | 首次接手 | 🟡 |
| [CONVENTIONS.md](./CONVENTIONS.md) | 修改框架文件前 | 🟡 |
| [glossary.md](./glossary.md) | 查术语时 | 🟢 |

---

## 🤖 Agent 阅读顺序

```
1. INDEX.md (本文件)            → 知道有哪些文档
2. PROGRESS.md                  → 知道当前状态（~500B）
3. ARCHITECTURE.md              → 知道系统怎么设计的
4. knowledge/pitfalls/          → 避坑（~2KB，必读）
5. 当前 Workspace 文件夹         → 了解本次会话的 Plan + TASK_BOARD
```

---

## 🔗 相关链接

| 项 | 地址 |
|----|------|
| GitHub | https://github.com/tribbianijoey401/yuanforge |
| 框架内核 | `.yuan/` — Agent 角色、Skill、铁律、平台适配器 |
| 规格书 | `.yuan/docs/` — 6 份 doc 规格书（含 OBJECT_MODEL） |

---

> *YuanForge: 驾驭 Agent，而非被 Agent 驾驭。*
