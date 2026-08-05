# Yuan Vibe Coding Profile

这是 Yuan 默认安装的工程能力层。它解决“LLM 应该怎样工作”，Core 解决“结果能否被证明”。

## 加载顺序

1. 用户自然语言只表达需求或“继续”；Conductor 根据状态自动进入 Intake、恢复或继任流程。
2. 新需求先完成 Intake 与用户确认。
3. 运行 `capability route`；始终读取返回的全部 Required Rules，Agent 与 Skill 只能来自 `routing/assignments`。
4. 每个角色只加载 Assignment 中与当前阶段相关的 `skills/*/SKILL.md`，不要一次加载全部内容。
5. 项目自定义能力写入 `.yuan/extensions/custom/`，不得修改本目录中的托管文件。

Catalog 与 Workflow 已由 `.yuan/extensions/manifest.json` 暴露。使用固定 Runtime 的 `capability list` 查看能力，使用 `capability route --risk ... --signal ...` 获得本 Work 的路径、Digest 和 Agent→Skill Assignment。Catalog 的 `use_when` 用于解释和诊断，不是绕过 Routing 的手动触发开关。

## 能力边界

- Rules、Agents、Skills 可以约束 Proposal、指导实施、定义 Verifier 配方或产生 Evidence。
- 它们不能增加 Core Primitive、增加 Result、重定义 `COMPLETE`，也不能直接改写 `.yuan-run/`。
- 平台不支持多 Agent 时，同一 LLM 可以按角色顺序执行，但必须保持实现与验证的证据分离。

## 默认工作流

`Intake → 用户确认 → 风险路由 → Work 最终确认 → 设计/实现 → Evidence → Role Handoff → Reducer → 交付/纠正`

## Agent 通用契约

每个 Agent 接收：Active Work Digest、Routing Assignment、相关 Artifact、前序 Attempt/Evidence/Handoff 和明确范围。输出必须是 Intake/Work/Proposal 草案、Artifact 修改、审查发现、Evidence 或 `READY/NEEDS_WORK` Handoff 候选，并给出来源指针。Agent 不得自行宣布 Core Result；Reviewer 不得修改被审对象；平台无法提供独立 Agent 时必须声明角色隔离降级。
