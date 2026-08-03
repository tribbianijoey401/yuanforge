# Agent 与 Skill 路由规则

1. 每个 Work 由 Conductor 负责状态路由；所有新请求先经过 Product Analyst 语义的需求澄清，但无阻塞问题时可由当前 LLM 顺序承担。
2. `capability route` 根据已确认 Risk/Signal 返回唯一 Agent、Skill 与 `assignments`；不得仅凭 `use_when` 自由删减。
3. 每个角色只加载自身 Assignment 中的 Skill。一个 Skill 可服务多个角色，但不能改变角色边界或 Core Truth。
4. R2 允许同一 LLM 顺序切换角色；R0/R1 的实现与审查应使用独立 Agent。平台不支持时必须如实标记隔离能力，不能伪装为独立执行。
5. 按 `routing.handoff_agents` 顺序交接；前序角色未 `READY` 或 Artifact Handoff 已过期时，后序角色不能记录 Handoff。`NEEDS_WORK` 路由回实现/设计角色并使 Reducer 返回 `CORRECT`。
6. Agent 的输出是 Intake/Work 草案、Proposal、Artifact、Evidence 或 Handoff 候选，不是 Core Result。
7. 子任务只有输入、范围、产出和验证方式都明确时才能并行；会写同一文件的任务不得并发。
8. Reviewer 不修改被审对象；修复必须由实现角色通过新 Attempt 完成，并触发受影响 Reviewer 重新交接。
