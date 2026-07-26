# FEATURE: Yuan Core 0.1 升级

> 会话: 20260726-yuan-core-01-upgrade
> 状态: 执行中
> 风险: R0（框架自修改、运行权威切换）
> 负责角色: Conductor / Product Analyst / Architect / Doc Engineer

## 用户意图

从第一性原理重新设计 Yuan：只以 LLM 驱动的轻框架为核心，把 memory（docs）、测试、审查和其他软件工程实践作为 Harness 或可选扩展；随后以该设计清理现有 YuanForge 多轮迭代产生的错误分支、重复真相源和繁重校验，直到框架完成升级。

用户于 2026-07-26 明确回复“确认”，冻结以下方向并授权开始实施：

1. 接受“五原语 + 六结果”的 Yuan Core 0.1。
2. 人类只在越权、高影响副作用或价值判断时介入。
3. 允许破坏性简化现有 YuanForge，但须先迁移唯一有效知识并保留可回退层。
4. 持续实施直到 Yuan 框架完全升级并经证据验证。

## 第一性原理约束

1. LLM 没有可靠的跨会话记忆，恢复状态必须外置。
2. LLM 的陈述不是事实证明，完成必须由独立证据判定。
3. 工具会改变真实世界，副作用必须受授权并可追踪。
4. 无新证据的重复不会增加正确性，循环必须有预算和退出条件。
5. 验证器也可能失效，验证失败、空验证和自引用验证必须失败关闭。
6. Core 的正确性不得依赖特定 Agent 平台、角色数量或后台调度器。

## 用户故事

- 作为 Yuan 使用者，我希望冷启动的 LLM 只读取有界、结构化的运行记忆，就能安全恢复工作。
- 作为 Yuan 使用者，我希望每次“完成”都能追溯到当前产物上的独立证据，而不是 Agent 自述。
- 作为 Yuan 维护者，我希望 Core 只有删除任一项都会破坏正确性的最小原语。
- 作为平台适配者，我希望只实现文件读写、命令执行和一次 LLM 推理即可承载 Core。
- 作为框架维护者，我希望 Yuan 能用旧信任根验证新版本，并在权威切换失败时无损回退。

## Clean-room 验收标准

| AC | 验收条件 | 必需证据 |
|----|----------|----------|
| AC-01 | Core 只定义 Protocol、Work Contract、Run Memory、Attempt、Evidence 五个原语，扩展不得反向成为 Core 前提 | Schema 清单、规范检查 |
| AC-02 | 每次 Tick 只能归约为 CONTINUE、CORRECT、COMPLETE、BLOCKED、WAIT_AUTH、BUDGET_EXIT 六种结果之一 | reducer conformance fixtures |
| AC-03 | COMPLETE 只由类型化 AC、有效 Evidence、安全不变量和无未决副作用共同推出 | 正反例 completion fixtures |
| AC-04 | 验证器崩溃、零断言、不可解析结果、过期证据和错误范围均失败关闭 | bootstrap verifier 负向 fixtures |
| AC-05 | Run Memory 可由不可变 Work、Attempt、Evidence 重建，损坏或丢失时不会把未知状态误判为成功 | replay/recovery fixtures |
| AC-06 | 任何副作用都必须经过 Harness 授权与 journal，崩溃窗口归约为 UNKNOWN 而非假成功 | side-effect crash fixtures |
| AC-07 | Reference Port 仅依赖文件读写、命令执行和 LLM 推理；其他平台能力由 conformance 证明，不得语义降级 | adapter conformance report |
| AC-08 | 旧规范每个条款都有 Core / Extension / Knowledge / Fixture / Obsolete-with-proof 归宿，覆盖率 100% | provenance manifest |
| AC-09 | 新 Run Memory 成为唯一运行权威后，旧 writer 被机械拒绝且回退演练通过 | authority-switch receipt |
| AC-10 | Yuan Core 能执行并验证一次“修改 Yuan 自身”的 Work Contract | dogfood Evidence |
| AC-11 | 原有 dirty 内容及未跟踪原文可从内容寻址证据恢复，迁移不会覆盖用户现场 | M0a snapshot manifest 与哈希复核 |
| AC-12 | 用户看到完整清场报告并再次明确确认后，才允许 tombstone 旧规范 | 授权回执与清场 Evidence |

## 非目标

- 固定 12/13 个角色进入 Core。
- 固定 Phase、Gate 编号、TDD 顺序或审查人数进入 Core。
- 依赖某一平台的 subagent、后台任务、数据库或消息队列。
- 在可信 bootstrap verifier 建立前，让现有 PTG/CAL 脚本证明新 Core 正确。
- 在 provenance 覆盖与用户清场确认前删除旧规范。

## 关联

| 关系 | 文档 |
|------|------|
| 冻结设计 | [DESIGN.md](./DESIGN.md) |
| 实施计划 | [PLAN.md](./PLAN.md) |
| 运行状态 | [TASK_BOARD.md](./TASK_BOARD.md) |
| 会话日志 | [SESSION_LOG.md](./SESSION_LOG.md) |
| M0a 现场证据 | [evidence/m0a/](./evidence/m0a/) |
