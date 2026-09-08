---
name: requesting-code-review
description: >
  Risk-driven 代码审查：Conductor 依据 framework://policies/review.md 选择最小充分 Reviewer 集合，
  并保持 Independent Artifact Critique → Context Compliance 双视角、独立 evidence 与对抗式检查。
version: 3.0.0
---

# 代码审查 Skill

## Authority and selection

`framework://policies/review.md` 是审查是否需要、需要哪些 Reviewer 的唯一权威。Conductor 根据当前 Diff、Acceptance 与风险选择**最小充分 Reviewer 集合**：小型机械改动通常无需独立审查；Bug、Public Interface、Data Model、Security、Concurrency、Migration、Dependency、Architecture、Test Modification 或可信 Cross-module Impact 才选择相称的审查。

以下是可能的 Reviewer，不是每次必选清单：

- Spec Reviewer：Acceptance、Public Contract、scope 与行为回归。
- Security Auditor：输入、权限、敏感数据、注入、依赖风险。
- Quality Auditor：Independent Artifact Critique + Context Compliance、边界、可维护性、性能或可靠性。
- UX Reviewer：只有界面、交互或可访问性风险时参与。

Platform 支持时，Material Review 使用 Independent Context；不支持时明确 Persona Switch 和共享 Context 的限制。Reviewer 不修改被审 Artifact。

## vNext Reference Routing

- Material Review：读取 `framework://references/01-standards/verifier-critic-pattern.md` 的 Actor / Checker、Input Boundary 与 Verdict Section。
- Test 或 Assertion 被修改：读取 `framework://references/01-standards/test-integrity-anti-gaming.md` 的 Integrity Difference 与 Reviewer Section。
- Production Readiness 是 Acceptance 一部分：读取 `framework://references/01-standards/production-readiness-scorecard.md` 的相关 Level 与 Dimension Section。

## Quality v0 双视角 Review

Quality Auditor 的审查不是单一 "Context → Diff first"。正确顺序：

```text
Independent Artifact Critique (Pass A)
↓
Context Compliance (Pass B)
```

**Pass A — Independent Artifact Critique：** 先基于 Task、Acceptance、Actual Diff 与 Relevant Repository Evidence 独立判断方案与实现本身的质量（Problem Fit、Simplicity、不必要的 abstraction、ownership 清晰度、failure / operational 问题、被忽略的 Repository invariant）。此阶段不把 Writer Engineering Context 当作正确答案——Context 本身可能漏事实或推导错误。

**Pass B — Context Compliance：** 然后以 Writer 实际使用且经 Conductor 原样转发的 Engineering Context、Acceptance Criteria、Actual Diff 与 Verification Evidence，验证 invariant、required_reuse、forbidden 与 implementation_guidance 的执行情况，报告**未经解释的 deviation**、未批准 abstraction 或真实 Stack 语义偏离。

Finding type 语义：`artifact-defect`（实现缺陷）、`solution-quality-defect`（功能正确但方案本身质量差）、`context-deviation`（Context 约定未被执行且无解释）、`context-gap`（Context 本身漏掉重要事实；只报告缺口，不得重新编译替代 Context）。

代码风格、复杂度与性能只在 Task-relevant 时审查，不能以固定 controller / service / repository 模板或文件长度阈值覆盖 Project-native facts。

## Review protocol

1. Conductor 依据风险选择 Reviewer，并给出 Acceptance、Diff、Verification Evidence 与所需 Context。
2. 每个被选 Reviewer 独立检查自己负责的维度；不参与的维度不假装已审。
3. Quality Auditor 按 Pass A → Pass B 顺序输出；每个 Material Review 记录至少一次任务相关的对抗式尝试，或说明为什么没有适用场景。
4. 报告包含 verdict（`READY` / `NEEDS_WORK`）、Finding（带 type）、Evidence、Affected Path 与 Residual Risk。
5. `NEEDS_WORK` 交回唯一 Writer 修正；Artifact 改变后重跑受影响验证，并按新的风险重新选择审查。

## Result handling

Conductor 保留各 Reviewer 的证据与 verdict。Blocker 必须修复；Advisory 可采纳、进入 backlog 或有理由豁免。`solution-quality-defect` 与 `context-gap` 由 Conductor 裁定是否需要回 Architect / Context 编译方，不默认塞给 Writer。不得把"启动四个审查官"当作完成质量工作的替代，也不得为小机械改动制造固定四人仪式。
