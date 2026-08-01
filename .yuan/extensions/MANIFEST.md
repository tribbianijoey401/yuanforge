# YuanCore Extension Manifest

> **定位**：扩展注册表，描述所有可选扩展及其依赖关系。
> **校验器**：读取本文件，动态加载对应的 workflows / policies / skills 规范。
> **Core 完整性**：禁用任一扩展不影响 Core Schema Validation 和 Reducer 判定。

---

## 扩展总览

| 类别 | 名称 | 文件 | 依赖 Core | 禁用影响 |
|------|------|------|-----------|---------|
| **Workflows** | tdd-loop | `workflows/tdd-loop.md` | NONE | TDD 纪律不再强制执行 |
| **Workflows** | phase-gates | `workflows/phase-gates.md` | NONE | 固定 Gate 不再触发，Core Tick 仍继续 |
| **Workflows** | atomic-commit | `workflows/atomic-commit.md` | NONE | 每 Task 一个 Commit 不再强制 |
| **Workflows** | role-isolation | `workflows/role-isolation.md` | NONE | 多角色并行不再自动隔离 |
| **Workflows** | promotion | `workflows/promotion.md` | NONE | Knowledge 蒸馏不再自动执行 |
| **Policies** | three-level-review | `policies/three-level-review.md` | INVARIANTS | 🔴 审查档位降低为 🟢 Advisory |
| **Policies** | per-task-commit | `policies/per-task-commit.md` | INVARIANTS | 提交粒度放宽为每 Feature |
| **Policies** | evidence-binding | `policies/evidence-binding.md` | INVARIANTS | 专业结论不再强制绑定 Evidence |
| **Skills** | test-driven-development | `skills/test-driven-development.md` | NONE | TDD 流程降级为建议 |
| **Skills** | subagent-driven-development | `skills/subagent-driven-development.md` | NONE | 子 Agent 派发降级为手动 |
| **Skills** | knowledge-distillation | `skills/knowledge-distillation.md` | NONE | 知识蒸馏不再自动执行 |
| **Skills** | debug-feedback-loop | `skills/debug-feedback-loop.md` | NONE | 诊断协议降级为手动 |
| **Skills** | grilling | `skills/grilling.md` | NONE | 需求追问降级为单次 |
| **Skills** | promotion | `skills/promotion.md` | NONE | Skill 晋升管线降级为手动 |

---

## 依赖关系图

```
Core (INVARIANTS + REDUCER + PROTOCOL)
  │
  ├─ workflows/
  │    tdd-loop ──┐
  │    phase-gates │──→ 可选，无依赖
  │    atomic-commit ─┘
  │    role-isolation
  │    promotion
  │
  ├─ policies/
  │    three-level-review ──→ INVARIANTS（三档审查原则）
  │    per-task-commit ──────→ INVARIANTS（原子提交原则）
  │    evidence-binding ─────→ INVARIANTS（证据绑定原则）
  │
  └─ skills/
       test-driven-development ──→ workflows/tdd-loop
       subagent-driven-development
       knowledge-distillation ──→ workflows/promotion
       debug-feedback-loop
       grilling
       promotion
```

---

## Core Tick 最小集（无扩展时仍可运行）

```
1. 读取 STATE.md → 获取当前状态
2. 扫描 proposals/ 目录 → 找到候选 Proposal
3. Core Schema Validation（必过）
4. Role Extension Validation（必过）
5. 确定性选择 select_proposal()
6. 执行 Attempt
7. 收集 Evidence
8. 运行 Reducer → 输出 COMPLETE / BLOCKED / CONTINUE / ...
9. 更新 STATE.md（CAS）
```

> **核心原则**：以上 9 步是 Core Tick 的完整定义。所有 workflows / policies / skills 都是可选的增强层。

---

## 版本

| 字段 | 值 |
|------|-----|
| manifest_version | yuan.extension.manifest/v1 |
| created_at | 2026-08-01 |
| core_schema_version | yuan.proposal/v1 |
| required_core_files | [PROTOCOL.md, INVARIANTS.md, REDUCER.md, schemas/*.md] |
