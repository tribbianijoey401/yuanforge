---
name: engineering-context-compilation
description: 在 Writer 编码前，从项目真实证据编译任务相关、可执行且有边界的 Engineering Context；不创建长期状态或新的 Runtime。
version: 2.0.0
---

# Engineering Context Compilation

## vNext Reference Routing

- 需要控制 Context 长度或检索顺序：读取 `framework://references/01-standards/context-engineering.md` 的 JIT 与 Compaction Section。
- 任务涉及代码组织或抽象边界：读取 `framework://references/01-standards/code-organization.md` 的 Project-native First 与相关 heuristic Section。
- Repository 的已验证语言 / Framework Signal 命中 Stack Reference 时，只读取对应的 `framework://references/stacks/` 文件和相关 Section。
- 未命中技术、风险或代码路径 Signal 时，不加载该类 Reference；禁止全量 Reference 注入。

## Mission

在 Writer 修改代码前，把当前任务的高级工程判断编译成一个**短小的运行时 Dispatch Context**。它回答的不是"注意性能"或"遵循分层"，而是"本任务应复用哪一个现有模式、在哪个边界完成事务或错误映射、为什么不能新建某个抽象，以及如何验证"。

Engineering Context 不创建新的 Project Truth Source，不写入 `project://docs/`、STATUS、State Guard 或 Runtime。它是当前 Dispatch 的输入；完成后只把有长期价值且经验证的事实按既有规则 Distill。

## Evidence Priority

冲突时严格按下列优先级裁决，并在 packet 中保留 Evidence locator：

1. Current confirmed Product Contract / Acceptance / explicit Task constraints
2. Current Repository implementation/tests/config
3. Project ARCHITECTURE / DECISIONS
4. Project MEMORY
5. Actual dependency/runtime/version facts
6. Stack-specific Engineering Knowledge
7. Yuan Universal Engineering Knowledge

Product Truth 定义本次要发生的**desired_changes**；Repository Evidence 只描述 **current_behavior**、既有边界、未受影响的兼容性与可复用模式。不得把被明确改变的旧行为写成 invariant。例如任务要求修复"重复提交会创建两笔订单"时，现有重复创建是 current_behavior，不是必须保持的 invariant。

Project-native facts 必须优先于通用 Reference，但确认的 Product Truth 高于当前实现。通用 Reference 只能帮助解释或补齐未知，不能把一个使用 adapter → application → domain 的项目改造成 controller → service → repository，也不能仅因行数跨过阈值而要求拆分。

Project-native is default, not automatic excellence：现有设计不是自动优秀的。当现有设计存在明显 local design debt 且会实质影响当前 Task 时，可以指出并建议调整，但必须给出 Evidence、Impact 与"为什么保持现状更差"；不能因为 Yuan 偏好另一种风格就改。没有这三样东西，现有设计按原样编译。

## Evidence Kind 与决策强度

改变 Writer 实现路线的高级判断（required_reuse / forbidden / implementation_guidance 中的实质决策）必须能表达 **decision + evidence + reason**，并标注 evidence_kind：

```yaml
required_reuse:
  - decision: reuse OrderRepository.find_by_request_id
    evidence:
      - src/order/repository.py#find_by_request_id
      - src/order/service.py#create_order
    reason: existing durable order lookup already crosses this persistence boundary
    evidence_kind: repository-invariant
```

允许的 evidence_kind（不引入数字 confidence score）：

| kind | 含义 | 可支持的决策强度 |
|------|------|----------------|
| contract | Product Contract / Acceptance / Task 约束的明确条款 | 任意，包括 forbidden 与 required_reuse |
| repository-invariant | Repository 中跨调用点稳定成立、本次 Task 未授权改变的既有机制 | required_reuse、forbidden |
| repeated-project-pattern | 项目内 ≥2 处独立出现的同一模式 | required_reuse；forbidden 需要补充上层 Evidence |
| local-example | 项目内仅 1 处的实例 | 通常只能支持 implementation_guidance；单个 local example 不应轻易变成 forbidden |
| stack-fact | 已验证的框架 / 依赖版本语义 | implementation_guidance、明确的版本兼容 forbidden |
| heuristic | Stack / Universal Knowledge 中的一般经验，无本仓库直接证据 | implementation_guidance；不得直接成为 hard prohibition，除非有更高层 Evidence |

Evidence strength 决定决策强度：`heuristic` 或单个 `local-example` 不支撑 forbidden；把 heuristic 直接写成 hard prohibition 是编译错误。

## Compilation Procedure

1. **Bound task.** 先从确认的 Product Contract、Acceptance、explicit Task constraints 提取 desired_changes；再明确哪些未变行为才是 invariants。不得由旧实现反推 Product Truth。
2. **Explore project evidence.** 读取目标模块、相邻实现、相邻测试、相关配置和 dependency / lock file；提取 current_behavior、module、existing_patterns、boundaries、error_model、state_model、transaction_model 与 test seam。不要只读目录树。
3. **Ground the stack.** 从真实 manifest、lock file、类型定义或 installed metadata 提取 language、framework、relevant_versions 与本任务真正会调用的语义。无法证实的版本不得以模型记忆补齐。
4. **Select real risks.** 仅对任务涉及的 transaction、concurrency、async、cache、lifecycle、error_handling、performance、security、compatibility、migration、state_transition 或 external_io 做调查；未涉及的风险不进入 packet。
5. **Retrieve narrowly.** 以已验证 Project Fact 为问题选择必要的 Stack-specific Engineering Knowledge 或 Yuan Universal Engineering Knowledge；每条规则必须能指出它为何适用或为何被上层事实覆盖。
6. **Compile guidance.** 把 Evidence 转成可执行的 required_reuse、forbidden 和 implementation_guidance。每条 guidance 必须说明具体对象 / 边界 / 策略，不能只写"注意并发""注意错误处理"。会改变 Writer 实现路线的判断按 decision + evidence + reason + evidence_kind 表达。
7. **Compile UI design facts（仅 UI Task，条件性）.** 当 Task 触及界面时，识别 project-native design facts（见下节 existing_design）。只放 task-relevant 且有 Repository Evidence 的字段；不要每次全部填写，缺的不猜。
8. **Expose unknowns.** 关键判断没有证据时写入 unknowns；继续调查、请求 Architect 或作为 Residual Risk。不得猜测。

## Frontend Design Facts（仅 UI Task）

UI Task 的 packet 在 `existing_design` 中条件性编译 project design facts。字段全部可选：只填 task-relevant 且有 Repository Evidence（组件文件、token 文件、样式表、config locator）的内容：

```yaml
existing_design:
  component_primitives: [<evidence-backed reusable component>]
  design_tokens: <token file / locator or none observed>
  spacing_scale: <observed scale or none observed>
  typography_roles: <observed role system or none observed>
  color_roles: <observed color role system or none observed>
  surface_model: <how surfaces/cards/panels are built here, or none observed>
  radius_model: <observed radius system or none observed>
  shadow_model: <observed shadow usage or none observed>
  interaction_patterns: [<observed interaction pattern>]
  responsive_pattern: <observed breakpoint/layout approach or none observed>
  accessibility_pattern: <observed a11y approach or none observed>
```

Frontend Design Facts 同样受"Project-native is default, not automatic excellence"约束：发现会实质影响本 Task 的 local design debt 时，在 packet 的 unknowns / guidance 中指出（带 Evidence、Impact、why preserving is worse），不静默沿用，也不静默改造。

## Writer Dispatch Packet

```yaml
task:
  goal: <observable change>
  acceptance: [<verifiable criterion>]
desired_changes: [<confirmed behavior to change>]
current_behavior: [<repository-observed behavior; never an invariant when explicitly changed>]
existing_design:
  module: <target module>
  existing_patterns: [<evidence-backed pattern>]
  boundaries: [<API / layer / ownership boundary>]
  error_model: <existing error mapping or none observed>
  state_model: <existing state lifecycle or none observed>
  transaction_model: <existing transaction / atomicity boundary or none observed>
  # UI Task only — conditional, evidence-backed, never fully mandatory:
  component_primitives: [<only when task-relevant>]
  design_tokens: <only when task-relevant>
  spacing_scale: <only when task-relevant>
  typography_roles: <only when task-relevant>
  color_roles: <only when task-relevant>
  surface_model: <only when task-relevant>
  radius_model: <only when task-relevant>
  shadow_model: <only when task-relevant>
  interaction_patterns: [<only when task-relevant>]
  responsive_pattern: <only when task-relevant>
  accessibility_pattern: <only when task-relevant>
invariants: [<behavior that must remain true>]
stack_facts:
  language: <evidence-backed language and version>
  framework: <evidence-backed framework and version>
  relevant_versions: [<dependency/version>]
  relevant_semantics: [<task-specific verified semantic>]
risk_constraints:
  transaction: <only when relevant>
  concurrency: <only when relevant>
  lifecycle: <only when relevant>
  error_handling: <only when relevant>
  performance: <only when relevant>
  security: <only when relevant>
  compatibility: <only when relevant>
required_reuse:
  - decision: <what to reuse>
    evidence: [<locator>]
    reason: <why>
    evidence_kind: <contract | repository-invariant | repeated-project-pattern | local-example | stack-fact | heuristic>
forbidden:
  - decision: <what not to do / not to introduce>
    evidence: [<locator>]
    reason: <why>
    evidence_kind: <usually contract or repository-invariant>
implementation_guidance:
  - decision: <task-specific decision>
    evidence: [<locator>]
    reason: <why>
    evidence_kind: <any kind>
unknowns: [<unverified high-impact judgement and next action>]
verification: [<test, static check, or repeatable manual observation>]
```

简单判断保持简单：`evidence` 单条 + `reason` 一句话即可，不要为每个字段写论文。只有真正改变 Writer 实现路线的判断才需要完整的 decision + evidence + reason 结构。

## Quality Bar

- **Specific:** "reuse `OrderItem.batchLoadProducts(ids)`" is useful; "avoid N+1" alone is not.
- **Bounded:** include only facts that affect this Task. Use locators and compact explanations instead of codebase dumps.
- **Traceable:** Project Fact and version claims include their source; Reference guidance identifies the Signal that selected it; evidence_kind matches actual evidence strength.
- **Project-native:** when local evidence and a generic pattern differ, preserve local architecture unless the Task explicitly changes it — while remembering existing design is not automatically excellent (see above).
- **Strength-honest:** forbidden backed only by heuristic or single local-example is a compilation error, not strictness.
- **Reviewable:** Writer returns the exact packet it actually used as `review_context.engineering_context` with the Diff; Quality Auditor compares that packet's required_reuse, forbidden and implementation_guidance against evidence.

## Stop Condition

Stop when the Writer can name what must be preserved, reused and avoided; the task-relevant stack semantics and risks are grounded; Verification is defined; and any remaining high-impact decision is explicit in unknowns. More general advice is Context noise, not quality.
