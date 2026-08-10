---
name: test-driven-development
description: Dev 实施 Bug Fix、Behavior Change 或 Refactor 时使用 Verification First；不机械要求所有修改制造 Red Test。
version: 4.0.0
---

# Verification First Skill

## vNext Reference Routing

- Bug / Behavior Change：读取 `framework://references/01-standards/test-discipline.md` 的 Impact Graph、Regression 与 Independent Test Section。
- Test 本身被修改或存在 Gaming Risk：读取 `framework://references/01-standards/test-integrity-anti-gaming.md` 的作弊目录与验证手段 Section。
- Generated Code 可能产生 Silent Failure：读取 `framework://references/01-standards/generated-code-failure-modes.md` 的对应 Failure Mode Section。
- 需要 Independent Verification：读取 `framework://references/01-standards/verifier-critic-pattern.md` 的 Input Boundary 与 Verdict Section。

## Choose Verification Mode

| Change | Before Implementation | After Implementation |
|---|---|---|
| Bug Fix | Failing Test 或可重复 Manual Reproduction | Focused Test + Regression |
| New Behavior | Acceptance / Behavior Test | Acceptance + Regression |
| Refactor | 当前 Test Baseline 必须 Passing | 原 Test 继续 Passing |
| Doc / Static Config | 明确 Lint、Parser、Diff 或 Manual Check | 执行对应 Check |
| 无法自动化的 UI / External Flow | 写明 Manual Acceptance Step | 执行并记录 Result 与限制 |

## Red / Green / Refactor

当 Bug 或 New Behavior 适合自动化时使用：

1. `Red`：测试因预期原因失败，而不是环境坏或 Test 写错。
2. `Green`：用最小实现满足 Behavior，不硬编码 Test Input。
3. `Refactor`：保持 Test 通过，改善结构，不改变 Acceptance。

纯文案、机械移动或无法自动化的 Work 不为了仪式制造无意义 Test。

## Integrity

- 禁止删除、弱化 Assertion，或用 `skip` / `xfail` 掩盖失败。
- 修改 Test 时说明为什么原 Test 不再代表 Acceptance，并优先使用 Independent Review。
- 实现与 Test 的大范围混合 Diff 需要 Integrity Review。
- 只报告实际运行的命令、结果和未覆盖范围；没有 Test 条件不等于 Test Passed。

## Record

Verification Plan、Command、Result 和 Residual Risk 作为 `work_updates` 返回 Conductor，由 Conductor 提交到 `project://docs/WORK.md`。可复用 Regression 或 Pitfall 在验证 Root Cause 后建议进入 `project://docs/MEMORY.md`。
