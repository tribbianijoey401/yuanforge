---
name: content-driven-interface-design
description: 根据可用的 Product Truth、系统行为与 Content Topology，推导可冻结或临时的 Presentation Contract。供 UI Designer 选择界面架构，或 UX Reviewer 审查架构、Detail Strategy、Visual Language 与语义 Liveness；不得创造第二份事实源，也不得套用预设视觉配方。
---

# 内容驱动的 Interface Design

## 单一 Product Truth Source

将 Active Work 引用的 canonical Product Contract / Acceptance / Repository Fact 视为唯一 Product Truth Source。Presentation Contract 只保存真实 source locator 与稳定 fact ID，不得复制或改写产品事实形成竞争性规范。canonical facts 冲突时，先将冲突交回 Conductor；缺少身份时，按下方 provisional path 处理。

不得创建、推断、重命名或铸造 canonical locator 或 fact ID。输入没有稳定 canonical locator 或 fact ID 时，记录 `source: current user request` 与 `canonical ID unavailable`，然后继续临时设计。结果是 provisional Presentation Contract，不能被冻结。在 Yuan 场景中，将 identity gap 返回 Conductor；在独立 Skill 场景中，在结果中披露 identity gap。两种场景都不得把 prompt 改写成第二份 Product Truth Source。只有真实 canonical source 与稳定 canonical locator、fact ID 才允许冻结。

## 决策链

有上游 fact ID 时，每个下游选择都必须引用它。临时路径则引用明确的 source description 与带标签的 derived anchor：

`System Story → Content Model → View Model → Visual Language → Liveness → Verification`

1. 建立完整 System Story：user and context、task and intended outcome、key object old → new change、why the user must perceive the change、consequence if they do not，以及 truth source locator 和 fact ID；临时路径改用明确的 provisional source description 与 identity gap。
2. 建立完整 Content Model：content and entity types、volume、relationships、priority and co-visibility、states and transitions、change frequency and freshness、key actions、device、context continuity requirements。
3. 选择 Primary View Model，并引用支撑它的 content facts。只有独立的 subordinate task 无法由主模型清晰表达时，才增加 Secondary View Model 并说明 rationale。至少记录一个 rejected candidate 及其被冲突事实否决的原因。仅在匹配 topology、detail、continuity 或 anti-convergence 决策时读取 `skill://references/presentation-architecture.md`。
4. 推导其余决策：
   - Visual Language：引用决定 hierarchy、density、emphasis、accessibility 与 project-owned tokens 的上游 fact ID；临时路径引用回明确 source description 的 derived anchor。
   - Liveness：为每个真实操作或 transition 引用上游 fact ID，或使用同一 provisional trace；写明 semantic event、truth source、perceptible change、recovery path 与 reduced-motion equivalent。
   - Verification：引用上游 fact ID，或使用同一 provisional trace；说明 normal、empty、loading、failure、success、recovery 与 continuity 的 observable acceptance step。

## Presentation Contract 状态

生成一份供实现与审查共用的 Contract，只包含 source reference 与 derived decision。只有 canonical source 与稳定 ID 真实存在时才能冻结；否则保持 provisional，同时完成所有可支持的设计决策：

- 真实 canonical source locator 与稳定 fact ID，或明确的 provisional source description 与 identity gap。
- 完整 System Story 与 Content Model，每个字段都链接到 source fact。
- Primary View Model、可选 Secondary View Model、rationale 与 rejected candidate。
- Information priority、Detail Strategy、Context Continuity、Visual Language 与语义 Liveness。
- Observable acceptance 与 recovery behavior。

UI Designer 编写 Contract，并仅在 identity condition 满足时冻结。UX Reviewer 审查同一 Contract，不重新编写。Frontend Dev 只消费该 Contract。

## Traceability Matrix

必须包含以下矩阵；没有有效上游引用的行是不完整的：

内部追踪可以创建 derived decision anchor，但必须标明 derived；它永远不是 canonical，不能替代缺失的 source locator 或 fact ID。

| Decision | Upstream fact reference | Consequence | Verification |
|---|---|---|---|
| System Story field | canonical fact ID，或 provisional source description + identity gap | user-visible meaning | source 与 completeness check |
| Content Model field | System Story、canonical fact ID，或 provisional derived anchor | topology constraint | model completeness check |
| Primary or Secondary View Model | Content Model field ID，或 provisional derived anchor | structure 与 continuity behavior | task-fit check |
| Visual Language | System Story、Content Model 或 View Model ID | hierarchy 与 emphasis | perceptual 与 accessibility check |
| Liveness | state、transition、freshness 或 action ID | feedback 与 recovery | event 与 reduced-motion check |
| Verification | Acceptance ID + derived decision ID | pass/fail observation | acceptance execution |

## vNext Reference Routing

- Topology、task shape 或 rejected candidates → View Models and Selection Contract。
- Focused inspection 或 edit → Detail Strategy。
- Return path、selection、filter、draft、focus 或 scroll preservation → Context Continuity。
- 出现趋同的 visual 或 layout instinct → Anti-convergence。

只有在 View Model 选定后才可进行 industry lookup。它只能提供条件性建议，不得覆盖 canonical product truth、Presentation Architecture、Visual Absolutes 或 Project Design System。
