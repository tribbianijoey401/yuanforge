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

在 Hermes Agent 中说：

```
开始开发一个 TODO API
```

Yuan 会自动：
1. **Architect** 分析需求 → 设计架构 → 产出 Plan（含 Dispatch Table）
2. 你确认 Plan
3. **Conductor** 解析 Dispatch Table → 构建 DAG → 并行派发 Coder
4. Coder → Reviewer → Tester → DevOps 逐层流转
5. 每个 Task 经历完整的 TDD + 两阶段审查
6. 交付可运行的代码

---

## 目录结构

```
yuanforge/
├── README.md                    # 本文件
├── .gitignore
├── .hermes/                     # 框架核心
│   ├── agents/                  # 5 个 Agent 角色定义（详细工作流）
│   │   ├── architect.md         # 架构师：需求→设计→计划
│   │   ├── coder.md             # 开发者：TDD 实现
│   │   ├── reviewer.md          # 审查者：两阶段审查
│   │   ├── tester.md            # 测试者：策略与覆盖
│   │   └── devops.md            # 运维者：CI/CD + 部署
│   ├── rules/
│   │   ├── iron-rules.md        # 九条铁律（含质量门禁 + 自主调度）
│   │   ├── plan-format.md       # Plan 工程化格式（含 Dispatch Table）
│   │   └── docs-framework.md    # docs/ 说明书框架规范
│   ├── skills/                  # Skill 定义
│   │   ├── vibecoding-workflow.md  # 核心引擎
│   │   ├── project-bootstrap.md    # 项目初始化
│   │   ├── project-memory.md       # 记忆管理
│   │   ├── writing-plans.md        # Plan 写作
│   │   ├── subagent-driven-development.md  # Subagent 执行
│   │   ├── test-driven-development.md      # TDD
│   │   ├── systematic-debugging.md         # 系统调试
│   │   └── requesting-code-review.md       # 代码审查
│   ├── docs/                    # 框架自身记忆
│   │   ├── PROGRESS.md          # 当前进度
│   │   ├── ARCHITECTURE.md      # 架构记录
│   │   ├── PITFALLS.md          # 踩坑记录
│   │   ├── DECISIONS.md         # 技术决策 (ADR)
│   │   ├── GLOSSARY.md          # 术语表
│   │   └── SESSION_LOG.md       # 会话日志
│   └── plans/                   # 实现计划存档
├── contracts/                   # Agent 角色合约（入参/出参/边界）
│   ├── conductor.md             # 调度者：读 Plan → DAG → 派发
│   ├── architect.md             # 架构师合约
│   ├── coder.md                 # 开发者合约
│   ├── reviewer.md              # 审查者合约
│   ├── tester.md                # 测试者合约
│   └── devops.md                # 运维者合约
├── protocols/                   # Agent 间协议
│   ├── dispatch-table.md        # Dispatch Table 格式规范
│   └── task-output.md           # Task 产出物格式规范
└── templates/                   # 项目模板
    └── plan-with-dispatch.md    # 含 Dispatch Table 的 Plan 模板
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

详见 [`.hermes/rules/iron-rules.md`](.hermes/rules/iron-rules.md)

---

## 两种模式

| 模式 | 触发 | 规则 |
|------|------|------|
| **严格模式**（默认） | 不加标记 | 九条铁律全开 |
| **快速模式** | `@快速模式` | 放宽审查和提交，其余保持 |

---

## 依赖

- **Hermes Agent** — 运行时引擎
- 不需要额外安装任何工具

---

## 贡献

YuanForge 本身也用 YuanForge 开发（自举）。

---

> *驾驭 Agent，而非被 Agent 驾驭。*
