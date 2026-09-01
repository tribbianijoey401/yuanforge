---
name: engineering-context-compilation
description: 在 Writer 编码前，从项目真实证据编译任务相关、可执行且有边界的 Engineering Context；不创建长期状态或新的 Runtime。
version: 1.0.0
---

# Engineering Context Compilation

## vNext Reference Routing

- 需要控制 Context 长度或检索顺序：读取 `framework://references/01-standards/context-engineering.md` 的 JIT 与 Compaction Section。
- 任务涉及代码组织或抽象边界：读取 `framework://references/01-standards/code-organization.md` 的 Project-native First 与相关 heuristic Section。
- Repository 的已验证语言 / Framework Signal 命中 Stack Reference 时，只读取对应的 `framework://references/stacks/` 文件和相关 Section。
- 未命中技术、风险或代码路径 Signal 时，不加载该类 Reference；禁止全量 Reference 注入。

## Mission

在 Writer 修改代码前，把当前任务的高级工程判断编译成一个**短小的运行时 Dispatch Context**。它回答的不是“注意性能”或“遵循分层”，而是“本任务应复用哪一个现有模式、在哪个边界完成事务或错误映射、为什么不能新建某个抽象，以及如何验证”。

Engineering Context 不创建新的 Project Truth Source，不写入 `project://docs/`、STATUS、State Guard 或 Runtime。它是当前 Dispatch 的输入；完成后只把有长期价值且经验证的事实按既有规则 Distill。

## Evidence Priority

冲突时严格按下列优先级裁决，并在 packet 中保留 Evidence locator：

1. 当前 Repository 真实代码与配置
2. Project ARCHITECTURE / DECISIONS
3. Project MEMORY
4. 当前实际依赖及版本
5. Stack-specific Engineering Knowledge
6. Yuan Universal Engineering Knowledge

Project-native facts 必须优先。通用 Reference 只能帮助解释或补齐未知，不能把一个使用 adapter → application → domain 的项目改造成 controller → service → repository，也不能仅因行数跨过阈值而要求拆分。

## Compilation Procedure

1. **Bound task.** 从 Work 的 Goal、Acceptance、Scope、Non-goals 确定要改变和必须保持的 Behavior。
2. **Explore project evidence.** 读取目标模块、相邻实现、相邻测试、相关配置和 dependency / lock file；提取 module、existing_patterns、boundaries、error_model、state_model、transaction_model 与 test seam。不要只读目录树。
3. **Ground the stack.** 从真实 manifest、lock file、类型定义或 installed metadata 提取 language、framework、relevant_versions 与本任务真正会调用的语义。无法证实的版本不得以模型记忆补齐。
4. **Select real risks.** 仅对任务涉及的 transaction、concurrency、async、cache、lifecycle、error_handling、performance、security、compatibility、migration、state_transition 或 external_io 做调查；未涉及的风险不进入 packet。
5. **Retrieve narrowly.** 以已验证 Project Fact 为问题选择必要的 Stack-specific Engineering Knowledge 或 Yuan Universal Engineering Knowledge；每条规则必须能指出它为何适用或为何被上层事实覆盖。
6. **Compile guidance.** 把 Evidence 转成可执行的 required_reuse、forbidden 和 implementation_guidance。每条 guidance 必须说明具体对象 / 边界 / 策略，不能只写“注意并发”“注意错误处理”。
7. **Expose unknowns.** 关键判断没有证据时写入 unknowns；继续调查、请求 Architect 或作为 Residual Risk。不得猜测。

## Writer Dispatch Packet

```yaml
task:
  goal: <observable change>
  acceptance: [<verifiable criterion>]
existing_design:
  module: <target module>
  existing_patterns: [<evidence-backed pattern>]
  boundaries: [<API / layer / ownership boundary>]
  error_model: <existing error mapping or none observed>
  state_model: <existing state lifecycle or none observed>
  transaction_model: <existing transaction / atomicity boundary or none observed>
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
required_reuse: [<existing abstraction / helper / error type to use>]
forbidden: [<unapproved abstraction, boundary drift, or unsupported API>]
implementation_guidance: [<task-specific decision with evidence>]
unknowns: [<unverified high-impact judgement and next action>]
verification: [<test, static check, or repeatable manual observation>]
```

## Quality Bar

- **Specific:** “reuse `OrderItem.batchLoadProducts(ids)`” is useful; “avoid N+1” alone is not.
- **Bounded:** include only facts that affect this Task. Use locators and compact explanations instead of codebase dumps.
- **Traceable:** Project Fact and version claims include their source; Reference guidance identifies the Signal that selected it.
- **Project-native:** when local evidence and a generic pattern differ, preserve local architecture unless the Task explicitly changes it.
- **Reviewable:** Writer returns the packet or a compact reference to it with the Diff; Quality Auditor compares its required_reuse, forbidden and implementation_guidance against evidence.

## Stop Condition

Stop when the Writer can name what must be preserved, reused and avoided; the task-relevant stack semantics and risks are grounded; Verification is defined; and any remaining high-impact decision is explicit in unknowns. More general advice is Context noise, not quality.
