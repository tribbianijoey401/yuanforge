# Yuan Quality v0 Benchmark

## Purpose

Benchmark 要回答的是：在**同一个模型、同一个任务、同一初始 Repository**下，Quality Yuan 是否比 Bare Agent 与 Current Yuan 产出更高质量的 patch。它不以“多了几个 Skill”或“测试是否全绿”替代 Artifact Quality。

## Immutable arms

| Arm | Fixed identity | Allowed context | Required evidence |
|---|---|---|---|
| Bare Agent | recorded run configuration | shared task、初始 Repository 和正常工具 | prompt、实际 patch、测试输出、diff review |
| Current Yuan | commit `5a42bbfafdddc7e0c81c8f74d4a88bd10f0fa543` | 该 commit 可用的 Yuan dispatch assets | prompt / dispatch、实际 patch、测试输出、diff review |
| Quality Yuan | immutable tag `quality-v0.1.1` | shared task + Engineering Context Compilation + Contract → Diff Review | compiled context、prompt / dispatch、实际 patch、测试输出、diff review |

`quality-v0.1.1` 必须指向包含 v0.1.1 protocol correction 的 release commit，创建后推送且永不覆盖；任何 arm 都不得使用可变的 `main`。每一轮从相同 fixture reset 开始，固定模型、模型版本、temperature、工具权限、token budget 与最大迭代次数。

Shared task 只描述观察到的目标与验收，不得包含 guidance、`required_reuse`、`forbidden`、stack strategy 或隐藏答案。只有 Quality Yuan 从任务与目标 Repository Evidence 编译自己的 Engineering Context；Bare Agent 与 Current Yuan 只能获得各自 arm 允许的 context。

## Tasks and Run Record

执行 `tasks/feature.md`、`tasks/bug.md`、`tasks/refactor.md`。每个任务从相应 fixture 复制出干净工作目录，并在该目录运行 `python -m unittest discover -s tests -v` 确认 baseline。对每个 arm 保存原始 prompt、模型与运行参数、完整 Diff、实际 patch、测试输出、Context（仅 Quality Yuan）、Review verdict 及六维 scorecard。由未参与实现的裁判按 `scorecard.md` 评分；分数必须附定位 Evidence。

`fixtures/` 提供每个 arm 相同的初始 Repository 与可执行 baseline；它通过**不是**真实模型效果。当前 fixtures 仍是 protocol smoke benchmark：它们尚不能衡量复杂多文件边界、生命周期、事务、状态或集成下的 artifact quality。后续真实质量比较需要这些类别的独立任务。

没有三组真实输出时，结果必须标记为 `protocol-validated / model-comparison-pending`，不得伪称 Quality Yuan 已提升代码质量。

## Decision Rule

分别比较每个任务和三任务汇总的六维得分、Blocker 数量与测试结果。只有 Quality Yuan 在不存在更高 Blocker 或 Scope Creep 的条件下稳定领先 Current Yuan，且 Current Yuan 领先或不差于 Bare Agent，才能报告预期的 `Bare Agent < Current Yuan < Quality Yuan`。若不成立，按 Context retrieval、project pattern extraction、stack grounding、guidance specificity、Writer compliance、Reviewer detection 逐项诊断。
