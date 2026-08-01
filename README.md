# 🔨 YuanForge — YuanCore

> **元锻造 · Core** — 以确定性 Harness 约束非确定性 LLM、以证据驱动完成判定的最小化多 Agent 持久化软件工程引擎。
> LLM 即 Runtime：不构建 Agent/Scheduler/Daemon，只定义协议。一套框架，生产无数项目。
>
> **当前版本**：`yuanforge-core-v1.0`（Phase 1–9 全部完成）
> **测试**：35/35 通过 · Python 3.9+ · 纯 Markdown 驱动

---

## 架构总览

```
┌─────────────────────────────────────────────────────────────┐
│  Platform Goal（Hermes / Claude Code / Cursor / Manual …） │  ← 驱动入口，不是完成裁判
└──────────────────────┬──────────────────────────────────────┘
                       ▼
┌─────────────────────────────────────────────────────────────┐
│  .yuan/platforms/   平台适配层                               │
│  capabilities.md    六大标准 Capability 声明格式            │
│  hermes.md          Hermes Agent 映射                        │
│  manual.md          人工协调模式                             │
│  capability_adapter.py  Goal Tick → Core Tick 调度           │
└──────────────────────┬──────────────────────────────────────┘
                       ▼
┌─────────────────────────────────────────────────────────────┐
│  .yuan/core/        确定性 Core（不可变约束）                │
│  PROTOCOL.md        Core 权威定义，优先级最高                 │
│  INVARIANTS.md      7 条安全不变量（I0–I7）                  │
│  REDUCER.md         6 结果确定性决策表                       │
│  schemas/           7 个核心 Schema                          │
│    WORK / STATE / PROPOSAL / ATTEMPT / EVIDENCE / JOURNAL   │
│    CHANGE                                           │
│  validators/        Core Schema + Role Extension 两阶段校验  │
└──────────────────────┬──────────────────────────────────────┘
                       ▼
┌─────────────────────────────────────────────────────────────┐
│  .yuan/extensions/  可选扩展（禁用不影响 Core 完成语义）    │
│  agents/roles/      13 个角色合约（按 Work Contract 声明）  │
│  workflows/         5 个编排模式（TDD / Phase Gates / …）  │
│  policies/          3 个执行约束（三档审查 / 原子提交 / …）│
│  skills/            6 个可执行技能（TDD / Debug / Grilling）│
└──────────────────────┬──────────────────────────────────────┘
                       ▼
┌─────────────────────────────────────────────────────────────┐
│  .yuan/runtime/     Shadow Runtime（观察 + 验证）          │
│  runner.py          Core Tick 循环（proposal scan → reducer │
│  shadow_evaluator.py 证据老化检测 + Reducer 预测            │
│  generate_views.py  STATE → TASK_BOARD / PROGRESS / SESSION │
│  capability_adapter.py Platform Capability 映射             │
└──────────────────────┬──────────────────────────────────────┘
                       ▼
              work/STATE.md    ← 唯一状态源（唯一恢复点）
```

---

## 核心闭环

```
Work Contract (WORK.md)
        │
        ▼
   Proposal ──[Core Schema]──→ Attempt ──[execute]──→ Evidence
        │                               │
        │        Core + Role Extension   │
        │        两阶段校验              │
        │                               │
        ▼                               ▼
   select_proposal               run_reducer()
        │                          │
        │   确定性选择              │   6 种结果：
        │   selection_rank         │   COMPLETE / BLOCKED / BUDGET_EXIT
        │                          │   WAIT_AUTH / CORRECT / CONTINUE
        ▼                          ▼
  STATE.md (CAS 更新) ◄─────────────┘
        │
        ▼
  generate_views() → TASK_BOARD / PROGRESS / SESSION
```

---

## 快速开始

### 1. 初始化项目

```bash
# 从零开始
./bin/yuanforge-init ./my-awesome-project --name "我的项目"

# 嫁接到已有项目
./bin/yuanforge-init ./existing-project --mode existing
```

### 2. 开始任务

**YuanForge 不绑定平台。** 选你习惯的 Agent 工具：

| 平台 | 操作 |
|------|------|
| **Hermes Agent** | 直接说「开发一个 TODO API」 |
| **Cursor** | 打开项目，Agent 自动读取 `AGENTS.md`，说「按 YuanForge 框架开发 TODO API」 |
| **Claude Code** | `claude` 启动，自动加载 `AGENTS.md`，说「按 YuanForge 框架开发 TODO API」 |
| **Codex CLI** | `codex` 启动，说「read AGENTS.md，按 YuanForge 框架开发 TODO API」 |
| **任何平台** | 参考 `.yuan/platforms/manual.md` — 人工协调也能走通全流程 |

无论哪个平台，YuanForge 的核心流程都一样：

```
Product Analyst（需求澄清）
      ▼
   Architect（计划 + API 契约）
      ▼
  Frontend Dev  +  Backend Dev（TDD 并行，Role Isolation）
      ▼
  Spec Reviewer（🔴Blocker）  Security Auditor（🔴Blocker）
  Quality Auditor（🟡Hard Gate）  UX Reviewer（🟡Hard Gate）
      ▼
     Tester（全量测试 PASS）
      ▼
   Doc Engineer（归档）
```

> 💡 不同平台的自动调度能力不同。Hermes/Claude Code 能自动 fork 子 Agent，Cursor 需要手动切换角色。详见 `.yuan/platforms/`。

---

## 目录结构

```
yuanforge/
├── AGENTS.md                    # 通用入口（跨平台），含框架激活检查 + 铁律速查
├── README.md                    # 本文件
├── bin/
│   └── yuanforge-init           # 项目初始化脚本
├── .yuan/
│   ├── core/                    # 🔒 Core（不可变约束）
│   │   ├── PROTOCOL.md          #   Core 权威定义，优先级最高
│   │   ├── INVARIANTS.md        #   7 条安全不变量 I0–I7
│   │   ├── REDUCER.md           #   6 结果确定性决策表
│   │   ├── schemas/             #   7 个核心 Schema（WORK/STATE/…）
│   │   ├── validators/          #   Trust Boundary 校验
│   │   └── CONFLICT_RULES.md    #   Core–Extension 冲突解决规则
│   ├── extensions/              # 🧩 可选扩展
│   │   ├── MANIFEST.md          #   扩展注册表（依赖图 + 禁用影响）
│   │   ├── agents/roles/        #   13 个角色合约
│   │   ├── workflows/           #   5 个编排模式
│   │   ├── policies/            #   3 个执行约束
│   │   └── skills/              #   6 个可执行技能
│   ├── platforms/               # 🎯 平台适配
│   │   ├── capabilities.md      #   六大标准 Capability 声明
│   │   ├── hermes.md            #   Hermes Agent 映射
│   │   └── manual.md            #   人工协调模式
│   ├── runtime/                 # ⚙️ Shadow Runtime
│   │   ├── runner.py            #   Core Tick 主循环
│   │   ├── shadow_evaluator.py  #   证据老化 + Reducer 预测
│   │   ├── generate_views.py    #   STATE → 派生视图
│   │   └── capability_adapter.py # Platform Goal → Core STATE
│   ├── specs/                   # 5 份核心协议（Object/State/Action/Workflow/Adapter）
│   ├── rules/                   # 十条铁律 + Plan 格式 + 文档框架
│   ├── skills/                  # Legacy 技能（兼容 Hermes skill_view）
│   └── docs/                    # 9 份文档格式规格书
├── contracts/                   # 👷 13 个角色合约（Legacy，仍被平台文档引用）
├── protocols/                   # Agent 间协议（dispatch-table / task-output）
├── templates/                   # 模板
│   └── plan-with-dispatch.md
├── scripts/
│   └── validation/
│       ├── core_validator.py    # 完整验证器（Core + Role 两阶段）
│       ├── phase3-tests.py      # Phase 3 验收测试（15 项）
│       ├── phase7-tests.py      # Phase 7 验收测试（12 项）
│       └── phase8-tests.py      # Phase 8 验收测试（8 项）
├── work/
│   ├── STATE.md                 # 🔑 唯一状态源（IDLE/COMPLETE/BLOCKED…）
│   ├── WORK.md                  # 工作契约
│   ├── proposals/               # 候选 Proposal
│   ├── attempts/                # 已执行 Attempt
│   ├── evidence/                # 绑定 Evidence
│   ├── journal/                 # 不可变审计日志
│   └── views/                   # 派生视图（TASK_BOARD / PROGRESS / SESSION）
├── docs/
│   ├── MIGRATION.md             # Phase 1–9 迁移完整记录
│   ├── ARCHITECTURE.md          # 框架架构概览
│   ├── anti-patterns.md         # 反模式清单
│   └── knowledge/               # Pitfall + Decision 记录
├── references/                  # 设计系统 + 行业参考
└── protocols/                   # 调度协议
```

---

## 十条铁律

| # | 铁律 | 一句话核心 |
|---|------|----------|
| Ⅰ | 计划先行 | 没有 Plan 不写一行代码 |
| Ⅱ | TDD 先行 | Red → Green → Refactor |
| Ⅲ | 三档审查 | 4 审查官并行：🔴Blocker / 🟡Hard Gate / 🟢Advisory |
| Ⅳ | 原子提交 | 一个 Task 一个 Commit |
| Ⅴ | 上下文隔离 | 每个 Task 全新 Subagent |
| Ⅵ | 文档即代码 | 决策必须落文档 |
| Ⅶ | 渐进式交付 | 每步可运行 |
| Ⅷ | 质量门禁 | G1→G2→G3→G4，含三档阻塞策略 |
| Ⅸ | 自主调度 | Conductor 按调度循环自主派发 |
| Ⅹ | 循环收敛 | 每个循环必须有闸门 |

详见 [`.yuan/rules/iron-rules.md`](.yuan/rules/iron-rules.md)

---

## 13 个角色合约

| 角色 | 职责 |
|------|------|
| **conductor** | 指挥/调度，不写代码，负责派单和进度监控 |
| **product-analyst** | 需求澄清，用户故事 + 验收标准，grilling 技能 |
| **architect** | 系统架构设计，API 契约，技术选型 |
| **frontend-dev** | 前端实现，TDD，响应式 UI |
| **backend-dev** | 后端实现，TDD，API/DB |
| **ui-designer** | 视觉设计，设计系统落地 |
| **spec-reviewer** | 🔴Blocker — 规格一致性审查 |
| **security-auditor** | 🔴Blocker — 安全漏洞审查 |
| **quality-auditor** | 🟡Hard Gate — 代码质量审查 |
| **ux-reviewer** | 🟡Hard Gate — 用户体验审查 |
| **design-reviewer** | 🟢Advisory — 设计一致性审查 |
| **tester** | 全量测试 PASS，Hard Gate |
| **doc-engineer** | 归档，Knowledge 蒸馏 |

---

## 可选扩展（按 Work Contract 声明）

### Workflows（编排模式）

| 名称 | 作用 |
|------|------|
| `tdd-loop.md` | Red→Green→Refactor 详细执行指引 |
| `phase-gates.md` | 五阶段流水线 + 质量门禁（G1–G4） |
| `atomic-commit.md` | 每 Task 一个独立 Commit |
| `role-isolation.md` | 多角色并行，独立上下文 |
| `promotion.md` | Workspace 关闭时知识蒸馏 |

### Policies（执行约束）

| 名称 | 作用 |
|------|------|
| `three-level-review.md` | 🔴Blocker / 🟡Hard Gate / 🟢Advisory 角色级定义 |
| `per-task-commit.md` | Commit message 格式要求 |
| `evidence-binding.md` | 专业结论必须绑定 Evidence |

### Skills（可执行技能）

| 名称 | 作用 |
|------|------|
| `test-driven-development.md` | TDD 循环详细指引 |
| `subagent-driven-development.md` | Conductor 子 Agent 派发策略 |
| `knowledge-distillation.md` | 知识提取：Pitfall / Pattern / Convention |
| `debug-feedback-loop.md` | 系统化诊断：Isolate→Bisect→Hypothesize→Verify→Fix |
| `grilling.md` | 需求追问协议（多轮澄清模糊维度） |
| `promotion.md` | Skill 晋升管线：draft → published → deprecated |

---

## 测试与验收

| 套件 | 项数 | 状态 |
|------|------|------|
| `phase3-tests.py` | 15 | ✅ 全部通过 |
| `phase7-tests.py` | 12 | ✅ 全部通过 |
| `phase8-tests.py` | 8 | ✅ 全部通过 |
| **合计** | **35** | **35/35 通过** |

```bash
python3 -B scripts/validation/phase3-tests.py
python3 -B scripts/validation/phase7-tests.py
python3 -B scripts/validation/phase8-tests.py
```

---

## 依赖

**YuanForge 不依赖任何特定工具。** 它是一套规则（Markdown 文件），任何能读懂规则、执行命令的 Agent 平台都能运行。

| 你需要什么 | 说明 |
|-----------|------|
| 一个 Agent 平台 | Hermes Agent / Cursor / Claude Code / Codex CLI / Copilot … 任意一个 |
| Git | 版本控制 |
| Python 3.9+（仅 `core_validator.py`） | Shadow Runtime 验证器 |
| 无其他依赖 | 具体项目需要的运行时由 Agent 按需安装 |

---

## 版本与回退

```bash
# 当前冻结基线
git tag -l yuanforge-core-v1.0

# 查看迁移历史
cat docs/MIGRATION.md
```

---

## 贡献

YuanForge 本身也用 YuanForge 开发（自举）。

Phase 1–9 迁移路线详见 [`.plan`](/home/admin/shishi.plan)，迁移日志见 [`docs/MIGRATION.md`](docs/MIGRATION.md)。

---

> *驾驭 Agent，而非被 Agent 驾驭。*
