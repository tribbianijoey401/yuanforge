---
name: vibecoding-workflow
description: >
YuanForge 核心工作流引擎。开发任何功能时加载。触发：用户说「开发」「实现」
「做项目」「继续」「build」、Phase 1 启动、Plan 确认后进入 Phase 2。
编排 12 人专家团完整流程：Product Analyst→Architect→Dev→4审查官→Tester→Doc Engineer。
读写：PROGRESS（进度）、features/（功能文档）、decisions/（决策）、
pitfalls（踩坑）、bugs/（Bug 记录）。所有 Agent 的调度中心。
version: 1.0.0
---

# YuanForge 核心工作流

> **这是元框架的「引擎」** — 定义了从用户需求到可交付代码的完整流程。
> 所有 YuanForge 项目必须遵循此工作流。

---

## 触发条件

用户说以下任何一句时激活：
- "开始开发 XX" / "实现 XX 功能" / "build XX" / "做一个 XX 项目"
- "@严格模式 开发 XX" / "@快速模式 原型 XX" / "继续开发" / "继续上次的"

激活后 **首先加载项目说明书**：`docs/INDEX.md` → `docs/PROGRESS.md`。

---

## 完整流程

### Agent 启动：加载项目说明书

```
[Agent 启动]
│
├── 1. read_file("docs/INDEX.md")                  ← 必读：入口
├── 2. read_file("docs/PROGRESS.md")               ← 必读：进度
│      获悉：当前 Phase/Stage/Task、阻塞项、下一步
│
├── 3. read_file("docs/ARCHITECTURE.md")           ← 必读：架构
│      了解系统全貌
│
├── 4. read_file("knowledge/pitfalls/")                 ← 必读：踩坑
│      避开已知陷阱
│
├── 5. 如果是继续开发（PROGRESS 显示有进行中 Plan）：
│      read_file(".yuan/plans/当前 Plan")
│
└── 6. 继续下面 Phase 流程
```

### 判断是否需要 Phase 0

检查 PROGRESS.md：
- 状态为「初始化」或「空模板」→ **进入 Phase 0（审计）**
- 状态为「就绪」或「开发中」→ **跳过 Phase 0，进入 Phase 1**

### Pipeline 总览

```
用户需求 / 已有项目
│
▼
┌──────────────────────────────────────────────┐
│ Phase 0: 审计（仅首次 / 嫁接项目）              │
│                                               │
│ 加载 project-audit skill                       │
│                                               │
│ 1. 覆盖扫描 — 文件树、技术栈、Git 历史         │
│ 2. 架构分析 — 模块、数据流、入口点             │
│ 3. 功能盘点 — 列出所有端点/功能                │
│ 4. 决策回溯 — 从代码反推选型原因               │
│ 5. 填充说明书 — ARCHITECTURE/PROGRESS/...     │
│ 6. 差异报告 — docs vs 代码                     │
│ 7. PROGRESS → 就绪                             │
└────────────────────┬─────────────────────────┘
│
▼
[Phase 0: 审计完成]
│
▼
┌──────────────────────────────────────────────┐
│ Phase 1: 架构 (Architect)                     │
│                                               │
│ 1. 加载 iron-rules.md（铁律入脑）             │
│ 2. 加载 architect agent persona               │
│ 3. 分析需求 → 技术选型 → 架构设计             │
│ 4. 产出 Implementation Plan                   │
│ 5. 保存到 .yuan/plans/                      │
│ 6. 更新 PROGRESS.md、decisions/ 决策记录       │
│                                               │
│ 输出：Plan + 技术选型理由                      │
└────────────────────┬─────────────────────────┘
│
▼
[G1: Plan Gate]
│
用户确认 Plan？
│
┌────────┴────────┐
│ 否              │ 是
▼                 ▼
修改 Plan       ┌──────────────────────────────┐
│ Phase 2: 执行 (Conductor)      │
│                               │
│ 加载 subagent-driven-dev skill + 读取 TASK_BOARD.md 找 🟢就绪 任务 │
│                               │
│ for each Task in Plan:        │
│   ┌──────────────────────┐    │
│   │ 2a. Coder (TDD 实现)  │    │
│   │ 2b. G2 Spec Review    │──┐ │
│   │    ├─ PASS → next     │  │ │
│   │    └─ FAIL → fix → 2b │  │ │
│   │ 2c. G2 Quality Review │  │ │
│   │    ├─ APPROVED → next │  │ │
│   │    └─ REJECT → fix→2c │  │ │
│   └──────────────────────┘    │
│                               │
│ 每个 Task 后更新 TASK_BOARD.md（状态 + 上下文传递），然后更新 PROGRESS.md     │
│ 踩坑立即记录 knowledge/pitfalls/（蒸馏时 Conductor 生成）         │
└──────────────┬───────────────┘
│
[G3: Integration Gate]
│
▼
┌──────────────────────────────┐
│ Phase 3: 收尾                   │
│                               │
│ 1. Tester — 补充集成测试       │
│ 2. DevOps — 配置 CI/CD         │
│ 3. 更新 ARCHITECTURE / decisions/ / docs   │
└──────────────┬───────────────┘
│
[G4: Release Gate]
│
▼
┌──────────────────────────────┐
│ Phase 4: 回顾 (Retrospector)    │
│                               │
│ 1. 遍历 knowledge/pitfalls/ 和当前会话文件夹中的 BUG 记录      │
│ 2. 判断每个坑：                 │
│    ├── 本项目特有 → 留在此文件  │
│    ├── 领域通用 → 提炼为 Skill  │
│    └── 框架通用 → 反馈到 Yuan   │
│ 3. 记录 SESSION_LOG.md          │
│ 4. 更新 PROGRESS.md → 已交付    │
└──────────────────────────────┘
```

---

## Phase 1: 架构阶段（详细）

### 1.1 加载上下文

```markdown
必加载：
- `.yuan/rules/iron-rules.md`  — 铁律
- `contracts/architect.md`  — 架构师角色

按需加载：
- 对应技术栈 skill（如 python-fastapi）
- `docs/ARCHITECTURE.md`  — 现有架构
- 当前会话文件夹中的 ADR — 已有技术决策
```

### 1.2 需求分析

分析维度：
- **功能需求：** 用户要什么？
- **边界条件：** 什么不算在内？
- **非功能需求：** 性能、安全、可扩展性？
- **约束条件：** 时间、资源、技术限制？

### 1.3 技术选型

选择原则：
- 语言无关 — 按任务选最合适的栈
- 简单优先 — 能用简单的不用复杂的
- 记录理由 — 每个选型写入 `decisions/`

### 1.4 架构设计

输出：
- 系统架构概述（2-3 句）
- 模块划分
- 数据流
- 目录结构

### 1.5 产出 Plan

遵循 `plan-format.md` 的 Pipeline-as-Code 规范：
- 定义 **Stage**（每个 Stage = 一组 Task + 一个 Gate）
- 每个 Task 包含：`Objective` / `Files` / `Input` / `Output` / `Test` / `Gate Check`
- 每个 Stage 出口定义 **Gate**：`Pass Criteria` + `Fail Action`
- 标注 `Pitfalls`（已知陷阱，从经验中提取）

保存路径：`.yuan/plans/YYYY-MM-DD_HHMMSS-<feature-slug>.md`

### 1.6 用户确认

展示 Plan 摘要，等待用户确认或修改。

---

## Phase 2: 执行阶段（详细）

### 2.1 加载 Conductor 模式

使用 `subagent-driven-development` skill 执行 Plan：
- 读 Plan 文件一次，提取所有 Task
- 创建 TODO 列表追踪进度

### 2.2 逐 Task 执行（含 Gate）

对每个 Task：

```
Step A: 派 Dev (新 subagent)
→ 加载 frontend-dev 或 backend-dev agent persona + TDD skill
→ 提供 Task 完整上下文
→ 执行 TDD → 原子提交

Step B: Gate G2 — 四审查官并行审查
→ 加载 spec-reviewer / security-auditor / quality-auditor / ux-reviewer agent persona
→ 对照 Plan 检查实现
→ PASS → 进入 Step C
→ FAIL → Coder 修复 → 重新审查
→ 同一 Task 连续 3 次 FAIL → 触发架构复盘

Step C: Gate G2-TASK — Quality Review
→ 代码质量审查
→ APPROVED → 标记 Task 完成 `[G2 ✓]`
→ REJECT → Coder 修复 → 重新审查

Step D: Stage Gate 检查
→ 当前 Stage 所有 Task 完成？
→ 是 → 执行 Stage Gate（G1/G3/G4）
→ 否 → 下一个 Task
```

### 2.3 快速模式

`@快速模式` 下：
- 跳过 Step B（Spec Review）
- Step C 只检查 Critical Issues
- 允许多个 task 合并提交

---

## Phase 3: 收尾阶段（详细）

### 3.1 集成测试

- 加载 `tester` agent persona
- 补充集成测试和边界测试
- 运行完整测试套件

### 3.2 CI/CD 配置

- 由 Conductor 执行 DevOps 交付模式（暂不开发独立 Agent）
- 配置 GitHub Actions 或等价 CI
- 编写 Dockerfile / docker-compose

### 3.3 文档更新

- 更新 `docs/ARCHITECTURE.md`（如有架构变更）
- 更新当前会话文件夹中的 ADR（如有新决策）
- 更新 `docs/glossary.md`（如有新术语）

---

## Phase 4: 回顾阶段（详细）

> Harness 的回环学习在此落地。

### 4.1 遍历踩坑记录

加载 knowledge/pitfalls/ 和当前会话文件夹中的 BUG 记录，逐条检查「归档判断」：

```
for each PIT in pitfalls.md:
if PIT.归档判断 == "本项目特有":
→ 留在此文件，不操作

if PIT.归档判断 == "提炼为 Skill":
→ 如果是新领域 → skill_manage(action='create', ...)
→ 如果是已有 Skill 的补充 → skill_manage(action='patch', ...)
→ 在 knowledge/pitfalls/PIT-NNN.md 中标注「已归档至 Skill: <name>」

if PIT.归档判断 == "反馈到 Yuan":
→ 评估是否需要修改铁律或流程 Skill
→ 修改后提交到 YuanForge 仓库
```

### 4.2 写会话日志

追加 `SESSION_LOG.md`：
```markdown
### Session N: YYYY-MM-DD — [项目名] 交付

- **完成:** 所有 Phase 1-3
- **决策:** 见 decisions/
- **踩坑:** PIT-001, PIT-002
- **Skill 提炼:** [如有]
- **Commit:** abc1234
```

### 4.3 更新进度

`docs/PROGRESS.md` 状态更新为「已交付」。

---

## 铁律执行

本 Skill 整个流程严格遵守 YuanForge 九条铁律：

| 铁律 | 执行点 |
|------|--------|
| Ⅰ. 计划先行 | Phase 1 产 Plan |
| Ⅱ. TDD 先行 | 每个 Task 内 Red → Green → Refactor |
| Ⅲ. 两阶段审查 | 每个 Task 后 Spec → Quality |
| Ⅳ. 原子提交 | 每个 Task 一个 Commit |
| Ⅴ. 上下文隔离 | 每个 Task 新 Subagent |
| Ⅵ. 文档即代码 | Phase 1 写决策，Phase 3 更新文档 |
| Ⅶ. 渐进式交付 | Task 顺序保证可运行 |
| Ⅷ. 质量门禁 | G1→G2→G3→G4，Phase 4 归档 |

---

## 相关 Skill

- `project-audit` — 审计现有项目（Phase 0）
- `writing-plans` — 写 Implementation Plan
- `subagent-driven-development` — Subagent 执行引擎
- `test-driven-development` — TDD 纪律
- `requesting-code-review` — 代码审查
- `project-bootstrap` — 项目初始化（含嫁接模式）
- `project-memory` — 项目记忆管理
