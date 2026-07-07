---
name: subagent-driven-development
description: >
  Phase 2 执行 Plan 时加载。触发：Plan 确认后进入 Phase 2、Conductor 需要
  逐 Task 派发 Coder→Reviewer 子流程、用户说「执行 Plan」「开始实现」。
  管理 TODO 列表、派发 Subagent（Coder→Reviewer）、追踪 G2 Gate 状态。
  读写：PROGRESS（每 Task 更新）、features/当前（上下文传递给 Subagent）、
  Plan（读取 Task 描述）。
version: 1.0.0
---

# Subagent 驱动开发 Skill

> **YuanForge 的 Phase 2 执行引擎。**
> 读取 Plan → 逐 Task 派发 Subagent → 追踪 Gate 状态。

---

## 触发条件

- Phase 2 启动：Plan 确认后
- Conductor 激活：需要逐 Task 执行
- 用户说「执行 Plan」「开始实现」「继续下一个 Task」

---

## 流程

### Step 1: 加载 Plan

1. 读取 `docs/PROGRESS.md` — 当前 Plan 路径
2. 读取 Plan 文件 — 所有 Task 列表
3. 读取 `docs/features/NNN-xxx.md` — 当前功能文档
4. 创建 TODO 列表追踪全部 Task

### Step 2: 逐 Task 执行

对每个 Task：

```
Task N: {描述}
  │
  ├── 派 Coder Subagent
  │   ├── 上下文：Plan Task 描述 + features/NNN-xxx.md + pitfalls
  │   ├── 加载：coder persona + test-driven-development skill
  │   └── 等待 Coder 完成 → Commit
  │
  ├── Gate G2-TASK: Spec Review
  │   ├── 派 Reviewer Subagent
  │   ├── 加载：reviewer persona + requesting-code-review skill
  │   ├── PASS → 进入 Quality Review
  │   └── FAIL → 退回 Coder（附差距列表）→ 最多 3 轮
  │
  ├── Gate G2-TASK: Quality Review
  │   ├── APPROVED → 标记 Task 完成 `[G2 ✓]`
  │   └── REJECT → 退回 Coder → 最多 3 轮
  │
  └── 更新 PROGRESS → 下一个 Task
```

### Step 3: Stage Gate 检查

当前 Stage 所有 Task 完成 → 执行 Stage Gate（G1/G3/G4）。

### Step 4: Phase 完成

Phase 2 全部 Stage 完成 → 更新 PROGRESS → 进入 Phase 3。

---

## 📚 文档读写规则

| 阶段 | 读 | 写 |
|------|-----|-----|
| 加载 Plan | Plan 文件, features/当前, PROGRESS, pitfalls | - |
| 每次 Task 完成 | - | PROGRESS（当前 Task → ✓） |
| 每次 Stage 完成 | - | PROGRESS（Gate 标注） |
| 传递上下文给 Subagent | features/当前, pitfalls, CONVENTIONS | - |

---

## Subagent 上下文模板

派 Coder 时注入：

```markdown
## Task 上下文

### Plan 要求
{Task 完整描述}

### 项目文档
- features/：{当前功能文档路径} — 了解设计意图
- pitfalls：docs/pitfalls.md — 避免已知坑
- CONVENTIONS：docs/CONVENTIONS.md — 代码规范

### 要求
- TDD: Red → Green → Refactor
- 完成后更新 features/ 的「修改文件」表
- 遇问题创建 bugs/ 文档
- 原子提交
```

## 快速模式

`@快速模式` 下：
- 跳过 Spec Review（只做 Quality）
- 允许多 Task 合并提交
- G3/G4 可选
