     1|---
     2|name: writing-plans
     3|description: >
     4|  写 Implementation Plan 时加载。触发：Architect 分析完需求要做 Plan、
     5|  用户说「写计划」「做方案」「设计架构」「Plan」、新功能启动进入设计阶段。
     6|  产出 Pipeline-as-Code 格式的 Plan 文件，定义 Stage → Task → Gate 流水线。
     7|  读写：ARCHITECTURE（架构参考）、PROGRESS（标记当前 Plan）、
     8|  features/（关联功能文档）、pitfalls（避开已知坑）。
     9|version: 1.0.0
    10|---
    11|
    12|# 写 Plan Skill
    13|
    14|> **YuanForge 的 Plan 工程化引擎。**
    15|> 将架构设计转化为可执行的 Pipeline-as-Code Plan。
    16|
    17|---
    18|
    19|## 触发条件
    20|
    21|用户说以下任何一句 + 当前处于 Phase 1 架构阶段：
    22|
    23|- 「写计划」「做方案」「设计架构」「Plan」
    24|- 「开始规划 XX」「给我一个实现计划」
    25|
    26|或：Architect 完成需求分析和架构设计后，自动加载。
    27|
    28|---
    29|
    30|## 流程
    31|
    32|### Step 1: 加载上下文
    33|
    34|**必须加载：**
    35|- `docs/ARCHITECTURE.md` — 架构全景
    36|- `docs/[当前会话]/ — 已有功能文档（避免冲突）
    37|- `docs/pitfalls.md` — 已知陷阱
    38|- `.yuan/rules/plan-format.md` — Plan 格式规范
    39|
    40|### Step 2: 分解 Task
    41|
    42|原则：
    43|- 每个 Task 2-5 分钟可完成
    44|- 每个 Task 单文件或紧密关联的 2-3 个文件
    45|- Task 顺序遵循渐进式交付（前一个 Task 做完项目可运行）
    46|
    47|### Step 3: 定义 Stage 和 Gate
    48|
    49|每个 Stage 出口定义 Gate：
    50|- **G1 (Plan Gate):** Plan 完整 + 用户确认 → 进入 Phase 2
    51|- **G2 (Task Gate):** 每个 Task 后 Spec Review + Quality Review
    52|- **G3 (Integration Gate):** Stage 全部完成，全量测试 PASS
    53|
    54|### Step 4: 保存 Plan
    55|
    56|路径：`.yuan/plans/YYYY-MM-DD_HHMMSS-feature-name.md`
    57|
    58|### Step 5: 更新文档
    59|
    60|```
    61|→ 更新 docs/PROGRESS.md：「当前 Plan」指向刚创建的 Plan
    62|→ 创建 docs/[当前会话]/FEATURE.md（如 Architect 尚未创建）
    63|```
    64|
    65|---
    66|
    67|## 📚 文档读写规则
    68|
    69|| 阶段 | 读 | 写 |
    70||------|-----|-----|
    71|| 上下文加载 | ARCHITECTURE, pitfalls, plan-format 规范 | - |
    72|| Plan 产出后 | - | PROGRESS（当前 Plan） |
    73|| 新 Feature | - | features/NNN-xxx.md（如未创建） |
    74|
    75|---
    76|
    77|## 📤 输出模板
    78|
    79|```markdown
    80|## 📋 Plan：{Feature 名称}
    81|
    82|### Stage 1: {名称} — `[G1]`
    83|| Task | 目标 | 文件 | 测试 |
    84||------|------|------|------|
    85|| 1.1 | {目标} | `src/xxx.py` | `tests/test_xxx.py` |
    86|| 1.2 | {目标} | `src/yyy.py` | `tests/test_yyy.py` |
    87|
    88|### Stage 2: {名称} — `[G2]`
    89|| Task | 目标 | 文件 | 测试 |
    90||------|------|------|------|
    91|| 2.1 | {目标} | - | - |
    92|
    93|### Gate 定义
    94|| Gate | 阶段 | 通过条件 |
    95||------|------|---------|
    96|| G1 | Plan → 执行 | Plan 确认 |
    97|| G2 | 每个 Task | Spec + Quality PASS |
    98|| G3 | Stage → 下一个 | 全量测试 PASS |
    99|
   100|### 已知风险（来自 pitfalls）
   101|| 风险 | 来源 | 缓解 |
   102||------|------|------|
   103|| {风险} | PIT-{NNN} | {措施} |
   104|```
   105|