# Yuan vNext Framework

本目录是 Yuan 的 Canonical Framework Asset。内容来自 `main@b8fc389` 的成熟 Agent、Skill、Policy 与 References，并按 vNext 产品边界重新组织；不是从零重写的空骨架。

## 唯一依赖方向

```text
Conductor 读取 Policy 与 Workflow
→ Routing 选择 Agent
→ Agent 只加载自己声明的 Skill
→ Skill 只加载自己声明的 References Section
```

禁止以下反向或越层依赖：

- Conductor 直接加载 References；
- Agent 绕过 Skill 直接批量加载 References；
- Skill 调用 Agent；
- References 主动触发 Skill；
- 每轮预加载全部 Agent、Skill 或 References。

## 加载顺序

1. `policies/core.md`；
2. `policies/routing.md`；
3. 当前 Primary Workflow；
4. Routing 选中的 Agent Contract；
5. Agent Contract 声明的 Skill；
6. Skill 中 `Reference Routing` 命中的 Reference Section；
7. 相同相对路径的 Project Override。

旧 Contract 中的固定 Phase、Gate、`WORK`、`STATUS` 等内容仅作为历史能力说明；与 vNext Header、Core Policy 或 Routing 冲突时，以 vNext 规则为准。
