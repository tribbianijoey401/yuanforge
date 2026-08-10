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

1. `framework://policies/core.md`；
2. `framework://policies/routing.md`；
3. `framework://policies/state-contract.md` 与只读 `framework://tools/state_guard.py`；
4. 当前 `framework://workflows/*` Primary Workflow；
5. Routing 选中的 `framework://agents/*` Agent Contract；
6. Agent Contract 声明的 `framework://skills/*` Skill；
7. Skill 中 `Reference Routing` 命中的 `framework://references/*` 或 `skill://references/*` Section；
8. `framework://` 解析时自动优先采用相同相对路径的 Project Override。

`project://`、`framework://`、`skill://` 是逻辑定位符，不是目录名、环境变量或 URL。调用文件 Tool 前必须先解析为真实路径。

旧 Contract 中的固定 Phase、Gate、`WORK`、`STATUS` 等内容仅作为历史能力说明；与 vNext Header、Core Policy 或 Routing 冲突时，以 vNext 规则为准。

## State Commit Guard

Conductor 每次激活、Dispatch、Focused Result、转换、Pause、Resume 与 Distill 后都运行 `state_guard.py check`。Guard 从当前 Workflow frontmatter 与 Agent Contract 文件名动态取得合法 Stage / Agent ID，并确认 Agent 已被当前 Workflow 声明，再验证 Work/Agent state 组合；校验未输出 `STATE_VALID` 时不得继续 Dispatch。具体动作只保存在 WORK 的 Current Task；Persona/Subagent/Session 标签可使用 `agent.instance`，但不改变规范路由身份。
