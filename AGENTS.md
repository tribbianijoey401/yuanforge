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
| 查看历史决策 | [docs/20260707-框架v2/](docs/20260707-框架v2/) |
| 完整文档地图 | [docs/INDEX.md](docs/INDEX.md) |

---

## ⚡ 核心规则（必读）

在 `.yuan/rules/` 下：

| 文件 | 内容 |
|------|------|
| [iron-rules.md](.yuan/rules/iron-rules.md) | **九条铁律** — 所有 Agent 必须遵守。含三档阻塞策略 |
| [plan-format.md](.yuan/rules/plan-format.md) | Plan 工程化格式（含 Dispatch Table） |
| [.yuan/docs/](.yuan/docs/) | docs/ 说明书体系规范 |

---

## 👷 Agent 专家团

在 `contracts/` 下定义了 12 个角色合约：

| 角色 | 文件 | 档位 | 职责 |
|------|------|------|------|
| Product Analyst | [product-analyst.md](contracts/product-analyst.md) | — | vibe→用户故事+验收标准+风险标签 |
| Architect | [architect.md](contracts/architect.md) | — | 计划复盘→API契约冻结+Plan |
| UI Designer | [ui-designer.md](contracts/ui-designer.md) | — | 视觉规范+交互原型 |
| Frontend Dev | [frontend-dev.md](contracts/frontend-dev.md) | — | 前端TDD实现+Debug模式 |
| Backend Dev | [backend-dev.md](contracts/backend-dev.md) | — | 后端TDD实现+Debug模式 |
| Spec Reviewer | [spec-reviewer.md](contracts/spec-reviewer.md) | 🔴 Blocker | 对照验收标准+API契约审查 |
| Security Auditor | [security-auditor.md](contracts/security-auditor.md) | 🔴 Blocker | P0/P1/P2分级安全审计 |
| Quality Auditor | [quality-auditor.md](contracts/quality-auditor.md) | 🟢 Advisory↗ | DB+性能审计，同类3次升级 |
| UX Reviewer | [ux-reviewer.md](contracts/ux-reviewer.md) | 🟢 Advisory↗ | UI还原度+无障碍审计 |
| Tester | [tester.md](contracts/tester.md) | 🟡 Hard Gate | 全量测试+修复回路路由 |
| Doc Engineer | [doc-engineer.md](contracts/doc-engineer.md) | — | 增量归档+阶段整合 |
| Conductor | [conductor.md](contracts/conductor.md) | — | 调度+DevOps模式+诊断包注入 |

> 三档阻塞：🔴 Blocker（不解决不合入）→ 🟡 Hard Gate（必须全绿）→ 🟢 Advisory（可豁免，🟠≥3升级）

---

## 🧰 可用 Skill

在 `.yuan/skills/` 下有 9 个通用 Skill：

- vibecoding-workflow — 核心开发工作流（含 Phase 0-4）
- project-bootstrap — 项目初始化（全新 + 嫁接两种模式）
- project-audit — 审计现有项目，填充说明书
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
| 角色合约 | [contracts/](contracts/) | 12 个 Agent 的职责/输入/输出/禁止 |
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
