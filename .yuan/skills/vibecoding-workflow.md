---
name: vibecoding-workflow
description: >
  YuanForge 核心工作流。开发任何功能时加载。触发：用户说「开发」「实现」
  「做项目」「继续」「build」、Phase 1 启动、Plan 确认后进入 Phase 2。
  编排 12 人专家团完整流程：Product Analyst→Architect→Dev→4审查官→Tester→Doc Engineer。
  遵循 5 份协议（.yuan/specs/）+ 十条铁律。Conductor = Workflow Interpreter。
version: 2.0.0
---

# YuanForge 核心工作流

> **这是元框架的 Workflow Protocol 实现。** Conductor = Workflow Interpreter：
> 读 Workspace → 读 Workflow Protocol → 读 State Protocol → 产生 Action → 调 Adapter → 更新 Docs。
> 所有 YuanForge 项目必须遵循此工作流。

---

## 触发条件

用户说以下任何一句时激活：
- "开始开发 XX" / "实现 XX 功能" / "build XX" / "做一个 XX 项目"
- "@严格模式 开发 XX" / "@快速模式 原型 XX" / "继续开发" / "继续上次的"

激活后 **首先加载项目说明书**：`docs/INDEX.md` → `docs/PROGRESS.md`。

---

## Agent 启动：加载最小安全上下文

```
[Agent 启动]
│
├── 1. read_file("docs/PROGRESS.md")               ← 必读：进度（~500B）
│      获悉：当前 Phase/Stage、阻塞项、下一步
│
├── 2. read_file("docs/ARCHITECTURE.md")           ← 必读：架构
│
├── 3. read_file("docs/knowledge/pitfalls/")       ← 必读：踩坑
│      避开已知陷阱
│
├── 4. 如果继续开发（PROGRESS 有进行中 Plan）：
│      读 docs/YYYYMMDD-描述/TASK_BOARD.md
│
└── 5. 继续下面 Phase 流程
```

### 判断是否需要 Phase 0

检查 PROGRESS.md：
- 状态为「初始化」或「空模板」→ **进入 Phase 0（审计）**
- 状态为「就绪」或「开发中」→ **跳过 Phase 0，进入 Phase 1**

---

## Pipeline 总览

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
┌──────────────────────────────────────────────┐
│ Phase 1: 需求分析 (Product Analyst)            │
│                                               │
│ 1. 用户给出 vibe / 一句话需求                  │
│ 2. Product Analyst 产出:                       │
│    - 用户故事                                  │
│    - 验收标准（可验证）                         │
│    - 风险标签(R0/R1/R2)                        │
│ 3. 用户确认                                    │
└────────────────────┬─────────────────────────┘
│
▼
┌──────────────────────────────────────────────┐
│ Phase 2: 方案设计 (Architect)                  │
│                                               │
│ 1. Architect 计划复盘                          │
│ 2. 输出「设计理解书」（核心实体+数据流+交互+推导链）│
│ 3. Conductor 审视推导链 → 用户确认              │
│ 4. API 契约 freeze + 数据模型 + Plan(含 Dispatch Table) │
│ 5. [有界面] UI Designer 并行 → 视觉规范+原型    │
│                                               │
│ [G1: Plan Gate] 用户确认 Plan                  │
└────────────────────┬─────────────────────────┘
│
▼
┌──────────────────────────────────────────────┐
│ Phase 2.5: 设计审查 (Design Reviewer) 🆕      │
│                                               │
│ 审查 API 契约 + 数据模型 + 架构设计:            │
│   ├─ API 契约合理性                           │
│   ├─ 数据模型完整性                           │
│   ├─ 架构设计合理性                           │
│   ├─ 安全设计覆盖                             │
│   └─ 需求覆盖率（AC → Task 映射）              │
│                                               │
│ 🔴 Blocker → 打回 Architect 修正（最多 2 轮）   │
│ ✅ 通过 → 进入 Dev 编码                        │
│                                               │
│ [G1.5: Design Gate] 设计审查通过               │
└────────────────────┬─────────────────────────┘
│
▼
┌──────────────────────────────────────────────┐
│ Phase 3: 开发实现 (Frontend Dev + Backend Dev) │
│                                               │
│ Conductor 初始化 TASK_BOARD → 并行派发:         │
│   - Frontend Dev × N (并行)                    │
│   - Backend Dev × N (并行)                     │
│                                               │
│ 硬前提: API 契约已 freeze + 设计审查已通过      │
│ 异常: ≥2次修复失败 → Debug 模式(诊断协议包)      │
│ 超时回退: 🔨→🟢 (attempts++), ≥3→❌阻塞       │
└────────────────────┬─────────────────────────┘
│
▼
┌──────────────────────────────────────────────┐
│ Phase 4: 质量审查 (4 审查官并行)                │
│                                               │
│ 四个审查官同时启动:                             │
│   ├─ Spec Reviewer     🔴 Blocker             │
│   ├─ Security Auditor  🔴 Blocker (P0/P1/P2)  │
│   ├─ Quality Auditor   🟢 Advisory↗           │
│   └─ UX Reviewer       🟢 Advisory↗           │
│                                               │
│ 审查报告各自独立呈现                            │
│ 任意 Blocker → 通知其他暂停 → 解决后断点恢复     │
│ 🟠 ≥3 → 自动升级 🔴                           │
└────────────────────┬─────────────────────────┘
│
▼
┌──────────────────────────────────────────────┐
│ Phase 5: 测试验证 (Tester)                     │
│                                               │
│ [🟡 Hard Gate] 全量测试 PASS                   │
│ 失败 → 修复回路路由:                            │
│   逻辑 → Dev / 接口→Architect / 依赖→Architect  │
│                                               │
│ [G3: Integration Gate]                        │
└────────────────────┬─────────────────────────┘
│
▼
┌──────────────────────────────────────────────┐
│ Phase 6: 知识蒸馏 (Conductor + Doc Engineer)   │
│                                               │
│ 1. Dispatch(doc-engineer) — 增量归档+阶段整合   │
│ 2. Conductor 蒸馏:                             │
│    - FEATURE → knowledge/features/            │
│    - ADR → knowledge/decisions/               │
│    - BUG → 判断 → knowledge/pitfalls/ 或跳过   │
│    - 未完成任务 → workspace/backlog.md         │
│ 3. Promote → Archive → 重建 Graph              │
│                                               │
│ [G4: Release Gate]                            │
└──────────────────────────────────────────────┘
```

---

## Phase 1: 需求分析（详细）

### 1.1 Product Analyst

**必加载**：`contracts/product-analyst.md` — 角色合约

分析维度：
- **功能需求：** 用户要什么？
- **边界条件：** 什么不算在内？
- **非功能需求：** 性能、安全、可扩展性？
- **风险识别：** R0=高敏 / R1=标准 / R2=低敏

**产出**：用户故事 + 验收标准 + 风险标签
**Gate**：用户确认

---

## Phase 2: 方案设计（详细）

### 2.1 Architect 计划复盘

**必加载**：`contracts/architect.md` + `iron-rules.md`

流程：
1. 读用户故事 + 验收标准
2. 输出「设计理解书」
3. Conductor 审视推导链完整性
4. 用户确认 → API 契约 freeze + Plan(含 Dispatch Table)
5. [有界面] UI Designer 并行

### 2.2 产出 Plan

遵循 `plan-format.md` 规范：
- 定义 Task（含 role/depends/output/timeout）
- Dispatch Table 完整（Architect 必须声明每个 Task 的角色、依赖、产出物）
- Plan 含技术选型理由（写入 ADR）

---

## Phase 3: 开发实现（详细）

### 3.1 Conductor 初始化 TASK_BOARD

- 从 Plan 的 Dispatch Table 提取所有 Task
- 所有 Task 初始状态 = ⏳等待
- 无依赖 Task = 🟢就绪

### 3.2 并行派发

- 所有 🟢就绪 Task 同时派发
- Frontend Dev + Backend Dev 各自独立上下文
- 每个 Dev Agent 加载：角色合约 + TDD skill + 上游产出物 + pitfalls

### 3.3 超时 + 巡检

- Conductor 定期巡检 🔨进行中 的 Task
- 超时 → 🔨→🟢 (attempts++)
- 同任务 3 次超时 → ❌阻塞

### 3.4 Debug 模式

触发：≥2 次修复失败
→ Conductor 注入诊断协议包：隔离复现 → 二分定位 → 假设记录 → 并行通知 Architect

---

## Phase 4: 质量审查（详细）

### 4.1 加载审查官

每个审查官加载对应合约 + 铁律 Ⅲ + 铁律 Ⅷ：

```
Spec Reviewer     → contracts/spec-reviewer.md
Security Auditor  → contracts/security-auditor.md
Quality Auditor   → contracts/quality-auditor.md
UX Reviewer       → contracts/ux-reviewer.md
```

### 4.2 双轨运行

所有审查官同时执行：
- 合规路径：逐条对照验收标准/安全清单/质量规范/UI 原型
- 对抗路径：主动构造边界条件、异常输入、极端场景

### 4.3 审查结果

```
PASS → ✅审查通过 → 下游 🟢就绪
BLOCKER → 🔄返工 → Dev 修复
🟠 Advisory ≥ 3 次 → 自动升级 🔴 Blocker
```

---

## Phase 5: 测试验证（详细）

### 5.1 Tester

- 加载 `tester` agent persona
- 补充集成测试和边界测试
- 🟡 Hard Gate：全量测试 PASS

### 5.2 修复回路

| 问题类型 | 回退 |
|---------|------|
| 仅逻辑错误 | Dev → Tester |
| 涉接口/权限 | Architect + Spec + Security |
| 涉依赖/数据 | Architect + Spec + Quality |

---

## Phase 6: 知识蒸馏（详细）

### 6.0 知识治理（← NF-07 完整路径前置增强）

**Phase 6 蒸馏前必须先完成知识治理。** 加载 `neat-freak` skill 执行：

```
Phase 5 测试通过
  │
  ▼
┌──────────────────────────────────────────────┐
│ Phase 6.0: 知识治理（neat-freak 完整路径）   │
│                                              │
│ 1. 事实面六维验证（NF-02）                   │
│    - 代码/运行态/文档/规则/记忆/工作区        │
│    - 每面标 verified-current/pending/N/A     │
│ 2. 规则链审计（引用 contract-conventions.md「输出格式通用约定」+ distill-workspace Skill）         │
│    - 必备文件/同源/矛盾/死引用/安全红线       │
│ 3. 变更影响路由（NF-09 sync-matrix.md）      │
│    - 9 种代码变化→知识面对照表               │
│ 4. 先减后加地修改（NF §4）                   │
│    - 删过期/合并重复/压缩过载                │
│ 5. 记忆边界控制（NF-16 + 本项目 memory.md）  │
│    - 人工维护记忆可写 / 生成记忆只读          │
│ 6. 发布状态验证（NF-12 状态机）              │
│    - 区分 merged/deployed/live verified      │
│ 7. 标准化汇报（NF-20 模板）                  │
│    - 影响 → 改动/新建 → 待确认 → 遗留        │
└────────────────────┬─────────────────────────┘
```

### 6.1 Doc Engineer

增量：合入主干时异步更新 API/数据/配置/依赖文档
阶段：Milestone 结束 → 概览图+索引+一致性检查

### 6.2 Conductor 蒸馏（← NF-09 变更路由吸收）

1. **CHANGE ROUTE（NF-09）**：根据 6.0 路由结果，识别受影响知识面
2. FEATURE.md → knowledge/features/FEAT-NNN.md
3. ADR → knowledge/decisions/ADR-NNN.md
4. BUG → 会重复 → knowledge/pitfalls/，一次性 → 留在 archive
5. 未完成 → workspace/backlog.md
6. Archive Workspace（含 NF-14 清场前 Gate）
7. 运行 build-graph.py

### 6.3 回环学习

遍历 knowledge/pitfalls/：
- 项目特有 → 留在此文件
- 领域通用 → 提炼为 Skill
- 框架通用 → 反馈到 YuanForge

---

## 铁律执行

| 铁律 | 执行点 |
|------|--------|
| Ⅰ. 计划先行 | Phase 2 产 Plan |
| Ⅱ. TDD 先行 | 每个 Task 内 Red → Green → Refactor |
| Ⅲ. 三档审查 | Phase 4 四审查官并行 |
| Ⅳ. 原子提交 | 每个 Task 一个 Commit |
| Ⅴ. 上下文隔离 | 每个 Task 新 Subagent |
| Ⅵ. 文档即代码 | Phase 2 写决策，Phase 6 蒸馏更新 |
| Ⅶ. 渐进式交付 | Task 顺序保证可运行 |
| Ⅷ. 质量门禁 | G1→G2→G3→G4 |
| Ⅸ. 自主调度 | Conductor 按调度循环派发 |
| Ⅹ. 循环收敛 | 每个循环必须有闸门，不得"直到正确为止" |

---

## 两种模式

| 模式 | 触发 | 门禁 |
|------|------|------|
| 严格模式（默认） | 不加标记 | G1+G2+G3+G4 全开，12 专家团全流程 |
| 快速模式 | `@快速模式` | 仅 G1 + 跳过 Phase 4（保留 Tester） |

---

## 相关 Skill

- `project-audit` — 审计现有项目（Phase 0）
- `project-bootstrap` — 项目初始化（含嫁接模式）
- `writing-plans` — Plan 写作规范
- `subagent-driven-development` — Subagent 执行引擎
- `test-driven-development` — TDD 纪律
- `requesting-code-review` — 四审查官并行审查
- `promotion` — 知识晋升管线
- `grilling` — 结构化逼问循环
- `debug-feedback-loop` — Debug 诊断协议包
