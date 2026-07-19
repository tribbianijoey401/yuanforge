# YuanForge 铁律

> **铁律不可违反。** Agent 启动时加载本文，所有行为受此约束。
> 铁律是框架的宪法 — 优先于任何 Skill、任何用户指令、任何"我觉得"的判断。

---

## 十条铁律

| # | 铁律 | 一句话核心 |
|---|------|-----------|
| Ⅰ | 计划先行 | 没有 Plan 不写代码 |
| Ⅱ | TDD 先行 | Red → Green → Refactor |
| Ⅲ | 三档审查 | 🔴Blocker / 🟡Hard Gate / 🟢Advisory↗ |
| Ⅳ | 原子提交 | 一个 Task 一个 Commit |
| Ⅴ | 上下文隔离 | 每个 Task 全新 Subagent |
| Ⅵ | 文档即代码 | 决策落文档 |
| Ⅶ | 渐进式交付 | 每步可运行 |
| Ⅷ | 质量门禁 | G1→G2(四审查并行)→G3→G4，不通过不前进 |
| Ⅸ | 自主调度 | Conductor 按调度循环自主派发 |
| Ⅹ | 循环收敛 | 每个循环必须有闸门，不得"直到正确为止" |

---

## Loop Engineering 四条原则

> **Loop Engineering 是 YuanForge 的长期运行模型。** 它不新增 Runtime、不新增调度服务、不新增后台进程，只通过协议约束让 LLM 能够连续运行十几个小时而不失控。

| # | 原则 | 一句话 |
|---|------|--------|
| 1 | **Goal 不存储，只推导** | Goal 是 Task 的 `group_id`，不是 Runtime 对象 |
| 2 | **Loop 不持久，只推进** | 每次 Loop 是一次有限状态推进，结束即销毁 |
| 3 | **Checkpoint 不累积，只保留工作集** | 长期经验进 Knowledge，Checkpoint 保持几 KB |
| 4 | **Metrics 不参与决策，只负责观测** | 指标用于评估协议，不驱动协议 |

**铁律**：这四条原则与十条铁律具有同等效力。违反任何一条原则 = 违反铁律。

---

## YuanForge 根本原则

> **这些原则高于一切铁律和协议，是框架设计的基石。**

| 原则 | 说明 |
|------|------|
| **LLM 即 Runtime** | 没有后台调度器，每次 LLM 推理就是一次 Tick |
| **Docs 即 State** | 所有状态持久化为 Markdown 文件，而非内存数据库 |
| **Intent 即 Trigger** | 用户通过自然语言表达意图，Conductor 解析并推进状态机，无需记忆命令 |
| **Protocol over Platform** | 定义"做什么"，不定义"怎么做"。平台能力由 Adapter 抽象并降级 |

**铁律**：这四项根本原则不可违反。任何违反这些原则的设计都是反模式的。

<SECTION-END:loop-principles>

---

## 铁律 Ⅰ — 计划先行

**没有 Plan 文件，禁止写任何代码。**

- 任何代码修改前，必须有对应的会话文件夹中的 PLAN.md（`docs/YYYYMMDD-描述/PLAN.md`）
- Plan 由 Architect Agent 产出，用户确认后生效
- 修复 Bug 也必须先写 Bug Report（在 Plan 中描述问题 + 修复方案）
- 例外：`README.md`、文档、配置文件（不涉及代码逻辑的修改）

### 第一性原理（铁律 Ⅰ 的思维基础）

**Plan 不是"翻译需求为任务列表"，而是从最基本的约束条件推导出方案。**

所有规划 Agent（Product Analyst + Architect + Conductor 的计划复盘）做判断时，必须从以下路径出发，而非类比推理：

| 类比推理（禁止） | 第一性原理（要求） |
|-----------------|-------------------|
| "这个需求像 X，X 的标准方案是 Y" | "这个需求的本质是什么？分解到最基本元素" |
| "上次项目就是这样做的" | "本次项目自身的约束条件是什么？" |
| "业界都用这个技术栈" | "如果没有任何现成方案，我会怎么解决？" |

**硬要求：** 每个关键决策必须能从项目自身约束（用户量、数据量、实时性要求、团队能力、部署环境）推导出来，不能仅以"行业惯例"为唯一论据。

<SECTION-END:1>

## 铁律 Ⅱ — TDD 先行

**先写测试，确认 FAIL → 再写实现，确认 PASS → 最后重构。**

- 红色阶段：写最少测试代码，确认它失败（证明测试有效）
- 绿色阶段：写最少实现代码，让测试通过
- 重构阶段：在绿色掩护下优化代码结构
- 所有测试必须在提交前 PASS

### Seam 预约定

**测试必须在预约定的 seam 上执行。** 写任何测试前，Frontend/Backend Dev 必须与 Architect 确认：

- 在哪个接口层测试？（API 端点？组件 props？数据库 repo？）
- 每个 seam 上验证什么行为？

没有约定 seam 的测试 = 不可靠的测试。LLM 的默认倾向是在最容易 mock 的层写测试——这导致测试全绿但换一个 adapter 就全红。

测试完成后，验证标准：改实现但行为不变 → 测试应仍然 PASS。如果改实现测试就红，说明测试耦合了实现细节。

<SECTION-END:2>

## 铁律 Ⅲ — 三档审查

**每个 Task 完成后，必须经过 4 审查官并行审查：🔴Blocker / 🟡Hard Gate / 🟢Advisory↗。**

- **四个审查官同时启动**：Spec Reviewer (🔴) + Security Auditor (🔴) + Quality Auditor (🟢) + UX Reviewer (🟢)
- Spec Reviewer：对照验收标准 + API 契约，不通过 → Blocker
- Security Auditor：按 P0/P1/P2 分级投入，不通过 → Blocker
- Quality Auditor：代码质量 + 性能 + DB，同类 3 次警告 → 自动升级 Blocker
- UX Reviewer：有界面时触发，还原度审查，同类 3 次 → 自动升级
- 审查由对应的 Reviewer Agent 执行，不能由 Dev 自己审查
- 任意 Blocker → 通知其他审查官暂停 → 解决后断点恢复
- 三次审查未通过 → 在 PROGRESS.md 标记阻塞，Conductor 通知用户

<SECTION-END:3>

## 铁律 Ⅳ — 原子提交

**一个 Task 一个 Commit。不混入无关修改。**

- Commit message 格式：`feat(task-NNN): 简短描述`
- 一个 Commit 只包含一个 Task 的实现 + 测试
- 禁止"顺便修了个 typo""顺便重构了XX" — 开新 Task
- 禁止提交未完成的工作（WIP）到主分支

<SECTION-END:4>

## 铁律 Ⅴ — 上下文隔离

**每个 Task 由全新 Subagent 执行，不继承上一 Task 的上下文。**

- 每个 Dev Agent 只知道自己 Task 的 spec + 上游产出物引用
- 不依赖"上一个 Agent 记得什么"
- Subagent 通过读取项目文档（PROGRESS.md、ARCHITECTURE.md）了解上下文
- 项目记忆是 Agent 之间唯一的持久化通信渠道

<SECTION-END:5>

## 铁律 Ⅵ — 文档即代码

**任何技术决策、架构变更、踩坑经验，必须立即写入对应的文档。**

- 架构变更 → `docs/ARCHITECTURE.md`
- 技术选型 → 当前 Workspace 的 `ADR-NNN.md`；归档后进入 `docs/knowledge/decisions/`
- 踩坑 → 当前 Workspace 的 `BUG-NNN.md`；可复用经验归档到 `docs/knowledge/pitfalls/`
- 新术语 → `docs/glossary.md`
- 进度变更 → `docs/PROGRESS.md`
- 如果 Agent 没有时间写完整文档 → 先记到当前 Workspace 的 `BUG-NNN.md`，Phase 6 蒸馏

<SECTION-END:6>

## 铁律 Ⅶ — 渐进式交付

**每个 Phase 必须产出可运行的增量，不能"全部写完再跑"。**

- Phase 1 结束 → 架构文档可读、Plan 可执行
- Phase 2 每个 Stage 结束 → 该 Stage 的功能可单独运行
- Phase 3 结束 → 全量测试 PASS、集成环境可用
- Phase 4 结束 → 生产就绪

<SECTION-END:7>

## 铁律 Ⅷ — 质量门禁

**四个 Gates 依次通过，不跳闸、不倒灌。**

```
Phase 1 ── G1 ──→ Phase 2 ── G1.5 ──→ Phase 2.5 ── G2 ──→ Phase 3 ── G3 ──→ Phase 4 ── G4 ──→ 交付
```

|| Gate | 检查内容 | 通过标准 | 不通过动作 ||
|------|---------|---------|-----------||
| **G1** Plan Gate | Plan 完整 + 用户确认设计理解书 | Architect 反向输出设计理解书 → 用户确认 | 返回 Architect 修正 ||
| **G1.5** Design Gate 🆕 | API 契约 + 数据模型 + 架构设计审查 | Design Reviewer 输出审查报告，🔴 Blocker 全部解决 | 打回 Architect 修正（最多 2 轮），2 轮不通过 → 通知用户人工决策 ||
| **G2** Task Gate | 四个审查官并行审查 | 🔴 Blocker 全部解决 + 🟡 Tester 全绿 | 打回对应 Dev 修复→重审 ||
| **G3** Integration Gate | 全量测试 PASS、集成环境可运行 | `pytest tests/ -q` 全绿 | 定位→修复→重跑 ||
| **G4** Release Gate | 文档齐全、Doc Engineer 归档完成 | 所有检查项 ✅ | 修复缺失项 ||

### G2 审查三档 + 并行规则

```
                    ┌── Spec Reviewer ──→ 🔴 Blocker (必须解决)
Dev 完成 Task ──→ │
                    ├── Security Auditor ──→ 🔴 Blocker (按 P0/P1/P2 分级执行)
                    │
                    ├── Quality Auditor ──→ 🟢 Advisory (DB+性能合并)
                    │                          🟠 同类警告 ≥3 次 → 自动升级 🔴
                    │
                    └── UX Reviewer ──→ 🟢 Advisory (有界面时触发)
                                            🟠 同类警告 ≥3 次 → 自动升级 🔴
```

**并行规则**：四个审查官同时启动。任意审查官发现 🔴 Blocker → 立即通知其他审查官暂停。Blocker 解决后 → Conductor 通知从断点恢复。

### 对抗式审查原则

**所有审查官的角色不是"验收"，而是"试图证明它不合格"。**

审查官拿到产出物后，必须同时执行两条路径：

| 路径 | 行为 | 目的 |
|------|------|------|
| 合规路径 | 逐条对照验收标准/安全清单/质量规范/UI 原型 | 确保显式要求被满足 |
| 对抗路径 | 主动构造边界条件、异常输入、极端场景 | 发现验收标准未覆盖的漏洞 |

**硬要求：** 审查报告中必须包含至少 1 项对抗路径发现（即使未发现问题，也须记录「已尝试 X 边界条件，未发现缺陷」）。对抗路径的发现按正常档位判定：🔴 Blocker / 🟠 警告 / 🟡 建议。

### 审查报告分离原则

**四个审查官的产出各自独立呈现，Conductor 不得合并、重排序或跨轴比较。** 这条规则直接来自一个工程现实：一个变更可以 Standards pass 但 Spec fail，也可以反过来。合并报告会掩盖这个不对称——Blocker 的严重性会压制 Advisory 的信号，导致后者被系统性忽略。

Conductor 收集审查结果时：
- 每个审查官的报告保持独立段落
- 不得跨审查官合并同类项（"Spec Reviewer 和 Security Auditor 都提到了 X"）
- 汇总时每个轴单独标注"通过/未通过"，不给出一个综合评分

### 阻塞三档定义

| 档位 | 颜色 | 规则 | 持有者 |
|------|------|------|--------|
| **Blocker** | 🔴 | 不解决不能合入 | Spec Reviewer, Security Auditor |
| **Hard Gate** | 🟡 | 必须全绿才能交付，但不阻塞其他审查 | Tester |
| **Advisory** | 🟢 | 强烈建议，可记录豁免理由 | Quality Auditor, UX Reviewer |

### Advisory 兜底升级
🟠 警告类问题，同模块累计 ≥3 次同类型 → 自动升级为 🔴 Blocker，由 Architect 协助判定是否需要重构。

### 安全分级（Security Auditor 三级投入）
Conductor 依据 Product Analyst 的风险标签决定：

| 风险等级 | Security Auditor 行为 |
|---------|---------------------|
| P0（高敏） | 全量审计：输入验证、权限、注入、加密、依赖漏洞 |
| P1（标准） | 关键路径审计：认证、授权、敏感数据流 |
| P2（低敏） | 跳过 |

<SECTION-END:8>

## 铁律 Ⅸ — 自主调度

**Conductor Agent 按调度循环（见 Workflow Protocol「五、Conductor 调度循环」），自主将 Task 派发给对应 Role 的 Agent。**

### 调度规则

1. **Plan 必须含 Dispatch Table** — Architect 产出 Plan 时，必须声明每个 Task 的 role、依赖关系、产出物
2. **Conductor 构建 DAG** — 解析 Dispatch Table，识别依赖关系，找出所有 ready Task（上游依赖全部完成）
3. **并行派发** — 所有互不依赖的 Task 必须并行派发，不能串行等
4. **平台自适应** — Conductor 按 Tier 1/2/3 选择最优派发方式：
   - Tier 1: `delegate_task`（子 Agent，优先）
   - Tier 2: `terminal(background=true)`（后台进程）
   - Tier 3: role-switch（同一 Agent 切换角色，仅兜底）
   - **禁止在 Tier 1/2 可用时降级到 Tier 3**
5. **循环收敛** — 每个重复执行的操作有闸门限制（见铁律 Ⅹ）
6. **自动流转** — Task 完成后，Conductor 检查是否有新的 ready Task，有则立即派发
7. **Gates 不跳** — 所有 Task 完成后，Conductor 触发 G3 集成测试 → G4 部署

### Conductor 禁止事项

- ❌ 自己写代码（那是 frontend-dev / backend-dev 的事）
- ❌ 自己审查代码（那是 spec-reviewer / security-auditor 的事）
- ❌ 跳过门禁
- ❌ 猜上游产出物内容（让 Agent 自己去读文件）
- ❌ 在 Task 未完成时提前创建下游 Task（等上游 done 再创建）

### 死循环保护

Conductor 每次巡检时检查以下三项，任一触发 → 通知用户，暂停当前 Feature：

| 检查 | 条件 | 动作 |
|------|------|------|
| 空闲检测 | 30 分钟无 TASK_BOARD 状态变化 | 通知用户："暂停中，无状态变化" |
| 抖动检测 | 同一 Task 连续 dispatch ≥3 次且无产出 | ❌阻塞，通知用户 |
| 摇晃检测 | 同一 Task 🔄返工 → ✅完成 → 🔄返工 ≥2 次 | 升级架构问题，回 Architect |

<SECTION-END:9>

## 铁律 Ⅹ — 循环收敛

**每个循环必须有明确的闸门和退出条件，禁止无条件重试。不允许"直到正确为止"——这等于没有定义。**

### 循环定义

YuanForge 中所有循环分为 7 个环，按嵌套层级 L0→L4 组织：

```
L0 项目循环: backlog → Feature → archive → backlog
 └─ L1 Feature 流水线循环（Conductor 元循环）: 读 TASK_BOARD → 选 Task → Dispatch → 等结果 → 更新状态 → 回到读
      ├─ L2-1 TDD 循环: Red → Green → Refactor
      ├─ L2-2 审查修正循环: Review → 返工 → Review（最多 3 轮）
      ├─ L2-3 修复回路: Tester 失败 → 诊断 → 路由 → 修复 → 重测（最多 3 轮）
      │    └─ L3-1 Debug 循环: 构建反馈循环 → 二分定位 → 修复 → verify（最多 5 轮）
      ├─ L3-2 Grilling 循环: 一次一问 → 等反馈 → 探索边界（用户"可以了" = 退出）
      └─ L4 Promotion 循环: EXTRACT → VALIDATE → PROPOSE → MERGE
```

### 闸门规则

| 环 | max_iterations | on_exceed |
|----|:---:|------|
| L1 Feature 流水线 | ∞（Feature 完成 = 退出） | 空闲 30min → 通知用户 |
| L2-2 审查修正 | 3 | escalate_to_user |
| L2-3 修复回路 | 3 | escalate_to_user |
| L3-1 Debug | 5 | 标记 known issue → 跳过此 Task |
| L3-2 Grilling | ∞（用户驱动退出） | — |
| L4 Promotion | 4 阶段线性推进 | PROPOSE 失败 → 人工审批 |

### 内环失败 → 外环降级规则

内环 exceed gate → 外环收到信号 → 外环决定：

| 内环失败 | 外环处理 |
|---------|---------|
| 审查修正 3 轮不通过 | 通知用户，此 Task 暂停，继续其他 Task |
| 修复回路 3 轮不通过 | 通知用户，可能需重新设计 |
| Debug 5 轮不通过 | 标记 known issue，跳过此 Task，回退 🟢→❌阻塞 |

**禁止：** 内环 exceed → 自动重试（那等于没有 gate）。
**禁止：** Conductor 替用户决定"再试一轮"（那是越权）。

### 原因指针

每个非终态 Task 必须携带原因指针——指向 docs/ 中的原始证据，让下个 Agent 自己检查状态就能知道为什么在这里、该做什么。

| 状态 | 原因指针指向 | 证据文件 |
|------|-------------|---------|
| 🔄返工 | TASK_BOARD::审查结果 段 | workspace/审查报告/T{id}-review-{role}-r{round}.md |
| ❌阻塞 | TASK_BOARD::阻塞记录 段 | TASK_BOARD.md 阻塞记录表 |
| 🔨超时回退 | events/*.jsonl | 最近 DISPATCH 事件 |
| 🟢就绪 | TASK_BOARD::上下文传递 段 | 上游产出文件 |

**Conductor 不转述。Conductor 只导航。** Agent 顺着指针自己去读原文，不依赖摘要。

<SECTION-END:10>

## 违规处理

Agent 违反铁律时：
1. **首次违反** → 警告，记录到当前 Workspace 的 `BUG-NNN.md`
2. **同一 Task 内再次违反** → Task 标记失败，重试
3. **同一 Plan 内累计 3 次** → block，等待用户介入

---

## 两种模式

| 模式 | 触发方式 | 生效铁律 | 说明 |
|------|---------|---------|------|
| **严格模式**（默认） | 不加标记 | 全部 Ⅰ-Ⅹ，12 专家团全流程 | 生产级质量 |
| **快速模式** | `@快速模式` | Ⅰ + Ⅱ + Ⅶ + Ⅸ + Ⅹ；跳过审查层 4 人（保留 Tester） | 原型验证 |

---

> *铁律是流水线的轨道。轨道越清晰，Agent 跑得越快。*
