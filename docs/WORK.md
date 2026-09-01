# Active Work

## Goal

完成 Quality v0.1 的六项闭环修复：Product Truth 优先、Writer-to-Reviewer exact Context handoff、target-version grounding、固定 Benchmark arm identity、shared-task treatment isolation，以及 risk-driven review 语义。

## Scope

- 修复 Engineering Context、Writer / Conductor / Quality Auditor、Review Skill、Python Stack Reference、Benchmark protocol / tasks 与 Contract Tests。
- 保持 Project-native first；不新增 Agent、Primary Workflow、长期 Project Document、Runtime 或 Core State。

## Non-goals

- 不扩展流程层、State Machine、Dashboard、Insight、Action Gateway 或大规模通用 Reference。
- 不将 Engineering Context 持久化为新的 Project Truth Source。

## Acceptance

- [ ] Current confirmed Product Contract / Acceptance / explicit Task constraints 高于 Repository current behavior；被明确改变的旧行为不会成为 invariant。
- [ ] Writer 返回实际使用的 Context，Conductor 仅在当前 review chain 原样转发，Quality Auditor 不得用重新编译的 Context 替代。
- [ ] Python version-specific semantics 只由 target Repository / runtime 的真实版本 Evidence 启用；未知版本进入 unknowns。
- [ ] Benchmark arm identity 固定：Current Yuan 为 `5a42bbfafdddc7e0c81c8f74d4a88bd10f0fa543`，Quality arm 为本次创建的 immutable tag；shared tasks 不泄漏工程答案。
- [ ] Reviewer 集合遵从 `review.md` 的 Risk-driven policy；Quality Audit 仅覆盖 Task-relevant dimensions。
- [ ] 全部 Contract / fixture / Framework verification 通过，且维持 `model-comparison-pending`、无新 Core State / Runtime。

## Assumptions and Risks

- 用户提供的 v0.1 修复规格和 arm identity 是已确认方向。
- 实际同模型三臂效果仍需要外部模型运行与独立裁判；本次只使 protocol 正确、可复现且隔离。

## Plan

| Slice | Outcome | Artifact | Verification |
|---|---|---|---|
| v0.1-A | Product truth / current behavior distinction | Context Compiler | Contract Test |
| v0.1-B | Exact transient review_context handoff | Writer、Conductor、Auditor Contracts | Contract Test |
| v0.1-C | Target-version grounding / review routing | Stack Reference、review Skill、Auditor | Contract Test |
| v0.1-D | Immutable benchmark arms / treatment isolation | Benchmark README、tasks | Contract Test |
| v0.1-E | Regression, fixtures, Framework check and final review | tests / docs | commands + review verdict |

---

# Active Workspace

## Current Task

**Agent:** conductor (persona-degraded)

**Task:** 提交并 push exact Context handoff review-safe correction；不移动或覆盖 `quality-v0.1`，然后恢复真实三臂模型比较为唯一 pending Next Action。

**Done conditions:**

- Commit 使用 `fix: make quality context handoff review-safe` 并推送 `origin/main`。
- `quality-v0.1` 的 tag object 与 peeled commit 保持不变。
- Work 仍 active，唯一 Open Finding 是真实三臂模型比较 pending。

**Declared Context Refs:** 用户 v0.1 规格；当前 `WORK.md`；`framework/policies/review.md`；相关 Agent / Skill / Benchmark assets；`tests/test_contracts.py`。

## Latest Result

**Outcome:** completed

**Summary:** Quality Auditor verdict: READY. Writer now always returns the exact Context it used; Conductor receives before Risk-driven selection and discards in both no-review and completed-review paths; selected Quality Auditor missing Context is a `NEEDS_WORK` protocol defect. Diff is limited to contracts, tests, package marker and required Work/Status checkpoints; tag remains unchanged.

**Next:** Commit and push the post-tag protocol correction, then obtain an execution environment and independent judge for the real three-arm model comparison.

## Open Findings

- 真实同模型三臂运行环境与独立裁判尚未获得授权；在获得真实 patch、测试输出和评分前，不得声明质量提升。

## Work Learnings

- Engineering Context 是 Dispatch 时的临时 packet；长期信息仍进入既有 Project Documents。
- Benchmark fixture 只提供相同起始状态和协议验证，不是模型质量结论。
- v0.1 的 `review_context` 只能是 transient Writer → Conductor → Reviewer handoff，不能成为 Work / Status / Memory 字段。
