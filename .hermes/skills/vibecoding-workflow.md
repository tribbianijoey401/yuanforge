---
name: vibecoding-workflow
description: "YuanForge 核心工作流引擎：从需求到交付的完整编排"
version: 1.0.0
---

# YuanForge 核心工作流

> **这是元框架的「引擎」** — 定义了从用户需求到可交付代码的完整流程。
> 所有 YuanForge 项目必须遵循此工作流。

---

## 触发条件

用户说以下任何一句时激活：
- "开始开发 XX"
- "实现 XX 功能"
- "build XX"
- "做一个 XX 项目"
- "@严格模式 开发 XX"
- "@快速模式 原型 XX"

---

## 完整流程

```
用户需求
   │
   ▼
┌──────────────────────────────────────────────┐
│ Phase 1: 架构 (Architect)                     │
│                                               │
│ 1. 加载 iron-rules.md（铁律入脑）             │
│ 2. 加载 architect agent persona               │
│ 3. 分析需求 → 技术选型 → 架构设计             │
│ 4. 产出 Implementation Plan                   │
│ 5. 保存到 .hermes/plans/                      │
│                                               │
│ 输出：Plan + 技术选型理由                      │
└────────────────────┬─────────────────────────┘
                     │
                     ▼
              用户确认 Plan？
                     │
            ┌────────┴────────┐
            │ 否              │ 是
            ▼                 ▼
      修改 Plan       ┌──────────────────────────────┐
                      │ Phase 2: 执行 (Conductor)      │
                      │                               │
                      │ 加载 subagent-driven-dev skill │
                      │                               │
                      │ for each Task in Plan:        │
                      │   ┌──────────────────────┐    │
                      │   │ 2a. Coder (TDD 实现)  │    │
                      │   │ 2b. Reviewer (Spec)   │──┐ │
                      │   │    ├─ PASS → next     │  │ │
                      │   │    └─ FAIL → fix → 2b │  │ │
                      │   │ 2c. Reviewer (Quality)│  │ │
                      │   │    ├─ APPROVED → next │  │ │
                      │   │    └─ REJECT → fix→2c │  │ │
                      │   └──────────────────────┘    │
                      └──────────────┬───────────────┘
                                     │
                                     ▼
                      ┌──────────────────────────────┐
                      │ Phase 3: 收尾                   │
                      │                               │
                      │ 1. Tester — 补充集成测试       │
                      │ 2. DevOps — 配置 CI/CD         │
                      │ 3. 更新项目文档                 │
                      └──────────────────────────────┘
```

---

## Phase 1: 架构阶段（详细）

### 1.1 加载上下文

```markdown
必加载：
- `.hermes/rules/iron-rules.md`  — 铁律
- `.hermes/agents/architect.md`  — 架构师角色

按需加载：
- 对应技术栈 skill（如 python-fastapi）
- `.hermes/docs/ARCHITECTURE.md`  — 现有架构
- `.hermes/docs/DECISIONS.md`    — 已有技术决策
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
- 记录理由 — 每个选型写入 DECISIONS.md

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

保存路径：`.hermes/plans/YYYY-MM-DD_HHMMSS-<feature-slug>.md`

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
Step A: 派 Coder (新 subagent)
  → 加载 coder agent persona + TDD skill
  → 提供 Task 完整上下文
  → 执行 TDD → 原子提交

Step B: Gate G2-TASK — Spec Review
  → 加载 reviewer agent persona
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

- 加载 `devops` agent persona
- 配置 GitHub Actions 或等价 CI
- 编写 Dockerfile / docker-compose

### 3.3 文档更新

- 更新 `ARCHITECTURE.md`（如有架构变更）
- 更新 `DECISIONS.md`（如有新决策）
- 更新 `GLOSSARY.md`（如有新术语）

---

## 铁律执行

本 Skill 整个流程严格遵守 YuanForge 七条铁律：

| 铁律 | 执行点 |
|------|--------|
| Ⅰ. 计划先行 | Phase 1 产 Plan，Phase 2 才开始 |
| Ⅱ. TDD 先行 | 每个 Task 内 Red → Green → Refactor |
| Ⅲ. 两阶段审查 | 每个 Task 后 Spec Review → Quality Review |
| Ⅳ. 原子提交 | 每个 Task 一个 Commit |
| Ⅴ. 上下文隔离 | 每个 Task 新 Subagent |
| Ⅵ. 文档即代码 | Phase 1 写 DECISIONS，Phase 3 更新文档 |
| Ⅶ. 渐进式交付 | Task 顺序保证每步可运行 |

---

## 相关 Skill

- `writing-plans` — 写 Implementation Plan
- `subagent-driven-development` — Subagent 执行引擎
- `test-driven-development` — TDD 纪律
- `requesting-code-review` — 代码审查
- `project-bootstrap` — 项目初始化
- `project-memory` — 项目记忆管理
