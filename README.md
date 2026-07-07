# 🔨 YuanForge

> **元锻造** — 可复制的 Vibecoding 项目母体。
> 基于 Harness 工程理念：驾驭 Agent、编排 Skill、铁律驱动。
> 一套框架，生产无数项目。

---

## 核心理念

```
你（导演）
  │ "做一个 TODO API"
  ▼
┌──────────────────────────────────────┐
│  YuanForge 元框架                     │
│                                      │
│  🔨 铁律 (Iron Rules)                │
│  ─────────────────────               │
│  九条不可违反的法则，约束所有 Agent    │
│                                      │
│  👷 Agent 军团                       │
│  ─────────────────────               │
│  Architect → Conductor               │
│  → Coder → Reviewer → Tester         │
│  → DevOps                            │
│                                      │
│  🧰 Skill 武器库                     │
│  ─────────────────────               │
│  每个技术栈封装为 Skill，Agent 按需加载│
│                                      │
│  📚 项目记忆 (Docs)                  │
│  ─────────────────────               │
│  架构、决策、术语 — 永不丢失的知识     │
└──────────────────────────────────────┘
```

**YuanForge 不绑定任何语言。** 你描述需求，框架选择最合适的栈。

---

## 快速开始

### 1. 启动新项目

```bash
cp -r yuanforge my-awesome-project
cd my-awesome-project
git init && git add -A && git commit -m "init: from YuanForge"
```

### 2. 开始 Vibecoding

**YuanForge 不绑定平台。** 选你习惯的 Agent 工具：

| 平台 | 操作 |
|------|------|
| **Hermes Agent** | 直接说「开发一个 TODO API」 |
| **Cursor** | 打开项目，Agent 自动读取 `AGENTS.md`，说「按照 YuanForge 框架开发 TODO API」 |
| **Claude Code** | `claude` 启动，自动加载 `AGENTS.md`，说「按 YuanForge 框架开发 TODO API」 |
| **Codex CLI** | `codex` 启动，说「read AGENTS.md，按 YuanForge 框架开发 TODO API」 |
| **任何平台** | 参考 `.yuan/platforms/manual.md` — 人工协调也能走通全流程 |

无论哪个平台，Yuan 的工作流都一样：

1. **Architect** 分析需求 → 设计架构 → 产出 Plan（含 Dispatch Table）
2. 你确认 Plan
3. **Conductor** 解析 Dispatch Table → 构建 DAG → 并行派发 Coder
4. Coder → Reviewer → Tester → DevOps 逐层流转
5. 每个 Task 经历完整的 TDD + 两阶段审查
6. 交付可运行的代码

> 💡 不同平台的自动调度能力不同。Hermes/Claude Code 能自动 fork 子 Agent，Cursor 需要手动切换角色。详见 `.yuan/platforms/`。

---

## 目录结构

```
yuanforge/
├── AGENTS.md                    # 🆕 通用入口（跨平台）
├── README.md                    # 本文件
├── .gitignore
├── docs/                        # 📚 项目说明书（生长层）
│   ├── INDEX.md                 # 入口 + 文档地图
│   ├── PROGRESS.md              # 进度中枢
│   ├── ARCHITECTURE.md          # 架构全景
│   ├── SETUP.md                 # 环境指南
│   ├── CONVENTIONS.md           # 规范约定
│   ├── glossary.md              # 术语表
│   ├── pitfalls.md              # 踩坑库
│   ├── features/                # 功能文档（每功能一文件）
│   │   └── _template.md
│   ├── bugs/                    # Bug 记录（每 Bug 一文件）
│   │   └── _template.md
│   └── decisions/               # 决策日志（每决策一文件）
│       └── _template.md
├── .yuan/                       # 🔧 框架内核（平台无关）
│   ├── agents/                  # 5 个 Agent 角色定义
│   │   ├── architect.md
│   │   ├── coder.md
│   │   ├── reviewer.md
│   │   ├── tester.md
│   │   └── devops.md
│   ├── rules/
│   │   ├── iron-rules.md        # 九条铁律
│   │   ├── plan-format.md       # Plan 工程化格式
│   │   └── docs-framework.md    # docs/ 说明书体系规范
│   ├── skills/                  # 8 个 Skill 定义
│   │   ├── vibecoding-workflow.md
│   │   ├── project-bootstrap.md
│   │   ├── project-memory.md
│   │   ├── writing-plans.md
│   │   ├── subagent-driven-development.md
│   │   ├── test-driven-development.md
│   │   ├── systematic-debugging.md
│   │   └── requesting-code-review.md
│   ├── docs/                    # 框架自身记忆
│   │   └── SESSION_LOG.md       # 会话日志
│   ├── platforms/               # 🆕 平台适配器
│   │   ├── hermes.md            # Hermes 平台适配
│   │   └── manual.md            # 通用/人工模式
│   └── plans/                   # 实现计划存档
├── contracts/                   # Agent 角色合约
│   ├── conductor.md
│   ├── architect.md
│   ├── coder.md
│   ├── reviewer.md
│   ├── tester.md
│   └── devops.md
├── protocols/                   # Agent 间协议
│   ├── dispatch-table.md
│   └── task-output.md
└── templates/
    └── plan-with-dispatch.md
```

---

## 九条铁律

| # | 铁律 | 核心 |
|---|------|------|
| Ⅰ | 计划先行 | 没有 Plan 不写一行代码 |
| Ⅱ | TDD 先行 | Red → Green → Refactor |
| Ⅲ | 两阶段审查 | Spec Review → Quality Review |
| Ⅳ | 原子提交 | 一个 Task 一个 Commit |
| Ⅴ | 上下文隔离 | 每个 Task 全新 Subagent |
| Ⅵ | 文档即代码 | 决策必须落文档 |
| Ⅶ | 渐进式交付 | 每步可运行 |
| Ⅷ | 质量门禁 | G1→G2→G3→G4，不通过不前进 |
| Ⅸ | 自主调度 | Agent 按 Dispatch Table 自主派发 Agent |

详见 [`.yuan/rules/iron-rules.md`](.yuan/rules/iron-rules.md)

---

## 两种模式

| 模式 | 触发 | 规则 |
|------|------|------|
| **严格模式**（默认） | 不加标记 | 九条铁律全开 |
| **快速模式** | `@快速模式` | 放宽审查和提交，其余保持 |

---

## 依赖

**YuanForge 不依赖任何特定工具。** 它是一套规则（Markdown 文件），任何能读懂规则、执行命令的 Agent 平台都能运行。

| 你需要什么 | 说明 |
|-----------|------|
| 一个 Agent 平台 | Hermes Agent / Cursor / Claude Code / Codex CLI / Copilot ... 任意一个 |
| Git | 版本控制 |
| 无其他依赖 | 具体项目需要的运行时由 Agent 按需安装 |

> YuanForge 是规则，不是代码。它不绑定语言、不绑定框架、不绑定平台。

---

## 贡献

YuanForge 本身也用 YuanForge 开发（自举）。

---

> *驾驭 Agent，而非被 Agent 驾驭。*
