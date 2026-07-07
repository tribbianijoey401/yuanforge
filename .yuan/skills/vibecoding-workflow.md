     1|---
     2|name: vibecoding-workflow
     3|description: >
     4|  YuanForge 核心工作流引擎。开发任何功能时加载。触发：用户说「开发」「实现」
     5|  「做项目」「继续」「build」、Phase 1 启动、Plan 确认后进入 Phase 2。
     6|  编排 Architect→Coder→Reviewer→Tester→DevOps 完整 4-Phase 流水线。
     7|  读写：PROGRESS（进度）、features/（功能文档）、decisions/（决策）、
     8|  pitfalls（踩坑）、bugs/（Bug 记录）。所有 Agent 的调度中心。
     9|version: 1.0.0
    10|---
    11|
    12|# YuanForge 核心工作流
    13|
    14|> **这是元框架的「引擎」** — 定义了从用户需求到可交付代码的完整流程。
    15|> 所有 YuanForge 项目必须遵循此工作流。
    16|
    17|---
    18|
    19|## 触发条件
    20|
    21|用户说以下任何一句时激活：
    22|- "开始开发 XX" / "实现 XX 功能" / "build XX" / "做一个 XX 项目"
    23|- "@严格模式 开发 XX" / "@快速模式 原型 XX" / "继续开发" / "继续上次的"
    24|
    25|激活后 **首先加载项目说明书**：`docs/INDEX.md` → `docs/PROGRESS.md`。
    26|
    27|---
    28|
    29|## 完整流程
    30|
    31|### Agent 启动：加载项目说明书
    32|
    33|```
    34|[Agent 启动]
    35|    │
    36|    ├── 1. read_file("docs/INDEX.md")                  ← 必读：入口
    37|    ├── 2. read_file("docs/PROGRESS.md")               ← 必读：进度
    38|    │      获悉：当前 Phase/Stage/Task、阻塞项、下一步
    39|    │
    40|    ├── 3. read_file("docs/ARCHITECTURE.md")           ← 必读：架构
    41|    │      了解系统全貌
    42|    │
    43|    ├── 4. read_file("docs/pitfalls.md")                 ← 必读：踩坑
    44|    │      避开已知陷阱
    45|    │
    46|    ├── 5. 如果是继续开发（PROGRESS 显示有进行中 Plan）：
    47|    │      read_file(".yuan/plans/当前 Plan")
    48|    │
    49|    └── 6. 继续下面 Phase 流程
    50|```
    51|
    52|### 判断是否需要 Phase 0
    53|
    54|检查 PROGRESS.md：
    55|- 状态为「初始化」或「空模板」→ **进入 Phase 0（审计）**
    56|- 状态为「就绪」或「开发中」→ **跳过 Phase 0，进入 Phase 1**
    57|
    58|### Pipeline 总览
    59|
    60|```
    61|用户需求 / 已有项目
    62|   │
    63|   ▼
    64|┌──────────────────────────────────────────────┐
    65|│ Phase 0: 审计（仅首次 / 嫁接项目）              │
    66|│                                               │
    67|│ 加载 project-audit skill                       │
    68|│                                               │
    69|│ 1. 覆盖扫描 — 文件树、技术栈、Git 历史         │
    70|│ 2. 架构分析 — 模块、数据流、入口点             │
    71|│ 3. 功能盘点 — 列出所有端点/功能                │
    72|│ 4. 决策回溯 — 从代码反推选型原因               │
    73|│ 5. 填充说明书 — ARCHITECTURE/PROGRESS/...     │
    74|│ 6. 差异报告 — docs vs 代码                     │
    75|│ 7. PROGRESS → 就绪                             │
    76|└────────────────────┬─────────────────────────┘
    77|                     │
    78|                     ▼
    79|              [Phase 0: 审计完成]
    80|                     │
    81|                     ▼
    82|┌──────────────────────────────────────────────┐
    83|│ Phase 1: 架构 (Architect)                     │
    84|│                                               │
    85|│ 1. 加载 iron-rules.md（铁律入脑）             │
    86|│ 2. 加载 architect agent persona               │
    87|│ 3. 分析需求 → 技术选型 → 架构设计             │
    88|│ 4. 产出 Implementation Plan                   │
    89|│ 5. 保存到 .yuan/plans/                      │
    90|│ 6. 更新 PROGRESS.md、decisions/ 决策记录       │
    91|│                                               │
    92|│ 输出：Plan + 技术选型理由                      │
    93|└────────────────────┬─────────────────────────┘
    94|                     │
    95|                     ▼
    96|              [G1: Plan Gate]
    97|                     │
    98|              用户确认 Plan？
    99|                     │
   100|            ┌────────┴────────┐
   101|            │ 否              │ 是
   102|            ▼                 ▼
   103|      修改 Plan       ┌──────────────────────────────┐
   104|                      │ Phase 2: 执行 (Conductor)      │
   105|                      │                               │
   106|                      │ 加载 subagent-driven-dev skill │
   107|                      │                               │
   108|                      │ for each Task in Plan:        │
   109|                      │   ┌──────────────────────┐    │
   110|                      │   │ 2a. Coder (TDD 实现)  │    │
   111|                      │   │ 2b. G2 Spec Review    │──┐ │
   112|                      │   │    ├─ PASS → next     │  │ │
   113|                      │   │    └─ FAIL → fix → 2b │  │ │
   114|                      │   │ 2c. G2 Quality Review │  │ │
   115|                      │   │    ├─ APPROVED → next │  │ │
   116|                      │   │    └─ REJECT → fix→2c │  │ │
   117|                      │   └──────────────────────┘    │
   118|                      │                               │
   119|                      │ 每个 Task 后更新 docs/PROGRESS.md     │
   120|                      │ 踩坑立即记录 docs/pitfalls.md         │
   121|                      └──────────────┬───────────────┘
   122|                                     │
   123|                                [G3: Integration Gate]
   124|                                     │
   125|                                     ▼
   126|                      ┌──────────────────────────────┐
   127|                      │ Phase 3: 收尾                   │
   128|                      │                               │
   129|                      │ 1. Tester — 补充集成测试       │
   130|                      │ 2. DevOps — 配置 CI/CD         │
   131|                      │ 3. 更新 ARCHITECTURE / decisions/ / docs   │
   132|                      └──────────────┬───────────────┘
   133|                                     │
   134|                                [G4: Release Gate]
   135|                                     │
   136|                                     ▼
   137|                      ┌──────────────────────────────┐
   138|                      │ Phase 4: 回顾 (Retrospector)    │
   139|                      │                               │
   140|                      │ 1. 遍历 docs/pitfalls.md 和当前会话文件夹中的 BUG 记录      │
   141|                      │ 2. 判断每个坑：                 │
   142|                      │    ├── 本项目特有 → 留在此文件  │
   143|                      │    ├── 领域通用 → 提炼为 Skill  │
   144|                      │    └── 框架通用 → 反馈到 Yuan   │
   145|                      │ 3. 记录 SESSION_LOG.md          │
   146|                      │ 4. 更新 PROGRESS.md → 已交付    │
   147|                      └──────────────────────────────┘
   148|```
   149|
   150|---
   151|
   152|## Phase 1: 架构阶段（详细）
   153|
   154|### 1.1 加载上下文
   155|
   156|```markdown
   157|必加载：
   158|- `.yuan/rules/iron-rules.md`  — 铁律
   159|- `.yuan/agents/architect.md`  — 架构师角色
   160|
   161|按需加载：
   162|- 对应技术栈 skill（如 python-fastapi）
   163|- `docs/ARCHITECTURE.md`  — 现有架构
   164|- 当前会话文件夹中的 ADR — 已有技术决策
   165|```
   166|
   167|### 1.2 需求分析
   168|
   169|分析维度：
   170|- **功能需求：** 用户要什么？
   171|- **边界条件：** 什么不算在内？
   172|- **非功能需求：** 性能、安全、可扩展性？
   173|- **约束条件：** 时间、资源、技术限制？
   174|
   175|### 1.3 技术选型
   176|
   177|选择原则：
   178|- 语言无关 — 按任务选最合适的栈
   179|- 简单优先 — 能用简单的不用复杂的
   180|- 记录理由 — 每个选型写入 `decisions/`
   181|
   182|### 1.4 架构设计
   183|
   184|输出：
   185|- 系统架构概述（2-3 句）
   186|- 模块划分
   187|- 数据流
   188|- 目录结构
   189|
   190|### 1.5 产出 Plan
   191|
   192|遵循 `plan-format.md` 的 Pipeline-as-Code 规范：
   193|- 定义 **Stage**（每个 Stage = 一组 Task + 一个 Gate）
   194|- 每个 Task 包含：`Objective` / `Files` / `Input` / `Output` / `Test` / `Gate Check`
   195|- 每个 Stage 出口定义 **Gate**：`Pass Criteria` + `Fail Action`
   196|- 标注 `Pitfalls`（已知陷阱，从经验中提取）
   197|
   198|保存路径：`.yuan/plans/YYYY-MM-DD_HHMMSS-<feature-slug>.md`
   199|
   200|### 1.6 用户确认
   201|
   202|展示 Plan 摘要，等待用户确认或修改。
   203|
   204|---
   205|
   206|## Phase 2: 执行阶段（详细）
   207|
   208|### 2.1 加载 Conductor 模式
   209|
   210|使用 `subagent-driven-development` skill 执行 Plan：
   211|- 读 Plan 文件一次，提取所有 Task
   212|- 创建 TODO 列表追踪进度
   213|
   214|### 2.2 逐 Task 执行（含 Gate）
   215|
   216|对每个 Task：
   217|
   218|```
   219|Step A: 派 Coder (新 subagent)
   220|  → 加载 coder agent persona + TDD skill
   221|  → 提供 Task 完整上下文
   222|  → 执行 TDD → 原子提交
   223|
   224|Step B: Gate G2-TASK — Spec Review
   225|  → 加载 reviewer agent persona
   226|  → 对照 Plan 检查实现
   227|  → PASS → 进入 Step C
   228|  → FAIL → Coder 修复 → 重新审查
   229|           → 同一 Task 连续 3 次 FAIL → 触发架构复盘
   230|
   231|Step C: Gate G2-TASK — Quality Review
   232|  → 代码质量审查
   233|  → APPROVED → 标记 Task 完成 `[G2 ✓]`
   234|  → REJECT → Coder 修复 → 重新审查
   235|
   236|Step D: Stage Gate 检查
   237|  → 当前 Stage 所有 Task 完成？
   238|    → 是 → 执行 Stage Gate（G1/G3/G4）
   239|    → 否 → 下一个 Task
   240|```
   241|
   242|### 2.3 快速模式
   243|
   244|`@快速模式` 下：
   245|- 跳过 Step B（Spec Review）
   246|- Step C 只检查 Critical Issues
   247|- 允许多个 task 合并提交
   248|
   249|---
   250|
   251|## Phase 3: 收尾阶段（详细）
   252|
   253|### 3.1 集成测试
   254|
   255|- 加载 `tester` agent persona
   256|- 补充集成测试和边界测试
   257|- 运行完整测试套件
   258|
   259|### 3.2 CI/CD 配置
   260|
   261|- 加载 `devops` agent persona
   262|- 配置 GitHub Actions 或等价 CI
   263|- 编写 Dockerfile / docker-compose
   264|
   265|### 3.3 文档更新
   266|
   267|- 更新 `docs/ARCHITECTURE.md`（如有架构变更）
   268|- 更新当前会话文件夹中的 ADR（如有新决策）
   269|- 更新 `docs/glossary.md`（如有新术语）
   270|
   271|---
   272|
   273|## Phase 4: 回顾阶段（详细）
   274|
   275|> Harness 的回环学习在此落地。
   276|
   277|### 4.1 遍历踩坑记录
   278|
   279|加载 docs/pitfalls.md 和当前会话文件夹中的 BUG 记录，逐条检查「归档判断」：
   280|
   281|```
   282|for each PIT in pitfalls.md:
   283|    if PIT.归档判断 == "本项目特有":
   284|        → 留在此文件，不操作
   285|    
   286|    if PIT.归档判断 == "提炼为 Skill":
   287|        → 如果是新领域 → skill_manage(action='create', ...)
   288|        → 如果是已有 Skill 的补充 → skill_manage(action='patch', ...)
   289|        → 在 docs/pitfalls.md 中标注「已归档至 Skill: <name>」
   290|    
   291|    if PIT.归档判断 == "反馈到 Yuan":
   292|        → 评估是否需要修改铁律或流程 Skill
   293|        → 修改后提交到 YuanForge 仓库
   294|```
   295|
   296|### 4.2 写会话日志
   297|
   298|追加 `SESSION_LOG.md`：
   299|```markdown
   300|### Session N: YYYY-MM-DD — [项目名] 交付
   301|
   302|- **完成:** 所有 Phase 1-3
   303|- **决策:** 见 decisions/
   304|- **踩坑:** PIT-001, PIT-002
   305|- **Skill 提炼:** [如有]
   306|- **Commit:** abc1234
   307|```
   308|
   309|### 4.3 更新进度
   310|
   311|`docs/PROGRESS.md` 状态更新为「已交付」。
   312|
   313|---
   314|
   315|## 铁律执行
   316|
   317|本 Skill 整个流程严格遵守 YuanForge 九条铁律：
   318|
   319|| 铁律 | 执行点 |
   320||------|--------|
   321|| Ⅰ. 计划先行 | Phase 1 产 Plan |
   322|| Ⅱ. TDD 先行 | 每个 Task 内 Red → Green → Refactor |
   323|| Ⅲ. 两阶段审查 | 每个 Task 后 Spec → Quality |
   324|| Ⅳ. 原子提交 | 每个 Task 一个 Commit |
   325|| Ⅴ. 上下文隔离 | 每个 Task 新 Subagent |
   326|| Ⅵ. 文档即代码 | Phase 1 写决策，Phase 3 更新文档 |
   327|| Ⅶ. 渐进式交付 | Task 顺序保证可运行 |
   328|| Ⅷ. 质量门禁 | G1→G2→G3→G4，Phase 4 归档 |
   329|
   330|---
   331|
   332|## 相关 Skill
   333|
   334|- `project-audit` — 审计现有项目（Phase 0）
   335|- `writing-plans` — 写 Implementation Plan
   336|- `subagent-driven-development` — Subagent 执行引擎
   337|- `test-driven-development` — TDD 纪律
   338|- `requesting-code-review` — 代码审查
   339|- `project-bootstrap` — 项目初始化（含嫁接模式）
   340|- `project-memory` — 项目记忆管理
   341|