# 🔨 YuanForge

> **元锻造** — 可复制的 Protocol-First 元框架。
> LLM 即 Runtime：不构建 Agent/Scheduler/Daemon，只定义协议。
> 一套框架，生产无数项目。

---

## 核心理念

```
你（导演）
  │ "我要做一个 xxx"
  ▼
┌──────────────────────────────────────┐
│  YuanForge 元框架                     │
│                                      │
│  🔨 铁律 (Iron Rules)                │
│  ─────────────────────               │
│  九条不可违反的法则，含三档阻塞策略    │
│                                      │
│  👷 12 人专家团                       │
│  ─────────────────────               │
│  Product Analyst → Architect         │
│  → Frontend/Backend Dev →            │
│  4 审查官并行 → Tester → Doc Engineer │
│                                      │
│  🧰 Skill 武器库                     │
│  ─────────────────────               │
│  每个技术栈封装为 Skill，Agent 按需加载│
│                                      │
│  📚 Docs（唯一状态）                  │
│  ─────────────────────               │
│  架构、决策、术语 — 永不丢失的知识     │
│                                      │
│  📐 5 份协议                          │
│  ─────────────────────               │
│  Object / State / Action             │
│  / Workflow / Adapter                │
└──────────────────────────────────────┘
```

**YuanForge 不绑定任何语言。** 你描述需求，框架选择最合适的栈。

---

## 快速开始

### 1. 初始化项目

```bash
# 从零开始
./bin/yuanforge-init ./my-awesome-project --name "我的项目"

# 嫁接到已有项目
./bin/yuanforge-init ./existing-project --mode existing
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

无论哪个平台，YuanForge 的工作流都一样：

1. **Product Analyst** 澄清需求 → 用户故事 + 验收标准
2. **Architect** 计划复盘 → 用户确认 → API 契约冻结 + Plan
3. **Frontend Dev + Backend Dev** 并行 TDD 实现
4. **4 审查官并行** → Spec/Security 为 Blocker，Quality/UX 为 Advisory
5. **Tester** Hard Gate → 全量测试 PASS
6. **Doc Engineer** 归档

> 💡 不同平台的自动调度能力不同。Hermes/Claude Code 能自动 fork 子 Agent，Cursor 需要手动切换角色。详见 `.yuan/platforms/`。

---

## 目录结构

```
yuanforge/
├── AGENTS.md                    # 通用入口（跨平台），含 6 步开发流程
├── README.md                    # 本文件
├── bin/yuanforge-init           # 项目初始化脚本
├── docs/                        # DocsOS 文档系统
│   ├── object-model.yaml        # 知识对象 Schema
│   ├── INDEX.md                 # 文档地图
│   ├── PROGRESS.md              # 进度中枢
│   ├── knowledge/               # 长期知识（features/decisions/pitfalls/modules）
│   ├── workspace/               # 计划管理（backlog + roadmap）
│   ├── policies/                # 系统规则（平台无关）
│   ├── archive/                 # 已关闭 Workspace 快照
│   └── 20260707-框架v2/          # 活跃 Workspace
├── .yuan/                       # 🔧 框架内核
│   ├── specs/                   # 5 份核心协议（Object/State/Action/Workflow/Adapter）
│   ├── docs/                    # 9 份文档格式规格书
│   ├── rules/                   # 九条铁律 + Plan 格式
│   ├── skills/                  # Skill 定义
│   └── platforms/               # 平台适配器
├── contracts/                   # 👷 12 个 Agent 角色合约
│   ├── conductor.md
│   ├── product-analyst.md
│   ├── architect.md
│   ├── ui-designer.md
│   ├── frontend-dev.md
│   ├── backend-dev.md
│   ├── spec-reviewer.md
│   ├── security-auditor.md
│   ├── quality-auditor.md
│   ├── ux-reviewer.md
│   ├── tester.md
│   └── doc-engineer.md
├── protocols/                   # Agent 间协议
│   ├── dispatch-table.md
│   └── task-output.md
└── templates/
    └── plan-with-dispatch.md
├── scripts/                     # 🛠 构建脚本
│   ├── build-graph.py           # Graph 自动生成
│   └── pre-commit               # 确定性校验（YAML/frontmatter/Proposal）
└── proposals/                   # 📝 提案事务（Knowledge 写保护）
```

---

## 九条铁律

| # | 铁律 | 核心 |
|---|------|------|
| Ⅰ | 计划先行 | 没有 Plan 不写一行代码 |
| Ⅱ | TDD 先行 | Red → Green → Refactor |
| Ⅲ | 三档审查 | 4 审查官并行：🔴Blocker / 🟡Hard Gate / 🟢Advisory↗ |
| Ⅳ | 原子提交 | 一个 Task 一个 Commit |
| Ⅴ | 上下文隔离 | 每个 Task 全新 Subagent |
| Ⅵ | 文档即代码 | 决策必须落文档 |
| Ⅶ | 渐进式交付 | 每步可运行 |
| Ⅷ | 质量门禁 | G1→G2→G3→G4，含三档阻塞策略 |
| Ⅸ | 自主调度 | Agent 按 Dispatch Table 自主派发 Agent |

详见 [`.yuan/rules/iron-rules.md`](.yuan/rules/iron-rules.md)

---

## 两种模式

| 模式 | 触发 | 规则 |
|------|------|------|
| **严格模式**（默认） | 不加标记 | 12 专家团全流程，九条铁律全开 |
| **快速模式** | `@快速模式` | 跳过审查层（保留 Tester），其余保持 |

---

## 依赖

**YuanForge 不依赖任何特定工具。** 它是一套规则（Markdown 文件），任何能读懂规则、执行命令的 Agent 平台都能运行。

| 你需要什么 | 说明 |
|-----------|------|
| 一个 Agent 平台 | Hermes Agent / Cursor / Claude Code / Codex CLI / Copilot ... 任意一个 |
| Git | 版本控制 |
| Python 3（仅 `yuanforge-init`） | 项目初始化脚本 |
| 无其他依赖 | 具体项目需要的运行时由 Agent 按需安装 |

> YuanForge 是规则，不是代码。它不绑定语言、不绑定框架、不绑定平台。

---

## 贡献

YuanForge 本身也用 YuanForge 开发（自举）。

---

> *驾驭 Agent，而非被 Agent 驾驭。*
