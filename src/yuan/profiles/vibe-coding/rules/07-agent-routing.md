# Agent 与 Skill 路由规则

1. 每个 Work 由 Conductor 负责状态路由；简单任务可以由当前 LLM 承担该职责。
2. 根据 Capability Catalog 的 `use_when` 选择最小 Agent 与 Skill 集合，不得一次加载全部文件。
3. R2 工作允许同一 LLM 顺序切换实现和验证角色；R0/R1 的实现与验证应使用独立 Agent，平台不支持时必须声明降级。
4. Agent 的输出是 Proposal、Artifact 或 Evidence 候选，不是 Core Result。
5. 子任务只有输入、范围、产出和验证方式都明确时才能并行；会写同一文件的任务不得并发。
6. Reviewer 不修改被审对象；需要修复时返回发现，由实现角色创建新的 Attempt。
