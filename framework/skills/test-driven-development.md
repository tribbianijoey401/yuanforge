---
name: test-driven-development
description: Dev 实施 Bug Fix、Behavior Change 或 Refactor 时使用 Verification First；不机械要求所有修改制造 Red Test，也不把 baseline 等同于无条件全量测试。
version: 4.0.1
---

# Verification First Skill

## vNext Reference Routing

- Bug / Behavior Change：读取 `framework://references/01-standards/test-discipline.md` 的 Impact Graph、Regression、Baseline Scope 与 Independent Test Section。
- Test 本身被修改或存在 Gaming Risk：读取 `framework://references/01-standards/test-integrity-anti-gaming.md` 的作弊目录与验证手段 Section。
- Generated Code 可能产生 Silent Failure：读取 `framework://references/01-standards/generated-code-failure-modes.md` 的对应 Failure Mode Section。
- 需要 Independent Verification：读取 `framework://references/01-standards/verifier-critic-pattern.md` 的 Input Boundary 与 Verdict Section。
- 新建模块/文件，或改动涉及分层归属与文件组织：读取 `framework://references/01-standards/code-organization.md` 的分层依赖与文件组织硬规则 Section。
- 实现可能引入 Silent Failure、Happy-path Bias 或幻觉 API：读取 `framework://references/01-standards/generated-code-failure-modes.md` 的对应 Failure Mode Section。

## Choose Verification Mode

| Change | Before Implementation | After Implementation |
|---|---|---|
| Bug Fix | Failing Test 或可重复 Manual Reproduction；若会触及既有行为，建立对应的 risk-scoped regression baseline | Focused Fix Test + 受影响旧行为 Regression |
| New Behavior | Acceptance / Behavior Test；若复用或改变共享 boundary/state/contract，先建立其受影响旧行为 baseline | Acceptance + 受影响旧行为 Regression |
| Refactor | **受影响既有行为的 Test Baseline 必须 Passing**；范围按 blast radius 选择 | 同一 baseline 继续 Passing + 必要的扩大回归 |
| Doc / Static Config | 明确 Lint、Parser、Diff 或 Manual Check；不为了 baseline 跑无关 Test Suite | 执行对应 Check |
| 无法自动化的 UI / External Flow | 写明 Manual Acceptance Step；对会被改动影响的既有行为建立可重复观察 baseline | 执行并记录 Result 与限制 |

## Baseline Scope — Risk-scoped, not universally full-suite

**Baseline 是“改动前可比较的验证状态”，不是“先把全项目所有测试跑一遍”的同义词。** 它的范围必须由本次改动的 blast radius、风险、项目测试结构和执行成本共同决定：

```text
Task / Change Type
+ Affected Boundary / Shared State / Contract
+ Blast Radius
+ Test Cost / Project Policy
→ Smallest sufficient pre-change baseline
```

- **Refactor**：因为目标是行为不变，必须先证明**受影响的既有行为**是绿的；局部 refactor 可以使用相关模块/调用链的测试集。只有 blast radius 很大、项目 policy 要求、或全量成本合理时才扩大到 full suite。
- **Bug Fix / New Behavior**：优先建立“目标行为的 Red / Acceptance”与“可能被打坏的旧行为 baseline”。不要只测新增代码，也不要为了仪式运行明显无关的全量 suite。
- **Doc / mechanical / static config**：用与改动匹配的 lint / parser / build / diff / manual check；没有代码行为风险时，不制造无意义 test baseline。
- **Full suite**：当成本合理且能显著增加回归证据，或项目已有 CI / release policy 明确要求时运行；它是验证范围的一种选择，不是 baseline 的定义。

因此报告里的：

```text
Baseline: 27 tests passed
```

只表示“本次选择的 pre-change baseline 实际运行了 27 个测试且为绿”，**27 不是 Yuan 的要求，也不是质量阈值**。应同时能回答：为什么这 27 个测试足以覆盖本次改动的主要旧行为风险；若只跑 focused subset，也应记录未覆盖范围与原因。

## Red / Green / Refactor

当 Bug 或 New Behavior 适合自动化时使用：

1. `Red`：测试因预期原因失败，而不是环境坏或 Test 写错。
2. `Green`：用最小实现满足 Behavior，不硬编码 Test Input。
3. `Refactor`：保持所选 regression baseline 通过，改善结构，不改变 Acceptance。

纯文案、机械移动或无法自动化的 Work 不为了仪式制造无意义 Test。

## Integrity

- 禁止删除、弱化 Assertion，或用 `skip` / `xfail` 掩盖失败。
- 修改 Test 时说明为什么原 Test 不再代表 Acceptance，并优先使用 Independent Review。
- 实现与 Test 的大范围混合 Diff 需要 Integrity Review。
- 只报告实际运行的命令、结果和未覆盖范围；没有 Test 条件不等于 Test Passed。
- 不得把“focused baseline 通过”表述成“全项目测试通过”；Verification claim 必须与实际 scope 一致。

## Record

Verification Plan、Baseline Scope、Command、Result、未覆盖范围和 Residual Risk 作为 `work_updates` 返回 Conductor，由 Conductor 提交到 `project://docs/WORK.md`。可复用 Regression 或 Pitfall 在验证 Root Cause 后建议进入 `project://docs/MEMORY.md`。
