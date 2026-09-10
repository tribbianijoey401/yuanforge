---
name: vibecoding-workflow
description: Yuan vNext 的 Dynamic Workflow Coordination。Conductor 在处理开发、修复、重构、切换或继续 Project Work 时使用。
version: 4.0.0
---

# Dynamic Workflow Coordination Skill

## vNext Reference Routing

本 Skill 不直接加载 Reference。它只负责选择/切换 Work、Workflow 与 Agent；Requirement、Plan、Implementation、Review、Test 和 Memory Skill 各自决定 Reference Routing。

## Inputs

- 用户 Request
- `project://docs/STATUS.md`
- `STATUS.focus` 指向的 `project://docs/works/<work-id>.md`；需要切换时只读候选 Work 的最小元数据
- legacy `project://docs/WORK.md`（仅旧 Project compatibility）
- 相关 Project Fact、Decision 与 Memory Section
- `framework://policies/core.md`、`framework://policies/routing.md`、`framework://policies/review.md`
- `framework://policies/state-contract.md` 与 `framework://tools/state_guard.py`
- 当前 Platform Capability

## Procedure

### 1. Preflight and Resume

解析逻辑定位符；确认 Core、Routing、Documents、Conductor 与四个 Primary Workflow 可读。检查 Project Document，缺失时只复制官方空模板，不覆盖已有内容。

先读 STATUS：
- 有 `focus` → 读取对应 `project://docs/works/<focus>.md` 的最小恢复 Context；
- 用户指定另一个 Work → 只读其 frontmatter / Goal / Next Action 后决定是否 Switch；
- 无 `focus` 且 legacy WORK 有旧 checkpoint → compatibility resume，下一次可靠 State Commit 再迁移；
- 不默认读取全部 persisted Work。

### 2. Classify Work Intent

判断 Request 属于：

1. 当前 focused Work 的必要补全；
2. 继续/切换到一个已存在 Work；
3. 一个新的独立 Work；
4. 尚未形成 Work Contract 的 Future / Deferred Item。

只有第 3 类在 Goal / Scope / Acceptance 足够明确时创建新的 `ready` Work；第 4 类进入 BACKLOG。Multi-Work 不是把每个想法都实例化。

### 3. Clarify

根据复杂度执行 Mentor Loop。只提会改变 Scope、Acceptance、Business Rule、关键 Experience、不可逆影响或主要 Risk 的问题。

### 4. Route

按 `framework://policies/routing.md` 选择唯一 Primary Workflow，并选择最小充分 Agent 集合和唯一 Implementation Writer。Routing 只决定“当前需要谁”，不承载方法内容。

### 5. Activate / Switch and Commit

正式 Dispatch 前：

- 若没有其它 `active` Work，正常激活；若已有 active Work，先检查 Platform 是否已经提供每条 lane 的真实 independent execution identity、唯一 `execution.mode: isolated` workspace 与唯一 `agent.instance`。条件全部成立时可直接激活目标 Work，并保留其它 active Work；否则必须 Serialize：完成、Pause 或 Block 现有 Work 后再激活；
- focused Work 写入 `state: active`、Workflow、Stage、当前 Agent、Current Task 与 Verification；
- STATUS `focus` 指向该 Work，并同步 `work_state: active`、Workflow、Stage、当前 Agent等 recovery projection；
- 两者在**同一逻辑步骤**提交。

随后运行：

`python -B <resolved-state-guard-path> check <project-root>`

只有输出 `STATE_VALID` 才表示**校验通过**并允许执行；失败时由 Conductor 修正同一次 Commit，校验通过前**不得继续 Dispatch**。

创建非 focused `ready` Work 时只写该 Work 文件，不抢占 focus。

### 6. Load Capability

```text
Selected Agent
→ Agent Contract 的 Skill Assignment
→ 当前动作需要的 Skill
→ Skill Reference Routing 命中的 Reference Section
```

不要因 Agent 拥有多个 Skill 就全部加载。

### 7. Execute and Verify

- 实现前定义 Test 或 Manual Verification。
- Bug 先 Reproduce；Refactor 使用 risk-scoped Baseline；New Behavior 先定义 Acceptance。
- 一次只由一个 Writer 修改目标 Artifact。
- Reviewer 只在 Risk Signal 命中时加载。
- 每次 Dispatch 前由 Conductor 提交 focused Work 的 Agent、Stage、Current Task；Specialist 返回 Focused Result 后，先提交 Latest Result、Verification、Open Findings 和下一状态，再允许下一 Dispatch。
- 当前 execution chain 的 transient `review_context` 不得跨 Work。

### 8. Pause / Block / Switch

Pause：保存 Current Task、Latest Result、Verification、Open Findings、唯一 Next Action；Work 与 STATUS projection 都设为 `paused`，当前 Agent state `paused`。暂停时保留全文，不归档。

Block：Work 与 STATUS projection 设为 `blocked`，记录 Blocker，Agent state `blocked`。Blocked Work 不阻止用户选择其它 persisted Work。

Switch：单 active Work 按 State Contract 先收敛再更新 focus；多个 State Guard 验证的 isolated active Work 可切换 focus，且不构成 completion。Framework 不调度或创建这些 execution lane。

### 9. Close or Continue

满足 Completion Checklist 后先 Distill 当前 Work：
- 长期 Fact / Decision / Pitfall 归位；
- 有历史价值才写 `project://docs/works/archive/` 摘要；
- 移除完成的 `project://docs/works/<id>.md`，其它 Work 原样保留；
- 移除完成 Work 后先扫描 remaining active Work：用户明确指定继续目标时使用该目标；否则选择 Work id 的稳定字典序首个，并完整同步其 STATUS projection。只有没有任何 active Work 时，才将 STATUS 清为 `focus: null` / `work_state: idle`，即 no active work。

Legacy `project://docs/WORK.md` 不再作为新模型的 canonical Work State。

## Output

- focused Work id / Work action（create / resume / switch / continue）
- Primary Workflow 与 Routing 理由
- Active Agent / Writer
- Focused Plan 或 Next Action
- Verification 与 Evidence
- Risk、Unknown 和真正需要用户确认的问题
