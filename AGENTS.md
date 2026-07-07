     1|# AGENTS.md — YuanForge 通用入口
     2|
     3|> 本文件是 YuanForge 的**平台无关入口**。
     4|> Cursor、Claude Code、Codex CLI、GitHub Copilot 等 Agent 平台都会自动读取此文件。
     5|> 它告诉任何 Agent 平台：**"这是什么项目，规则在哪，怎么做。"**
     6|
     7|---
     8|
     9|## 🔨 这是什么
    10|
    11|YuanForge（元锻造）是一个 **Vibecoding 元框架** — 一套可复制的 Agent 协作规范。
    12|它不是代码库，而是一套让任何 Agent 平台都能按同一套规则协作的说明书。
    13|
    14|---
    15|
    16|## 🧭 快速入口
    17|
    18|| 你想… | 读这里 |
    19||--------|--------|
    20|| 了解项目当前状态 | [docs/PROGRESS.md](docs/PROGRESS.md) |
    21|| 了解系统架构 | [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) |
    22|| 搭建环境 | [docs/SETUP.md](docs/SETUP.md) |
    23|| 写代码前的规范 | [docs/CONVENTIONS.md](docs/CONVENTIONS.md) |
    24|| 查术语 | [docs/glossary.md](docs/glossary.md) |
    25|| 避坑 | [docs/pitfalls.md](docs/pitfalls.md) |
    26|| 查看历史决策 | [docs/[当前会话]/](docs/[当前会话]/) |
    27|| 完整文档地图 | [docs/INDEX.md](docs/INDEX.md) |
    28|
    29|---
    30|
    31|## ⚡ 核心规则（必读）
    32|
    33|在 `.yuan/rules/` 下：
    34|
    35|| 文件 | 内容 |
    36||------|------|
    37|| [iron-rules.md](.yuan/rules/iron-rules.md) | **九条铁律** — 所有 Agent 必须遵守 |
    38|| [plan-format.md](.yuan/rules/plan-format.md) | Plan 工程化格式（含 Dispatch Table） |
    39|| [.yuan/docs/](.yuan/docs/) | docs/ 说明书体系规范 |
    40|
    41|---
    42|
    43|## 👷 Agent 角色
    44|
    45|在 `.yuan/agents/` 下定义了 6 个角色合约：
    46|
    47|| 角色 | 文件 | 职责 |
    48||------|------|------|
    49|| Architect | [architect.md](.yuan/agents/architect.md) | 需求分析 → 架构设计 → 产出 Plan |
    50|| Coder | [coder.md](.yuan/agents/coder.md) | TDD 实现代码 |
    51|| Reviewer | [reviewer.md](.yuan/agents/reviewer.md) | 两阶段代码审查 |
    52|| Tester | [tester.md](.yuan/agents/tester.md) | 测试策略 + 执行 |
    53|| DevOps | [devops.md](.yuan/agents/devops.md) | CI/CD + 部署 |
    54|| Conductor | [../contracts/conductor.md](contracts/conductor.md) | 读 Plan → DAG → 派发 Agent |
    55|
    56|---
    57|
    58|## 🧰 可用 Skill
    59|
    60|在 `.yuan/skills/` 下有 9 个通用 Skill：
    61|
    62|- vibecoding-workflow — 核心开发工作流（含 Phase 0-4）
    63|- project-bootstrap — 项目初始化（全新 + 嫁接两种模式）
    64|- project-audit — 审计现有项目，填充说明书
    65|- project-memory — 项目记忆管理
    66|- writing-plans — Plan 写作
    67|- subagent-driven-development — 子 Agent 并行执行
    68|- test-driven-development — TDD 流程
    69|- systematic-debugging — 系统调试方法
    70|- requesting-code-review — 代码审查流程
    71|
    72|---
    73|
    74|## 🌐 平台适配
    75|
    76|**YuanForge 不绑定任何特定 Agent 平台。** `.yuan/platforms/` 下是各平台的适配说明。
    77|
    78|| 平台 | 适配文件 |
    79||------|---------|
    80|| Hermes Agent | [platforms/hermes.md](.yuan/platforms/hermes.md) |
    81|| 通用/人工 | [platforms/manual.md](.yuan/platforms/manual.md) |
    82|
    83|如果你是 Agent：先读 `manual.md`，了解 YuanForge 的核心概念（角色、铁律、Dispatch Table）。然后在当前平台的能力范围内，选择最合适的执行方式。
    84|
    85|---
    86|
    87|## 📐 合约与协议
    88|
    89|| 层 | 位置 | 作用 |
    90||----|------|------|
    91|| 角色合约 | [contracts/](contracts/) | 每个 Agent 的入参/出参/边界 |
    92|| 通信协议 | [protocols/](protocols/) | Dispatch Table + Task 产出物格式 |
    93|| Plan 模板 | [templates/](templates/) | 含 Dispatch Table 的 Plan 模板 |
    94|
    95|---
    96|
    97|## 🚀 两种模式
    98|
    99|| 模式 | 触发 | 规则 |
   100||------|------|------|
   101|| **严格模式**（默认） | 不加标记 | 九条铁律全开 |
   102|| **快速模式** | `@快速模式` | 放宽审查和提交，其余保持 |
   103|
   104|---
   105|
   106|> *YuanForge 不绑定语言，不绑定平台。它只是一套规则，任何 Agent 都能看懂、都能执行。*
   107|