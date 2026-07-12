# Workflow Protocol — 工作流协议

> **协议定位**：定义 YuanForge 的软件开发流程——项目从用户需求到交付的完整阶段。
> **本协议只定义「下一步应该做什么」。**
>
> 不定义怎么派发（那是 Adapter Protocol）、不定义怎么审查（那是 Action Protocol）。
>
> **Conductor = Workflow Interpreter** — 读 Workflow → 读 State Machine → 产生 Action → 调用 Adapter。

---

## 一、设计原则

```
Workflow 决定：下一步应该干什么。
Workflow 不决定：谁来做、怎么做。

Conductor 是 Workflow 的解释器，不是 Scheduler。
它不知道这是 Claude 还是 Codex。
它只读 Protocol → 产出 Action → 交给 Adapter。
```

---

## 二、DAG 拓扑

YuanForge 的开发流程不是线性 pipeline——它是一个有向无环图（DAG），包含 5 个 Phase 和 7 个循环。

```
Phase 1: 需求分析（Product Analyst）
  │ 产出: 用户故事 + 验收标准 + 风险标签(P0/P1/P2)
  │ 内含: L3-2 Grilling 循环（一次一问，用户确认 = 退出）
  ▼
Phase 2: 方案设计（Architect）
  │ 动作: 计划复盘 → 设计理解书 → 用户确认 → API 契约冻结 → Plan
  │ [G1: Plan Gate]
  │
  ▼
Phase 3: 开发实现（Frontend Dev + Backend Dev 并行）
  │ 硬前提: API 契约已 freeze
  │ 每个 Task 内含: L2-1 TDD 循环（Red→Green→Refactor）
  │
  ▼
┌─────────────────────────────────────────────────────────┐
│ Phase 3-4: 审查修正 DAG（有回路！）                      │
│                                                         │
│   Task ✅完成                                            │
│     │                                                   │
│     ▼                                                   │
│   4 审查官并行                                         │
│   ┌── Spec Reviewer  [🔴 Blocker]                      │
│   ├── Security Auditor [🔴 Blocker]                    │
│   ├── Quality Auditor [🟢 Advisory↗]                   │
│   └── UX Reviewer     [🟢 Advisory↗]                   │
│     │                                                   │
│     ├─ 全部通过 → Phase 5                              │
│     └─ 有 Blocker ──→ L2-2 审查修正循环 ──→ 返工      │
│                          │                              │
│                          ▼                              │
│                       Dev 修复                          │
│                          │                              │
│                          ▼                              │
│                       重新审查                          │
│                          │                              │
│                          ├─ 通过 → Phase 5              │
│                          └─ 仍失败 → 回到审查修正循环   │
│                              (最多 3 轮 → escalate)      │
└─────────────────────────────────────────────────────────┘
  │
  ▼
Phase 5: 测试验证（Tester）
  │ [🟡 Hard Gate] 全量测试 PASS
  │
  ├─ PASS → Phase 6
  └─ FAIL ──→ L2-3 修复回路 ──→ 诊断 → 路由 → 修复 → 重测
                │                   (最多 3 轮 → escalate)
                │
                └──→ 内嵌 L3-1 Debug 循环
                     (Dev ≥2 次失败触发，最多 5 轮)
  │
  ▼
Phase 6: 知识蒸馏（Conductor）
  │ Workspace Close → Promote → Archive
  │ 内含: L4 Promotion 循环（EXTRACT→VALIDATE→PROPOSE→MERGE）
  │ [G4: Distillation Gate]
  │
  ▼
Done → 回到 L0 项目循环（backlog → 下一个 Feature）
```

---

## 三、Phase 详解

### Phase 1: 需求分析

```
输入: 用户原始需求（vibe）
触发: 用户说「开发 XX」

Action Sequence:
  1. Dispatch(product-analyst)
  2. Wait: 用户确认用户故事 + 验收标准 + 风险标签

产出:
  - 用户故事
  - 验收标准（可验证的 checkpoints）
  - 风险标签（P0=高敏 / P1=标准 / P2=低敏）

规则:
  - Product Analyst 必须主动追问模糊点
  - 验收标准必须可验证（不能用「用户体验好」这种）
```

### Phase 2: 方案设计

```
输入: 用户故事 + 验收标准
触发: Phase 1 用户确认后

Action Sequence:
  1. Dispatch(architect)
     输入: 用户故事 + 验收标准
     动作: 输出「设计理解书」（核心实体 + 数据流 + 关键交互 + 推导链标注）
  2. Wait: Conductor 审视推导链完整性 → 用户确认理解正确
  3. Architect 产出: API 契约(freeze) + 数据模型 + Plan(含 Dispatch Table)
  4. [有界面时] Dispatch(ui-designer) — 与 Architect 并行
     产出: 视觉规范 + 交互原型

Gate G1:
  - 用户确认 Plan ✓
  - API 契约已 freeze
  - Dispatch Table 完整（每个 Task 有 role/depends/output）

产出:
  - Plan（含 Dispatch Table）
  - API 契约（冻结）
  - 数据模型
  - [有界面] 视觉规范 + 原型
```

### Phase 3: 开发实现

```
输入: API 契约 + Plan
触发: Phase 2 Gate G1 通过后

Action Sequence:
  1. Conductor 初始化 TASK_BOARD（从 Dispatch Table）
  2. Dispatch 无依赖 Task — 并行
     - Dispatch(frontend-dev) × N
     - Dispatch(backend-dev) × N
  3. 每个 Task Complete → Dependency Check → Promote 下游

硬前提: API 契约已 freeze，Dev 不得修改契约

异常处理:
  - 需变更契约 → Dispatch(architect) 评估
  - ≥2 次修复失败 → 注入诊断协议包（Debug 模式）
```

### Phase 4: 质量审查

```
输入: ✅完成的 Task + 审查标准
触发: 所有 Dev Task Complete

Action Sequence:
  1. Review(spec-reviewer)    [🔴 Blocker]
  2. Review(security-auditor)  [🔴 Blocker]
  3. Review(quality-auditor)   [🟢 Advisory]
  4. Review(ux-reviewer)       [🟢 Advisory，有界面时]
  → 四个并发，各自独立产出报告

并发规则:
  - 任意 Blocker → 通知其他审查官暂停
  - Blocker 解决 → 通知各审查官从断点恢复

审查报告分离原则:
  - 四个审查官报告各自独立呈现
  - Conductor 不得合并、重排序、跨轴比较

Security Auditor 分级:
  - P0（高敏）→ 全量审计
  - P1（标准）→ 关键路径审计
  - P2（低敏）→ 跳过

Advisory 升级规则:
  - 同模块 🟠 警告 ≥ 3 次 → 强制升级 🔴 Blocker
```

### Phase 5: 测试验证

```
输入: 所有 Blocker 已解决 + 审查通过
触发: Phase 4 完成后

Action Sequence:
  1. Dispatch(tester)
  2. [🟡 Hard Gate] 全量测试必须 PASS

Gate G3:
  - 全量测试 PASS ✓
  - 所有 🔴 Blocker 已解决 ✓
  - Security 已通过 ✓

修复回路（测试失败时）:
  ┌──────────────────────────────────┐
  │ 仅逻辑错误 → Dispatch(dev) → 回到 Phase 5 │
  │ 涉接口/权限 → Dispatch(architect) + Review(spec+security) │
  │ 涉依赖/数据 → Dispatch(architect) + Review(spec+quality)  │
  └──────────────────────────────────┘
```

### Phase 6: 知识蒸馏

```
输入: 所有 Task 终态 + 测试全绿
触发: Phase 5 Gate G3 通过后

Action Sequence:
  1. Promote(workspace_id)
     - FEATURE.md → knowledge/features/FEAT-NNN.md
     - ADR-NNN.md → knowledge/decisions/ADR-NNN.md
     - BUG-NNN.md → 判断 → knowledge/pitfalls/PIT-NNN.md 或留在 archive
     - 未完成任务 → workspace/backlog.md
  2. Archive(workspace_id)
     - Workspace 目录 → archive/
  3. 重建 Graph（python scripts/build-graph.py）

Gate G4:
  - 所有可蒸馏内容已提取 ✓
  - Workspace 已归档 ✓
  - Graph 已重建 ✓
```

---

## 四、循环定义

### L0 · 项目循环

```
scope: L0
trigger: PROGRESS.md 有未完成的 Feature
body: 选 Feature → 创建 Workspace → 执行 L1 Feature 循环 → 归档 → 回到 backlog
gate: 无 max_iterations（backlog 耗尽 = 项目完成）
carry: knowledge/pitfalls/ 跨 Feature 共享
```

### L1 · Feature 流水线循环（Conductor 元循环）

```
scope: L1
trigger: Workspace 创建完成
body:
  loop:
    read TASK_BOARD              # 找 🟢就绪 的任务
    if 无就绪:
      if 有 🔄返工 → 路由到修复回路（L2-3）
      if 有 ❌阻塞 且 可自动解除 → 解除阻塞
      if 全部 ✅已部署 → break（进入 Phase 6）
      else → 等待（用户操作/超时回退）
    select 最优 Task             # DAG 拓扑序中无依赖未满足的最早任务
    dispatch                     # 通过 Adapter Tier 1/2/3
    wait                         # 等 Agent 完成
    read 产出                    # 状态标记 + 路径，不读内容
    update TASK_BOARD            # 状态 + 原因指针 + 审查结果
    write Event Log              # 每次迭代写事件
    goto loop
gate:
  max_iterations: ∞（Feature 完成 = 退出）
  死循环保护: 见 iron-rules.md 铁律 Ⅹ「死循环保护」
carry:
  跨会话恢复时读 TASK_BOARD + Event Log 重建状态
```

### L2-1 · TDD 循环

```
scope: L2（内嵌在 Dev 中）
trigger: Dev 收到 Task（Dispatch）
body: Red（写测试 → FAIL）→ Green（写实现 → PASS）→ Blue（重构 → STILL PASS）
gate: Red→Green→Blue 线性推进，不会反向。Blue 阶段 max 3 次重构失败 → 跳过重构，mark 技术债
carry: 不需要——Dev 是同一 Agent 同一会话
```

### L2-2 · 审查修正循环

```
scope: L2
trigger: Dev 标记 Task ✅完成
body:
  四个审查官并行启动
  → 审查报告写入 TASK_BOARD「审查结果」段  ← 关键：必须落盘！
  → Conductor 读所有报告
  → if 任意 🔴Blocker:
      Conductor 向其他审查官发暂停信号
      写 TASK_BOARD 原因指针 → 审查结果#T{id}-r{round}
      Dispatch 原 Dev → 修复 → 回到审查
  → if 仅 🟡🟢:
      审查通过 → exit
gate:
  max_iterations: 3
  同一审查官连续 2 次报同一类 Blocker → 升级架构问题 → 回 Architect
  on_exceed: escalate_to_user
carry:
  原因指针 → 审查报告文件路径（Dev 按需加载完整审查报告）
```

### L2-3 · 修复回路

```
scope: L2
trigger: Tester 返回 ❌
body:
  Tester 诊断失败类型 → 写入 TASK_BOARD 原因指针
  Conductor 读失败类型，路由：
    → 逻辑缺陷 → Dispatch 原 Dev（回 L2-1 TDD）
    → 接口/权限缺陷 → 通知 Architect + Spec Reviewer + Security Auditor
    → 依赖问题 → 通知 Architect + Spec Reviewer + Quality Auditor
  → 问题修复 → 重新进入 L2-2 审查 → 审查通过 → 重新进入测试
gate: max_iterations: 3; on_exceed: escalate_to_user
carry: Tester 写入「失败类型 + 具体症状」→ Conductor 路由决策落盘
```

### L3-1 · Debug 循环

```
scope: L3（内嵌在 L2-3 中）
trigger: Dev ≥2 次修复失败，猜测代替逻辑
body: 详见 debug-feedback-loop Skill
  Phase 0: 构建反馈循环（10 种方式）
  Phase 1: 隔离 → 二分定位 → 假设记录 → 并行通知 Architect → 修复 → verify
gate: max_iterations: 5; on_exceed: 标记 known issue → 跳过此 Task
carry: 「假设记录 + 诊断结论」→ TASK_BOARD 原因指针
```

### L3-2 · Grilling 循环

```
scope: L3（内嵌在 Product Analyst / Architect 中）
trigger: 需求存在模糊点
body: 详见 grilling Skill。一次一问 → 等反馈 → 探索边界
gate: max_iterations: ∞（用户驱动，"可以了" = 退出）
carry: 不需要——与用户对话，同一 Agent
```

### L4 · Promotion 循环

```
scope: L4
trigger: Phase 6 开始（所有 Task ✅已部署）
body: 详见 promotion Skill。EXTRACT → VALIDATE → PROPOSE → MERGE
gate: 4 阶段线性推进；PROPOSE 失败 → 人工审批
carry: 按蒸馏 Checklist 逐步推进
```

---

## 五、Conductor 调度循环

Conductor 是一个事件循环，不是一次性表格：

```
while true:
    1. READ — 读 TASK_BOARD 全部行，扫描状态列
    2. FIND — 找可执行任务：
       a. 🟢就绪 + 依赖全部满足 → 可派发
       b. 🔄返工 → 进入审查修正循环（L2-2）
       c. ❌阻塞 → 检查是否可自动解除
       d. 全部 ✅已部署 → break（进入 Phase 6）
    3. SELECT — 从可派发任务中选优先级最高的：
       优先级 = DAG 拓扑序（依赖少的先执行）
    4. DISPATCH — 通过 Adapter 派发（Tier 1/2/3）
    5. WAIT — 等 Agent 返回结果
    6. DIGEST — 读产出物状态标记 + 路径，不读内容
    7. UPDATE — 更新 TASK_BOARD 状态 + 原因指针 + 审查结果
    8. LOG — 写 Event Log（DISPATCH / COMPLETE / REVIEW / REWORK / BLOCK）
    9. GOTO 1
```

### 跨会话恢复

新 Conductor 启动时：
1. 读 PROGRESS.md → 找到当前 Workspace
2. 读 TASK_BOARD → 扫描全部状态
3. 读 Event Log（最近 20 条）→ 了解刚才发生了什么
4. 回退 🔨进行中 → 🟢就绪（上一个 Conductor 可能崩溃）
5. 检查 Git working tree → 脏则 stash
6. 进入调度循环 step 1

---

## 六、巡检循环

```
Conductor 持续巡检:
  - 检查所有 🔨进行中 Task 是否超时
    - 超时 → State: 🔨→🟢（attempts++）
    - attempts ≥ 3 → State: 🟢→❌阻塞
  - 检查外因阻塞 → 条件满足 → 自动解除
  - 更新 TASK_BOARD「当前状态快照」
  - 任务终态 → 更新 SESSION_LOG「任务完成情况」
```

---

## 七、跨会话继承

> **详细恢复逻辑见「五、Conductor 调度循环 → 跨会话恢复」。本节仅保留继承的核心规则。**

```
新会话启动:
  1. 崩溃检测
     - PROGRESS → 当前 Workspace 是否存在？
     - SESSION_LOG 是否完整？
     - 异常 → 进入 Recover Action

  2. 继承非终态任务
     - 读旧 TASK_BOARD → 提取非终态
     - 重置: 🔨→🟢 / 🔄→🟢
     - 重算依赖: 已完成任务的下游 → 依赖满足
     - 复制上下文传递行

  3. 重新审视旧 Plan
     - 项目约束是否已变化？
     - 推导链是否仍然成立？
     - 不成立 → Dispatch(architect) 重新设计受影响部分
```

---

## 八、两种执行模式

| 模式 | 触发 | 差异 |
|------|------|------|
| **严格模式**（默认） | 不加标记 | 全流程，所有 Gate 全开 |
| **快速模式** | `@快速模式` | 跳过审查层（Phase 4），保留 Tester（Phase 5） |

---

## 九、与其他协议的关系

| 协议 | 本协议如何使用 |
|------|--------------|
| Object Protocol | Workflow 中每个 Phase 产生/操作的对象 |
| State Protocol | Workflow 通过 Action 触发状态转换 |
| Action Protocol | Workflow 产生 Action → Adapter 执行 |
| Adapter Protocol | Workflow 不直接执行——通过 Adapter |
