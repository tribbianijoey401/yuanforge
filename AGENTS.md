# AGENTS.md — YuanForge 通用入口

> 本文件是 YuanForge 的**平台无关入口**。
> Cursor、Claude Code、Codex CLI、GitHub Copilot 等 Agent 平台都会自动读取此文件。
> 它告诉任何 Agent 平台：**"这是什么项目，规则在哪，怎么做。"**

---

## 🔨 这是什么

YuanForge（元锻造）是一个 **Vibecoding 元框架** — 一套可复制的 Agent 协作规范。
它不是代码库，而是一套让任何 Agent 平台都能按同一套规则协作的说明书。

---

## 🧭 快速入口

| 你想… | 读这里 |
|--------|--------|
| 了解项目当前状态 | [docs/PROGRESS.md](docs/PROGRESS.md) |
| 了解系统架构 | [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) |
| 搭建环境 | [docs/SETUP.md](docs/SETUP.md) |
| 写代码前的规范 | [docs/CONVENTIONS.md](docs/CONVENTIONS.md) |
| 查术语 | [docs/glossary.md](docs/glossary.md) |
| 避坑 | [docs/pitfalls.md](docs/pitfalls.md) |
| 查看历史决策 | [docs/decisions/](docs/decisions/) |
| 完整文档地图 | [docs/INDEX.md](docs/INDEX.md) |

---

## ⚡ 核心规则（必读）

在 `.yuan/rules/` 下：

| 文件 | 内容 |
|------|------|
| [iron-rules.md](.yuan/rules/iron-rules.md) | **九条铁律** — 所有 Agent 必须遵守 |
| [plan-format.md](.yuan/rules/plan-format.md) | Plan 工程化格式（含 Dispatch Table） |
| [docs-framework.md](.yuan/rules/docs-framework.md) | docs/ 说明书体系规范 |

---

## 👷 Agent 角色

在 `.yuan/agents/` 下定义了 6 个角色合约：

| 角色 | 文件 | 职责 |
|------|------|------|
| Architect | [architect.md](.yuan/agents/architect.md) | 需求分析 → 架构设计 → 产出 Plan |
| Coder | [coder.md](.yuan/agents/coder.md) | TDD 实现代码 |
| Reviewer | [reviewer.md](.yuan/agents/reviewer.md) | 两阶段代码审查 |
| Tester | [tester.md](.yuan/agents/tester.md) | 测试策略 + 执行 |
| DevOps | [devops.md](.yuan/agents/devops.md) | CI/CD + 部署 |
| Conductor | [../contracts/conductor.md](contracts/conductor.md) | 读 Plan → DAG → 派发 Agent |

---

## 🧰 可用 Skill

在 `.yuan/skills/` 下有 8 个通用 Skill：

- vibecoding-workflow — 核心开发工作流
- project-bootstrap — 项目初始化
- project-memory — 项目记忆管理
- writing-plans — Plan 写作
- subagent-driven-development — 子 Agent 并行执行
- test-driven-development — TDD 流程
- systematic-debugging — 系统调试方法
- requesting-code-review — 代码审查流程

---

## 🌐 平台适配

**YuanForge 不绑定任何特定 Agent 平台。** `.yuan/platforms/` 下是各平台的适配说明。

| 平台 | 适配文件 |
|------|---------|
| Hermes Agent | [platforms/hermes.md](.yuan/platforms/hermes.md) |
| 通用/人工 | [platforms/manual.md](.yuan/platforms/manual.md) |

如果你是 Agent：先读 `manual.md`，了解 YuanForge 的核心概念（角色、铁律、Dispatch Table）。然后在当前平台的能力范围内，选择最合适的执行方式。

---

## 📐 合约与协议

| 层 | 位置 | 作用 |
|----|------|------|
| 角色合约 | [contracts/](contracts/) | 每个 Agent 的入参/出参/边界 |
| 通信协议 | [protocols/](protocols/) | Dispatch Table + Task 产出物格式 |
| Plan 模板 | [templates/](templates/) | 含 Dispatch Table 的 Plan 模板 |

---

## 🚀 两种模式

| 模式 | 触发 | 规则 |
|------|------|------|
| **严格模式**（默认） | 不加标记 | 九条铁律全开 |
| **快速模式** | `@快速模式` | 放宽审查和提交，其余保持 |

---

> *YuanForge 不绑定语言，不绑定平台。它只是一套规则，任何 Agent 都能看懂、都能执行。*
