# Yuan Vibe Coding Profile

这是 Yuan 默认安装的工程能力层。它解决“LLM 应该怎样工作”，Core 解决“结果能否被证明”。

## 加载顺序

1. 始终读取 `capability resolve` 返回的全部 Required Rules；当前 Profile 为 `rules/00` 至 `rules/07`。
2. 根据 Work 风险与任务类型，从 `agents/` 选择角色。
3. 只加载与当前 Tick 相关的 `skills/*/SKILL.md`，不要一次加载全部内容。
4. 项目自定义能力写入 `.yuan/extensions/custom/`，不得修改本目录中的托管文件。

Catalog 已由 `.yuan/extensions/manifest.json` 暴露。使用固定 Runtime 的 `capability list` 查看触发条件，使用 `capability resolve` 获得本 Tick 必须读取的路径和 Digest。

## 能力边界

- Rules、Agents、Skills 可以约束 Proposal、指导实施、定义 Verifier 配方或产生 Evidence。
- 它们不能增加 Core Primitive、增加 Result、重定义 `COMPLETE`，也不能直接改写 `.yuan-run/`。
- 平台不支持多 Agent 时，同一 LLM 可以按角色顺序执行，但必须保持实现与验证的证据分离。

## 默认工作流

`理解意图 → 建立 Work Contract → 设计 → 实现 → 独立验证 → Reducer 判定 → 交付/纠正`

## Agent 通用契约

每个 Agent 接收：Active Work、相关 Artifact、前序 Attempt/Evidence 和明确范围。输出必须是 Work/Proposal 草案、Artifact 修改、审查发现或 Verifier Evidence 之一，并给出来源指针。Agent 不得自行宣布 Core Result；Reviewer 不得修改被审对象；平台无法提供独立 Agent 时必须声明角色隔离降级。
