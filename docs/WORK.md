# Active Work

## Goal

交付 Yuan Quality v0：以项目优先的运行时 Engineering Context 约束 Writer，并建立可复现的 Bare / Current Yuan / Quality Yuan Benchmark，用实际代码与设计证据衡量 Artifact Quality。

## Scope

- 新增 Engineering Context Compilation Skill、Writer / Quality Auditor 接入、一个真实 Stack Reference 与 Quality Benchmark。
- 保持 Project-native first；不新增 Agent、Primary Workflow、长期 Project Document、Runtime 或 Core State。

## Non-goals

- 不扩展流程层、State Machine、Dashboard、Insight、Action Gateway 或大规模通用 Reference。
- 不将 Engineering Context 持久化为新的 Project Truth Source。

## Acceptance

- [ ] Context 从 Repository、Project Documents、实际版本和按需知识生成具体、受限的 implementation guidance。
- [ ] backend-dev、frontend-dev 消费 Context；Quality Auditor 可报告 Context 与 Diff 的未经解释 deviation。
- [ ] 通用架构与文件组织规则是 Project-native-first heuristic，而非绝对模板。
- [ ] Benchmark 具有 Feature / Bug / Refactor 的可运行 fixture、三臂运行协议和六维 scorecard。
- [ ] 自动测试、Framework validation 与 risk-driven Quality Review 通过；无新 State / Runtime。

## Assumptions and Risks

- 用户提供的 Yuan Quality v0 与 P0–P6 顺序是已确认方向。
- 首个 Stack Reference 以 Repository Evidence 支持的 Python >=3.10 / standard-library `unittest` 为起点。
- 真实同模型三臂效果需要外部模型运行与独立裁判，不能由 fixture 或 Contract Test 代替。

## Plan

| Slice | Outcome | Artifact | Verification |
|---|---|---|---|
| P0 | Runtime Engineering Context packet | `framework/skills/engineering-context-compilation/SKILL.md` | Contract Test |
| P1–P2 | Writer Context consumption / Contract → Diff Review | Writer、Auditor、review Skill Contracts | Contract Test |
| P3–P4 | Benchmark protocol / Python Stack Reference | `framework/benchmarks/quality-v0/`、`references/stacks/` | Contract Test |
| P5 | 每任务可复制的 initial Repository fixture 和 baseline command | `framework/benchmarks/quality-v0/fixtures/` | fixture `unittest` + Contract Test |
| P6 | Full regression、review、distill | docs / tests | commands + review verdict |

---

# Active Workspace

## Current Task

**Next:** 在获得同一模型、固定运行参数与独立评分条件后，按 `framework/benchmarks/quality-v0/README.md` 对每个 fixture 运行 Bare Agent、Current Yuan、Quality Yuan，并写入实际 patch、测试输出与 scorecard。

## Latest Result

**Outcome:** ready

**Summary:** Final Contract → Diff Review 为 READY（本地 Framework / protocol 范围）。Compiler 的事实优先级、Writer 的 Explore → Context → Verification First 顺序、Auditor 的 Contract → Diff 输入、Project-native heuristic、Python >=3.10 / unittest version grounding、三套 initial Repository fixture、三臂证据字段与六维 scorecard 一致。未发现新的 Workflow、Agent、长期 State、Runtime 或误导性的“已提升”声明。

**Adversarial checks:** 检查了固定行数 / 三层模板残留、隐藏的长效 Context、无版本 API 断言、fixture 被用作效果证据、以及 README 自述漂移；均已消除或受明确边界约束。

**Verdict:** READY（protocol-validated）。

**Verification:** `python -m unittest discover -s tests -v` (pass)；三个 fixture baseline (2 / 1 / 2 tests pass)；`python -B scripts/sync_project.py check G:\yuanforge` (pass, 0 warnings)；`git diff --check` (pass)。

**Residual risk:** `model-comparison-pending`。没有相同模型三臂的真实 patch、测试输出与独立评分，不能声称 Artifact Quality 已被 Benchmark 证明提升。

**Next:** 获得同模型运行权限后执行三臂 Benchmark。

## Open Findings

- 真实同模型三臂运行环境与独立裁判尚未获得授权；在获得真实 patch、测试输出和评分前，不得声明质量提升。

## Work Learnings

- Engineering Context 是 Dispatch 时的临时 packet；长期信息仍进入既有 Project Documents。
- Benchmark fixture 只提供相同起始状态和协议验证，不是模型质量结论。
