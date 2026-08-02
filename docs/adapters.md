# Adapter 与 Port

Adapter 只映射平台能力，不能修改 Core 语义。每个 Descriptor 必须逐项声明 `SUPPORTED` 或 `UNSUPPORTED`，不能用文档描述替代机械能力。

Codex 等开放 Agent 平台无法禁止模型使用原生写文件或 Shell 工具，因此只能诚实声明 `AUDITED`：Yuan 能检测 Artifact 是否发生未声明变化，但不能成为物理上不可绕过的 Action Gateway。

`ReferencePort` 提供以下稳定边界：

- Scoped File Enumeration/Read/Atomic CAS Write
- 预绑定 Executable 的 Bounded Command，无 Shell
- 可注入 Provider 的 LLM Proposal Receipt

存在 `ReferencePort` 不等于平台达到 `ENFORCED`。只有平台或 OS 确实撤销旁路工具、并让所有副作用经过该 Port 时，Descriptor 才能把 `physical_effect_mediation` 标为 `SUPPORTED`。
