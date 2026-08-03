# Adapter 与 Port

Adapter 只映射平台能力，不能修改 Core 语义。每个 Descriptor 必须逐项声明 `SUPPORTED` 或 `UNSUPPORTED`，不能用文档描述替代机械能力。

Codex 等开放 Agent 平台无法禁止模型使用原生写文件或 Shell 工具，因此只能诚实声明 `AUDITED`：Yuan 能检测 Artifact 是否发生未声明变化，但不能成为物理上不可绕过的 Action Gateway。

`ReferencePort` 提供以下稳定边界：

- Scoped File Enumeration/Read/Atomic CAS Write
- 预绑定 Executable 的 Bounded Command，无 Shell
- 可注入 Provider 的 LLM Proposal Receipt

存在 `ReferencePort` 不等于平台达到 `ENFORCED`。只有平台或 OS 确实撤销旁路工具、并让所有副作用经过该 Port 时，Descriptor 才能把 `physical_effect_mediation` 标为 `SUPPORTED`。

## Agent/Skill 调用边界

`capability list/resolve` 负责确定性发现角色与 Skill，并返回必须读取的路径和 Digest；它不虚假宣称能够在所有平台创建子 Agent。Codex、Claude Code 等平台由当前 LLM 使用平台原生委派能力执行所选 Agent Contract。平台没有委派能力时，同一 LLM 按角色顺序执行并声明隔离降级，Core 只接受最终的 Attempt 与 Evidence，不依赖某个特定多 Agent API。
