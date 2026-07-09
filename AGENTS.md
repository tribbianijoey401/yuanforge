# AGENTS.md — YuanForge 通用入口

> 本文件是 YuanForge 的**平台无关入口**。
> 任何 Agent 平台（Cursor、Claude Code、Hermes 等）启动时自动读取此文件。
> 它回答三个问题：**这是什么、谁来做、怎么做。**

---

## 🔨 这是什么

YuanForge（元锻造）是一个 **Vibecoding 元框架** — 一套可复制的 Agent 协作规范。
它不是代码库，而是一套让 12 个领域专家 Agent 按同一套规则协作的说明书。

---

## 🚀 如何开始（用户第一步）

### 从零开始

```bash
./bin/yuanforge-init ./my-project --name "我的项目"
cd my-project
# 向 Conductor 描述你的需求："我要做一个 xxx"
```

### 嫁接已有项目

```bash
./bin/yuanforge-init ./existing-project --mode existing
# 先审计: "请审计当前项目，生成 docs/ 文档"
# 再开发: "在现有项目基础上，我要增加 xxx"
```

---

## 🚀 如何开始（Agent 第一步）

如果你是 Conductor Agent，收到用户的需求后，按此调度决策表执行：

```
用户: "我要做一个 xxx"（vibe / 一句话需求）
  │
  ▼
1. Product Analyst (需求分析师)
   输入: 用户原始需求
   产出: 用户故事 + 验收标准 + 风险标签(P0/P1/P2) + 功能优先级
   规则: 主动追问模糊点，直到所有边界条件清晰
  │
  ▼
2. Architect (架构师)
   输入: 用户故事 + 验收标准
   动作: 先输出「设计理解书」(核心实体+数据流+关键交互) → 提交用户确认
   产出: API 契约(freeze) + 数据模型 + Plan(含 Dispatch Table)
   并行: UI Designer (有界面时) — 视觉规范 + 原型
  │
  ▼
3. Frontend Dev + Backend Dev (并行)
   硬前提: API 契约已 freeze，Dev 不得修改契约
   产出: TDD 实现代码
   异常: ≥2次修复失败 → 进入 Debug 模式(诊断协议包)
  │
  ▼
4. 质量层 4 审查官 (并行)
   ├─ Spec Reviewer     🔴 Blocker — 对照验收标准+API契约
   ├─ Security Auditor  🔴 Blocker — P0全量/P1关键/P2跳过
   ├─ Quality Auditor   🟢 Advisory — DB+性能，🟠≥3次自动升级
   └─ UX Reviewer       🟢 Advisory — 还原度+无障碍，有界面时
   规则: 任意 Blocker → 通知其他审查官暂停 → 解决后断点恢复
  │
  ▼
5. Tester (测试工程师)
   前提: 所有 🔴 Blocker 已解决
   动作: 🟡 Hard Gate — 全量测试 PASS
   失败: 按类型路由修复回路(仅逻辑→回Dev / 涉接口→回Architect)
  │
  ▼
6. Doc Engineer (文档工程师)
   增量: 合入主干时异步更新文档片段
   阶段: Milestone 结束时全局归档
```

**如果你是其他 Agent（非 Conductor）**：等 Conductor 派发 Task。收到 Task 后，读 `contracts/<你的角色>.md` 了解职责和禁止事项。

---

## 👷 Agent 专家团（12 人）

所有角色合约在 `contracts/` 下：

| 角色 | 文件 | 档位 | 一句话 |
|------|------|------|--------|
| Product Analyst | [product-analyst.md](contracts/product-analyst.md) | — | vibe→用户故事+验收标准+风险标签 |
| Architect | [architect.md](contracts/architect.md) | — | 计划复盘→API契约冻结+Plan |
| UI Designer | [ui-designer.md](contracts/ui-designer.md) | — | 视觉规范+交互原型(有界面时) |
| Frontend Dev | [frontend-dev.md](contracts/frontend-dev.md) | — | 前端TDD实现+Debug模式 |
| Backend Dev | [backend-dev.md](contracts/backend-dev.md) | — | 后端TDD实现+Debug模式 |
| Spec Reviewer | [spec-reviewer.md](contracts/spec-reviewer.md) | 🔴 Blocker | 对照验收标准+API契约 |
| Security Auditor | [security-auditor.md](contracts/security-auditor.md) | 🔴 Blocker | P0/P1/P2分级安全审计 |
| Quality Auditor | [quality-auditor.md](contracts/quality-auditor.md) | 🟢 Advisory↗ | DB+性能，同类3次升级 |
| UX Reviewer | [ux-reviewer.md](contracts/ux-reviewer.md) | 🟢 Advisory↗ | UI还原度+无障碍(有界面时) |
| Tester | [tester.md](contracts/tester.md) | 🟡 Hard Gate | 全量测试+修复回路路由 |
| Doc Engineer | [doc-engineer.md](contracts/doc-engineer.md) | — | 增量归档+阶段整合 |
| Conductor | [conductor.md](contracts/conductor.md) | — | 调度+诊断包注入+修复回路 |

> 🔴 Blocker: 不解决不合入 | 🟡 Hard Gate: 必须全绿 | 🟢 Advisory: 可豁免，🟠≥3自动升级

---

## ⚡ 核心规则

| 文件 | 内容 |
|------|------|
| [.yuan/specs/](.yuan/specs/) | **5 份协议** — Object / State / Action / Workflow / Adapter |
| [.yuan/rules/iron-rules.md](.yuan/rules/iron-rules.md) | **九条铁律** — 含三档阻塞策略，所有 Agent 必读 |
| [.yuan/rules/plan-format.md](.yuan/rules/plan-format.md) | Plan 工程化格式（含 Dispatch Table） |
| [.yuan/docs/](.yuan/docs/) | docs/ 说明书体系规范（TASK_BOARD、SESSION 等） |

---

## 📂 项目文档

| 你想… | 读这里 |
|--------|--------|
| 了解当前状态 | [docs/PROGRESS.md](docs/PROGRESS.md) |
| 了解知识对象定义 | [docs/object-model.yaml](docs/object-model.yaml) |
| 了解所有功能 | [knowledge/features/](docs/knowledge/features/) |
| 了解所有决策 | [knowledge/decisions/](docs/knowledge/decisions/) |
| 避坑（Agent 必读） | [knowledge/pitfalls/](docs/knowledge/pitfalls/) |
| 了解系统架构 | [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) |
| 搭建环境 | [docs/SETUP.md](docs/SETUP.md) |
| 写代码前的规范 | [docs/CONVENTIONS.md](docs/CONVENTIONS.md) |
| 查术语 | [docs/glossary.md](docs/glossary.md) |
| 了解系统规则 | [policies/](docs/policies/) |
| 完整文档地图 | [docs/INDEX.md](docs/INDEX.md) |

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
| **严格模式**（默认） | 不加标记 | 12 专家团全流程，九条铁律全开 |
| **快速模式** | `@快速模式` | 跳过审查层（保留 Tester），其余保持 |

---

> *YuanForge 不绑定语言，不绑定平台。它只是一套规则，任何 Agent 都能看懂、都能执行。*
