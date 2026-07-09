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

## 二、完整流程

```
User Story (vibe / 一句话需求)
  │
  ▼
Phase 1: 需求分析（Product Analyst）
  │ 产出: 用户故事 + 验收标准 + 风险标签(P0/P1/P2)
  │
  ▼
Phase 2: 方案设计（Architect）
  │ 动作: 计划复盘 → 设计理解书 → 用户确认 → API 契约冻结 → Plan
  │ [G1: Plan Gate]
  │
  ▼
Phase 3: 开发实现（Frontend Dev + Backend Dev 并行）
  │ 硬前提: API 契约已 freeze
  │
  ▼
Phase 4: 质量审查（4 Reviewer 并行）
  ├─ Spec Reviewer     [🔴 Blocker]
  ├─ Security Auditor  [🔴 Blocker]
  ├─ Quality Auditor   [🟢 Advisory↗]
  └─ UX Reviewer       [🟢 Advisory↗]
  │
  ▼
Phase 5: 测试验证（Tester）
  │ [🟡 Hard Gate]
  │
  ▼
Phase 6: 知识蒸馏（Conductor）
  │ Workspace Close → Promote → Archive
  │ [G4: Distillation Gate]
  │
  ▼
Done
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

## 四、Conductor 的工作流解释循环

```
Conductor 的每次循环:

  1. 读 Workspace 状态
     - 当前 Phase
     - Task 状态（TASK_BOARD.md）
     - 状态快照（Git HEAD / 脏文件 / 活跃 Agent）

  2. 读 Workflow Protocol（本文）
     - 当前 Phase 的下一步是什么？

  3. 读 State Protocol
     - 哪些 Task 满足转换条件？

  4. 产生 Action
     - Dispatch / Review / Promote / Archive / Recover

  5. 调用 Platform Adapter
     - adapter.dispatch(task, context)
     - adapter.review(task, criteria)
     - ...

  6. 更新 Docs
     - TASK_BOARD.md
     - PROGRESS.md
     - SESSION_LOG.md

  7. 写 Events
     - 状态变更事件
```

---

## 五、巡检循环

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

## 六、跨会话继承

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

## 七、两种执行模式

| 模式 | 触发 | 差异 |
|------|------|------|
| **严格模式**（默认） | 不加标记 | 全流程，所有 Gate 全开 |
| **快速模式** | `@快速模式` | 跳过审查层（Phase 4），保留 Tester（Phase 5） |

---

## 八、与其他协议的关系

| 协议 | 本协议如何使用 |
|------|--------------|
| Object Protocol | Workflow 中每个 Phase 产生/操作的对象 |
| State Protocol | Workflow 通过 Action 触发状态转换 |
| Action Protocol | Workflow 产生 Action → Adapter 执行 |
| Adapter Protocol | Workflow 不直接执行——通过 Adapter |
