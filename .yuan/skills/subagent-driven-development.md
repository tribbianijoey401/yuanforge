---
name: subagent-driven-development
description: >
  Phase 2-5 执行引擎。Conductor 按调度循环派发 Task 到 12 人专家团。
  触发：Plan 确认后进入 Phase 2、用户说「执行 Plan」「开始实现」。
  管理 TASK_BOARD、派发 Subagent（并行 Dev → 并行 4 审查官 → Tester → Doc Engineer）。
version: 2.0.0
---

# Subagent 驱动开发 Skill

> **YuanForge 的 Phase 2-5 执行引擎。**
> Conductor = Workflow Interpreter：读 Workflow Protocol → 读 TASK_BOARD → 产生 Action → 委托 Adapter。

---

## 触发条件

- Plan 确认（G1 通过）→ 进入 Phase 2
- Conductor 激活：需要按调度循环逐批派发
- 用户说「执行 Plan」「开始实现」「继续」

---

## 执行流程

### Phase 2: 方案设计

```
1. Dispatch(product-analyst)
   输入: 用户 vibe / 一句话需求
   产出: 用户故事 + 验收标准 + 风险标签(R0/R1/R2)
   → 用户确认

2. Dispatch(architect)
   输入: 用户故事 + 验收标准
   动作: 计划复盘 → 设计理解书 → 用户确认 → API 契约 freeze + Plan(含 Dispatch Table)
   并行: Dispatch(ui-designer) — 有界面时
   → [G1: Plan Gate] 用户确认 Plan
```

### Phase 3: 开发实现

```
1. Conductor 初始化 TASK_BOARD（从 Plan 的 Dispatch Table）
2. 找出所有 🟢就绪 Task → 并行派发
   - Dispatch(frontend-dev) × N  (并行)
   - Dispatch(backend-dev) × N   (并行)
   硬前提: API 契约已 freeze

3. 每个 Task Complete → Dependency Check → Promote 下游
4. 超时回退: 🔨→🟢 (attempts++)
5. attempts ≥ 3 → ❌阻塞

异常:
  - ≥2 次修复失败 → 注入诊断协议包（Debug 模式）
  - 需变更契约 → 回退 Dispatch(architect)
```

### Phase 4: 质量审查

```
所有 Dev Task ✅完成 → 同时派发 4 审查官

  Dispatch(spec-reviewer)    [🔴 Blocker]
  Dispatch(security-auditor)  [🔴 Blocker]
  Dispatch(quality-auditor)   [🟢 Advisory↗]
  Dispatch(ux-reviewer)       [🟢 Advisory↗]

并发规则:
  - 任意 Blocker → 通知其他审查官暂停 → 解决后断点恢复
  - 审查报告各自独立呈现

Task 状态:
  - ✅完成 → ✅审查通过 (PASS)
  - ✅完成 → 🔄返工 (FAIL) → 回 Dev 修复
  - 🔄返工 ≥ 3 次 → ❌阻塞
```

### Phase 5: 测试验证

```
前提: 所有 🔴 Blocker 已解决

Dispatch(tester)
  [🟡 Hard Gate] 全量测试必须 PASS

修复回路:
  - 仅逻辑错误 → 回 Dev → Tester
  - 涉接口/权限 → 回 Architect + Spec + Security
  - 涉依赖/数据 → 回 Architect + Spec + Quality
```

### Phase 6: 归档

```
Dispatch(doc-engineer)
  - 增量: 合入主干时异步更新
  - 阶段: Milestone 结束全局归档

Conductor 蒸馏:
  - Promote → Archive → 重建 Graph
```

---

## TASK_BOARD 管理

| 操作 | 谁 | 时机 |
|------|-----|------|
| 初始化 | Conductor | Phase 3 开始，从 Dispatch Table 复制 |
| 领取 Task | Agent | 找到自己角色 + 🟢就绪 的行 |
| 更新状态 | Agent | 🔨→✅ 完成时 |
| Promote 下游 | Conductor | 每次 Task Complete 后重算依赖 |
| 巡检 | Conductor | 持续：超时回退、阻塞升级、更新快照 |
| 上下文传递 | Agent | 完成时追加「上下文传递」行 |

---

## Subagent 上下文模板

派发 Dev Agent 时注入：

```markdown
## Task: T{N}

### 目标
{Task summary}

### 验收标准
- {criterion 1}
- {criterion 2}

### 必读
- 角色合约: contracts/{role}.md
- 铁律: .yuan/rules/iron-rules.md
- 上游产出: {file paths}

### 产出
- {expected output files}
```
