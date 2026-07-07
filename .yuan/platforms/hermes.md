     1|# Hermes Agent 平台适配
     2|
     3|> 本文件告诉 Hermes Agent 如何执行 YuanForge 的定义。
     4|
     5|---
     6|
     7|## 加载规则
     8|
     9|Hermes 的系统提示会注入 `.yuan/rules/` 下的规则文件：
    10|
    11|| 规则 | 加载方式 |
    12||------|---------|
    13|| iron-rules.md | 系统提示中注入 |
    14|| plan-format.md | 写入 Plan 时参考 |
    15|| docs-framework.md | project-bootstrap skill 引用 |
    16|
    17|---
    18|
    19|## 派发子 Agent（Conductor）
    20|
    21|使用 Hermes 的 `delegate_task` 工具：
    22|
    23|```markdown
    24|# Conductor 的标准操作：
    25|1. 读取 Plan 中的 Dispatch Table
    26|2. 解析依赖关系 → 构建 DAG
    27|3. 为每个 ready Task 调用 delegate_task，context 含：
    28|   - Task 详细 spec
    29|   - 对应角色合约（contracts/）
    30|   - 铁律引用
    31|   - 上游产出物路径
    32|```
    33|
    34|可选：如配置了 Kanban 系统，用 `kanban_create` 创建持久化任务板。
    35|
    36|---
    37|
    38|## 加载 Skill
    39|
    40|使用 `skill_view(name)` 工具，skill 名称对应 `.yuan/skills/` 下的文件名（不含扩展名）。
    41|
    42|示例：
    43|```
    44|skill_view("vibecoding-workflow")
    45|skill_view("test-driven-development")
    46|```
    47|
    48|---
    49|
    50|## 追踪进度
    51|
    52|- `docs/PROGRESS.md` — 项目进度中枢
    53|- `.yuan/docs/SESSION_LOG.md` — 会话日志
    54|- `.yuan/plans/` — Plan 存档
    55|
    56|---
    57|
    58|## 工具映射
    59|
    60|| YuanForge 概念 | Hermes 工具 |
    61||---------------|------------|
    62|| 派发子 Agent | `delegate_task` |
    63|| 加载 Skill | `skill_view` |
    64|| 项目管理 | `kanban_*` 系列 |
    65|| 终端执行 | `terminal` |
    66|| 文件操作 | `read_file` / `write_file` / `patch` |
    67|| Git 操作 | `terminal` (git 命令) |
    68|
    69|---
    70|
    71|## 注意事项
    72|
    73|- Hermes 的 `delegate_task` 是 **同步**的 — 父 Agent 等待子 Agent 完成
    74|- 最多 3 个并行子 Agent（可配置 `delegation.max_concurrent_children`）
    75|- 子 Agent 没有父会话的记忆 — 必须通过 context 传递全部信息
    76|