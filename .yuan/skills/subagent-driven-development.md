     1|---
     2|name: subagent-driven-development
     3|description: >
     4|  Phase 2 执行 Plan 时加载。触发：Plan 确认后进入 Phase 2、Conductor 需要
     5|  逐 Task 派发 Coder→Reviewer 子流程、用户说「执行 Plan」「开始实现」。
     6|  管理 TODO 列表、派发 Subagent（Coder→Reviewer）、追踪 G2 Gate 状态。
     7|  读写：PROGRESS（每 Task 更新）、features/当前（上下文传递给 Subagent）、
     8|  Plan（读取 Task 描述）。
     9|version: 1.0.0
    10|---
    11|
    12|# Subagent 驱动开发 Skill
    13|
    14|> **YuanForge 的 Phase 2 执行引擎。**
    15|> 读取 Plan → 逐 Task 派发 Subagent → 追踪 Gate 状态。
    16|
    17|---
    18|
    19|## 触发条件
    20|
    21|- Phase 2 启动：Plan 确认后
    22|- Conductor 激活：需要逐 Task 执行
    23|- 用户说「执行 Plan」「开始实现」「继续下一个 Task」
    24|
    25|---
    26|
    27|## 流程
    28|
    29|### Step 1: 加载 Plan
    30|
    31|1. 读取 `docs/PROGRESS.md` — 当前 Plan 路径
    32|2. 读取 Plan 文件 — 所有 Task 列表
    33|3. 读取 当前会话文件夹中的 FEATURE.md — 当前功能文档
    34|4. 创建 TODO 列表追踪全部 Task
    35|
    36|### Step 2: 逐 Task 执行
    37|
    38|对每个 Task：
    39|
    40|```
    41|Task N: {描述}
    42|  │
    43|  ├── 派 Coder Subagent
    44|  │   ├── 上下文：Plan Task 描述 + features/NNN-xxx.md + pitfalls
    45|  │   ├── 加载：coder persona + test-driven-development skill
    46|  │   └── 等待 Coder 完成 → Commit
    47|  │
    48|  ├── Gate G2-TASK: Spec Review
    49|  │   ├── 派 Reviewer Subagent
    50|  │   ├── 加载：reviewer persona + requesting-code-review skill
    51|  │   ├── PASS → 进入 Quality Review
    52|  │   └── FAIL → 退回 Coder（附差距列表）→ 最多 3 轮
    53|  │
    54|  ├── Gate G2-TASK: Quality Review
    55|  │   ├── APPROVED → 标记 Task 完成 `[G2 ✓]`
    56|  │   └── REJECT → 退回 Coder → 最多 3 轮
    57|  │
    58|  └── 更新 PROGRESS → 下一个 Task
    59|```
    60|
    61|### Step 3: Stage Gate 检查
    62|
    63|当前 Stage 所有 Task 完成 → 执行 Stage Gate（G1/G3/G4）。
    64|
    65|### Step 4: Phase 完成
    66|
    67|Phase 2 全部 Stage 完成 → 更新 PROGRESS → 进入 Phase 3。
    68|
    69|---
    70|
    71|## 📚 文档读写规则
    72|
    73|| 阶段 | 读 | 写 |
    74||------|-----|-----|
    75|| 加载 Plan | Plan 文件, features/当前, PROGRESS, pitfalls | - |
    76|| 每次 Task 完成 | - | PROGRESS（当前 Task → ✓） |
    77|| 每次 Stage 完成 | - | PROGRESS（Gate 标注） |
    78|| 传递上下文给 Subagent | features/当前, pitfalls, CONVENTIONS | - |
    79|
    80|---
    81|
    82|## Subagent 上下文模板
    83|
    84|派 Coder 时注入：
    85|
    86|```markdown
    87|## Task 上下文
    88|
    89|### Plan 要求
    90|{Task 完整描述}
    91|
    92|### 项目文档
    93|- features/：{当前功能文档路径} — 了解设计意图
    94|- pitfalls：docs/pitfalls.md — 避免已知坑
    95|- CONVENTIONS：docs/CONVENTIONS.md — 代码规范
    96|
    97|### 要求
    98|- TDD: Red → Green → Refactor
    99|- 完成后更新 features/ 的「修改文件」表
   100|- 遇问题创建 bugs/ 文档
   101|- 原子提交
   102|```
   103|
   104|## 快速模式
   105|
   106|`@快速模式` 下：
   107|- 跳过 Spec Review（只做 Quality）
   108|- 允许多 Task 合并提交
   109|- G3/G4 可选
   110|