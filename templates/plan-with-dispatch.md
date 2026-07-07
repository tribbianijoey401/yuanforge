# Plan: [功能名称]

> 此模板供 Architect Agent 使用。Plan 写入 `docs/YYYYMMDD-描述/PLAN.md`。

---

## 输入：Product Analyst 产出

| 项 | 内容 |
|----|------|
| 用户故事 | [作为 XX，我想要 YY，以便 ZZ] |
| 验收标准 | [Given/When/Then 格式] |
| 风险标签 | P0 / P1 / P2 |
| 功能优先级 | P0 / P1 / P2 / P3 |

---

## 概况

- **目标:** [一句话描述要交付什么]
- **创建时间:** YYYY-MM-DD
- **Architect:** [产出此 Plan 的 Agent]
- **关联需求:** [用户原始需求摘要]

---

## 设计理解书

> Architect 必须输出此段，提交用户确认后才能进入详细设计。

- **核心实体:** [有哪些主要对象/概念]
- **主要数据流:** [数据从哪来、经过哪、到哪去]
- **关键交互:** [用户/系统如何触发这些流程]

---

## 技术方案

### 技术栈选择

| 层 | 选型 | 原因 |
|----|------|------|
| 语言 | [如 Python 3.11] | [原因] |
| 框架 | [如 FastAPI] | [原因] |
| 数据库 | [如 PostgreSQL] | [原因] |

### 架构决策

[关键决策简述，详细 ADR 见 ADR-NNN.md]

---

## 模块划分

| 模块 | 职责 | 对应 Task | 关键文件 |
|------|------|----------|---------|
| [模块 A] | [职责] | task-NNN | `src/path/` |
| [模块 B] | [职责] | task-NNN | `src/path/` |

---

## Dispatch Plan

Conductor 请按以下方案调度 Agent：

### 依赖关系

- [task-AAA]（[简述]）依赖 [task-BBB] 的 [产出物]，[可否与其他并行]
- [task-CCC]（[简述]）依赖 [task-DDD] 的 [产出物]，[可否与其他并行]

### 任务派发表

| Task ID | 优 | 标题 | Role | 上游依赖 | ⏱超时 | 产出物 | 门禁 | 风险 |
|---------|----|------|------|---------|-------|--------|------|------|
| task-001 | P0 | 需求澄清 | product-analyst | - | 30 | `docs/[会话]/` | G1 | — |
| task-002 | P0 | 架构设计 | architect | task-001 | 120 | `docs/[会话]/PLAN.md` | G1 | — |
| task-003 | P1 | 数据模型 | backend-dev | task-002 | 30 | `src/models/x.py, tests/` | G2 | [P0/P1] |
| task-004 | P1 | API 实现 | backend-dev | task-003 | 30 | `src/api/x.py, tests/` | G2 | [P0/P1] |
| task-005 | P1 | 前端实现 | frontend-dev | task-002 | 30 | `src/ui/X.tsx, tests/` | G2 | [P0/P1] |
| task-006 | P1 | 集成测试 | tester | task-004,task-005 | 20 | `tests/integration/` | G3 | — |
| task-007 | P2 | 文档归档 | doc-engineer | task-006 | 10 | `docs/CHANGELOG.md` | G4 | — |

---

## 质量门禁

| Gate | 检查内容 | 通过标准 | 执行者 |
|------|---------|---------|--------|
| G1 | Plan 完整性 + 用户确认设计理解书 | Dispatch Table 无遗漏、依赖正确、用户确认 | 用户 |
| G2 | 四审查官并行 | 🔴 Blocker 全部解决 | spec-reviewer, security-auditor, quality-auditor, ux-reviewer |
| G3 | 集成测试 | 🟡 Hard Gate — 全量测试 PASS | tester |
| G4 | 文档归档 | Doc Engineer 归档完成 | doc-engineer |
