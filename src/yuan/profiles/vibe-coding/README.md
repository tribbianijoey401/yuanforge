# Yuan Vibe Coding Profile

这是 Yuan 默认安装的工程能力层。它解决“LLM 应该怎样工作”，Core 解决“结果能否被证明”。

## 加载顺序

1. 始终读取 `rules/00-boundary.md`、`rules/01-workflow.md` 和 `rules/02-evidence.md`。
2. 根据 Work 风险与任务类型，从 `agents/` 选择角色。
3. 只加载与当前 Tick 相关的 `skills/*/SKILL.md`，不要一次加载全部内容。
4. 项目自定义能力写入 `.yuan/extensions/custom/`，不得修改本目录中的托管文件。

## 能力边界

- Rules、Agents、Skills 可以约束 Proposal、指导实施、定义 Verifier 配方或产生 Evidence。
- 它们不能增加 Core Primitive、增加 Result、重定义 `COMPLETE`，也不能直接改写 `.yuan-run/`。
- 平台不支持多 Agent 时，同一 LLM 可以按角色顺序执行，但必须保持实现与验证的证据分离。

## 默认工作流

`理解意图 → 建立 Work Contract → 设计 → 实现 → 独立验证 → Reducer 判定 → 交付/纠正`
