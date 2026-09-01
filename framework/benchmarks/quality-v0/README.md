# Yuan Quality v0 Benchmark

## Purpose

Benchmark 要回答的是：在**同一个模型、同一个任务、同一初始 Repository**下，Quality Yuan 是否比 Bare Agent 与 Current Yuan 产出更高质量的 patch。它不以“多了几个 Skill”或“测试是否全绿”替代 Artifact Quality。

## Three Arms

| Arm | Allowed context | Required evidence |
|---|---|---|
| Bare Agent | Task、初始 Repository 和正常工具 | prompt、实际 patch、测试输出、diff review |
| Current Yuan | 当前 Quality v0 之前的 Yuan dispatch assets | prompt / dispatch、实际 patch、测试输出、diff review |
| Quality Yuan | Current Yuan + Engineering Context Compilation + Contract → Diff Review | compiled context、prompt / dispatch、实际 patch、测试输出、diff review |

每一轮都从相同 commit / fixture reset 开始，固定模型、模型版本、temperature、工具权限、token budget 与最大迭代次数。Quality Yuan 的 Context 必须是 Task-specific，不能把答案或隐藏测试直接注入。

## Tasks and Run Record

执行 `tasks/feature.md`、`tasks/bug.md`、`tasks/refactor.md`。每个任务从相应的 `fixtures/feature-config`、`fixtures/bug-cleanup` 或 `fixtures/refactor-parser` 复制出干净工作目录，并在该目录运行 `python -m unittest discover -s tests -v` 确认 baseline。对每个 arm：保存原始 prompt、模型与运行参数、完整 Diff、实际 patch、测试输出、Context（仅 Quality Yuan）、Review verdict 及六维 scorecard。由未参与实现的裁判按 `scorecard.md` 评分；分数必须附定位证据。

`fixtures/` 提供每个 arm 相同的初始 Repository 与可执行 baseline；它通过**不是**真实模型效果。没有三组真实输出时，结果必须标记为 `protocol-validated / model-comparison-pending`，不得伪称 Quality Yuan 已提升代码质量。

## Decision Rule

分别比较每个任务和三任务汇总的六维得分、Blocker 数量与测试结果。只有 Quality Yuan 在不存在更高 Blocker 或 Scope Creep 的条件下稳定领先 Current Yuan，且 Current Yuan 领先或不差于 Bare Agent，才能报告预期的 `Bare Agent < Current Yuan < Quality Yuan`。若不成立，按 Context retrieval、project pattern extraction、stack grounding、guidance specificity、Writer compliance、Reviewer detection 逐项诊断。
