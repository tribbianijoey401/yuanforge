# 📚 YuanForge 项目说明书

> **YuanForge（元锻造）** — 可复制的 Vibecoding 项目母体。平台无关的 Agent 协作框架。

---

## ⚡ 30 秒速览

- **项目是什么:** 一套纯 Markdown 规则体系，让任何 Agent 平台都能按统一的工作流协作开发
- **技术栈:** 无代码 — Markdown + Git
- **当前状态:** 框架 v2.0，功能完整，持续迭代
- **下一步:** 实战验证 + 用户反馈优化

---

## 🚀 快速导航

| 你想… | 读这个 |
|--------|--------|
| 了解当前框架状态 | → [PROGRESS.md](./PROGRESS.md) |
| 了解框架设计理念和架构 | → [ARCHITECTURE.md](./ARCHITECTURE.md) |
| 把 YuanForge 跑起来 | → [SETUP.md](./SETUP.md) |
| 写框架代码的规范 | → [CONVENTIONS.md](./CONVENTIONS.md) |
| 查术语 | → [glossary.md](./glossary.md) |
| 看踩过的坑 | → [pitfalls.md](./pitfalls.md) |
| 看历史决策 | → [decisions/](./decisions/) |
| 看功能记录 | → [features/](./features/) |
| 查 Bug | → [bugs/](./bugs/) |

---

## 📚 文档地图

### 全局文档（每次必读）

| 文档 | 何时读 | 优先级 |
|------|--------|--------|
| [PROGRESS.md](./PROGRESS.md) | 每次必读 | 🔴 必读 |
| [ARCHITECTURE.md](./ARCHITECTURE.md) | 首次接手、架构变更时 | 🔴 必读 |
| [pitfalls.md](./pitfalls.md) | 每次必读 | 🔴 必读 |
| [SETUP.md](./SETUP.md) | 首次接手 | 🟡 按需 |
| [CONVENTIONS.md](./CONVENTIONS.md) | 修改框架文件前 | 🟡 按需 |

### 生长文档

| 目录 | 内容 | 当前状态 |
|------|------|---------|
| [features/](./features/) | 框架功能演进记录 | 待填充 |
| [bugs/](./bugs/) | 框架自身 Bug | 待填充 |
| [decisions/](./decisions/) | 架构决策 (ADR) | 待填充 |
| [glossary.md](./glossary.md) | 领域术语 | 已填充 |
| [pitfalls.md](./pitfalls.md) | 开发踩坑 | 已填充 |

---

## 🤖 Agent 接手阅读顺序

```
1. INDEX.md (本文件)     → 知道有哪些文档
2. PROGRESS.md           → 知道框架当前状态
3. ARCHITECTURE.md       → 知道框架怎么设计的
4. pitfalls.md           → 知道有哪些坑
5. 按需进入 features/ bugs/ decisions/
```

---

## 🔗 相关链接

| 项 | 地址 |
|----|------|
| GitHub | https://github.com/tribbianijoey401/yuanforge |
| 框架内核 | `.yuan/` — Agent 角色、Skill、铁律、平台适配器 |
| 项目模板 | `.yuan/templates/` — 供新项目复制的模板文件 |

---

> *YuanForge: 驾驭 Agent，而非被 Agent 驾驭。*
