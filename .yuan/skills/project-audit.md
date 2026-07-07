     1|---
     2|name: project-audit
     3|description: >
     4|  审计现有项目，填充 YuanForge docs/ 说明书。触发：用户说「审计项目」
     5|  「接手项目」「了解现有项目」「嫁接 YuanForge」「填充说明书」「分析现有代码」
     6|  「项目审计」。也用于 project-bootstrap 的嫁接模式。
     7|  读取项目全部代码，填写 PROGRESS/ARCHITECTURE/decisions/glossary/
     8|  pitfalls/features/SETUP/CONVENTIONS。产出审计报告，列出 docs/ 与实际代码的差异。
     9|version: 1.0.0
    10|---
    11|
    12|# 项目审计 Skill
    13|
    14|> **目的：** 让 YuanForge 能接手一个已有代码的半路项目。
    15|> 审计 = 阅读全部代码 → 理解现状 → 填充说明书 → 发现差异。
    16|
    17|---
    18|
    19|## 触发条件
    20|
    21|用户说以下任何一句时激活：
    22|- "审计项目" / "分析现有项目" / "了解这个项目"
    23|- "把 YuanForge 嫁接到这个项目" / "填充说明书"
    24|- "接手这个项目" / "这是半路项目，帮我梳理"
    25|
    26|---
    27|
    28|## 审计流程（7 步）
    29|
    30|```
    31|┌─────────────────────────────────────────────────────┐
    32|│                Phase 0: 项目审计                       │
    33|│                                                      │
    34|│  Step 1: 覆盖扫描（5 分钟）                           │
    35|│     ├── 文件树全览                                    │
    36|│     ├── 识别技术栈（package.json/requirements.txt/...）│
    37|│     ├── 识别构建工具（Makefile/docker-compose/...）   │
    38|│     └── Git 历史速览（最近 20 条 commit）              │
    39|│                                                      │
    40|│  Step 2: 架构分析                                    │
    41|│     ├── 读入口文件（main.py/index.ts/...）            │
    42|│     ├── 读核心模块（src/ 下的主要目录）                │
    43|│     ├── 读配置文件（config/env/...）                  │
    44|│     └── 画模块依赖关系图                              │
    45|│                                                      │
    46|│  Step 3: 功能盘点                                    │
    47|│     ├── 读路由/API 定义 → 列出所有端点                │
    48|│     ├── 读数据模型 → 列出所有实体                     │
    49|│     ├── 读测试 → 了解测试覆盖范围                     │
    50|│     └── 与用户确认："我看到这些功能，对吗？"          │
    51|│                                                      │
    52|│  Step 4: 技术决策回溯                                │
    53|│     ├── 从 package.json/requirements.txt 反推选型    │
    54|│     ├── 从注释/README/commit 中找设计意图             │
    55|│     └── 无法确定 → 标注「待确认」，询问用户           │
    56|│                                                      │
    57|│  Step 5: 填充说明书                                  │
    58|│     ├── docs/PROGRESS.md    ← 当前进度               │
    59|│     ├── docs/ARCHITECTURE.md ← 架构全景               │
    60|│     ├── docs/SETUP.md       ← 如何跑起来              │
    61|│     ├── docs/CONVENTIONS.md ← 从代码中归纳规范        │
    62|│     ├── docs/glossary.md    ← 领域术语                │
    63|│     ├── 当前会话文件夹/         ← ADR-NNN.md 等        │
    64|│     ├── 当前会话文件夹/         ← FEATURE.md        │
    65|│     └── docs/pitfalls.md    ← （如有已知坑）          │
    66|│                                                      │
    67|│  Step 6: 差异报告                                    │
    68|│     ├── docs/ 描述的 vs 实际代码的差异                │
    69|│     ├── 缺失的文档/测试/配置                          │
    70|│     └── 输出 Markdown 报告                           │
    71|│                                                      │
    72|│  Step 7: 更新 PROGRESS → 就绪                         │
    73|└─────────────────────────────────────────────────────┘
    74|```
    75|
    76|---
    77|
    78|## Step 1: 覆盖扫描
    79|
    80|### 1.1 获取项目全貌
    81|
    82|```bash
    83|# 文件树（去掉 node_modules/.venv 等噪声）
    84|find . -not -path '*/node_modules/*' -not -path '*/.git/*' \
    85|       -not -path '*/__pycache__/*' -not -path '*/.venv/*' \
    86|       -type f | head -100
    87|
    88|# 如果项目很大，只看关键目录
    89|ls -la src/ app/ lib/ api/ 2>/dev/null
    90|```
    91|
    92|### 1.2 识别技术栈
    93|
    94|查找以下特征文件，确定技术栈：
    95|
    96|| 文件 | 推断 |
    97||------|------|
    98|| `package.json` | Node.js / TypeScript / JavaScript |
    99|| `requirements.txt` / `pyproject.toml` | Python |
   100|| `go.mod` | Go |
   101|| `Cargo.toml` | Rust |
   102|| `Gemfile` | Ruby |
   103|| `pom.xml` / `build.gradle` | Java / Kotlin |
   104|| `Dockerfile` | 部署方式 |
   105|| `docker-compose.yml` | 服务编排 |
   106|| `.github/workflows/` | CI/CD |
   107|
   108|### 1.3 Git 历史速览
   109|
   110|```bash
   111|git log --oneline -20
   112|git log --oneline --all --graph -30  # 看分支情况
   113|```
   114|
   115|---
   116|
   117|## Step 2: 架构分析
   118|
   119|### 2.1 入口文件
   120|
   121|```bash
   122|# 找到入口点
   123|grep -r "if __name__" --include="*.py" -l | head -5   # Python
   124|grep -r "app.listen\|server.start" --include="*.ts" --include="*.js" -l | head -5  # Node
   125|```
   126|
   127|读取入口文件，理解：
   128|- 启动时加载了什么？
   129|- 有哪些中间件/插件？
   130|- 路由是怎么组织的？
   131|
   132|### 2.2 核心模块
   133|
   134|```
   135|# 目录结构 → 模块划分
   136|src/
   137|├── models/      → 数据模型 → 有哪些实体？
   138|├── routes/      → API 路由 → 有哪些端点？
   139|├── services/    → 业务逻辑 → 核心功能是什么？
   140|├── middleware/   → 中间件   → 有哪些横切关注点？
   141|└── utils/       → 工具函数 → 有哪些通用能力？
   142|```
   143|
   144|### 2.3 数据模型
   145|
   146|```bash
   147|# Python: SQLAlchemy / Django models
   148|grep -r "class.*Model\|class.*Base" --include="*.py" -l | head -10
   149|
   150|# Node: Prisma / TypeORM / Mongoose
   151|grep -r "model\|schema" --include="*.ts" --include="*.js" -l | head -10
   152|```
   153|
   154|读取数据模型文件，列出所有实体和关系。
   155|
   156|---
   157|
   158|## Step 3: 功能盘点
   159|
   160|### 3.1 API 端点
   161|
   162|```bash
   163|# Python FastAPI/Flask
   164|grep -r "@app\.\|@router\.\|@bp\." --include="*.py" -l | head -10
   165|
   166|# Node Express/Koa
   167|grep -r "\.get\|\.post\|\.put\|\.delete" --include="*.ts" --include="*.js" -l | head -10
   168|```
   169|
   170|### 3.2 列出所有功能
   171|
   172|对每个端点，用自然语言描述：
   173|- `GET /api/users` → 获取用户列表
   174|- `POST /api/users` → 创建用户
   175|- ...
   176|
   177|### 3.3 与用户确认
   178|
   179|```
   180|审计发现以下功能，请确认：
   181|1. 用户注册/登录（JWT 认证）
   182|2. 用户列表查询（支持分页）
   183|3. ...
   184|
   185|还有我遗漏的吗？哪些功能还未完成？
   186|```
   187|
   188|---
   189|
   190|## Step 4: 技术决策回溯
   191|
   192|### 4.1 从依赖反推
   193|
   194|```json
   195|// package.json → "dependencies"
   196|{
   197|  "express": "^4.18",      // → 为什么选 Express 而非 Fastify？
   198|  "prisma": "^5.0",        // → 为什么选 Prisma 而非 TypeORM？
   199|  "postgresql": "...",     // → 为什么选 PostgreSQL 而非 MySQL？
   200|}
   201|```
   202|
   203|### 4.2 从代码注释中找
   204|
   205|```bash
   206|grep -r "TODO\|FIXME\|HACK\|NOTE\|为什么\|因为" --include="*.py" --include="*.ts" | head -20
   207|```
   208|
   209|### 4.3 无法确定 → 标注「待确认」
   210|
   211|```
   212|以下选型原因不确定，请补充：
   213|- 为什么用 Redis？（没有找到相关说明）
   214|- 为什么前端用 Vue 而非 React？（没有 ADR 记录）
   215|```
   216|
   217|---
   218|
   219|## Step 5: 填充说明书
   220|
   221|按以下顺序填写 docs/，每填完一个就输出确认：
   222|
   223|### 5.1 ARCHITECTURE.md
   224|
   225|```
   226|项目概述:
   227|- 项目名: [从 package.json/README 获取]
   228|- 一句话描述: [从 README 或代码推断]
   229|- 技术栈表: [语言/框架/数据库/缓存/消息队列...]
   230|- 模块划分: [从目录结构反推 + 每个模块的职责]
   231|- 数据流: [请求 → 路由 → 服务层 → 数据层 → 响应]
   232|```
   233|
   234|### 5.2 SETUP.md
   235|
   236|```
   237|从 Makefile/README/docker-compose 中提取：
   238|- 前置依赖: Node 18+, PostgreSQL 15+, ...
   239|- 安装步骤: npm install / pip install -r requirements.txt
   240|- 环境变量: 从 .env.example 或代码中搜索 process.env / os.getenv
   241|- 启动命令: npm run dev / python main.py
   242|```
   243|
   244|### 5.3 CONVENTIONS.md
   245|
   246|```
   247|从代码中归纳：
   248|- 命名风格: camelCase? snake_case? PascalCase?
   249|- 目录约定: src/ vs app/ vs lib/
   250|- 提交格式: 从 git log 归纳
   251|```
   252|
   253|### 5.4 PROGRESS.md
   254|
   255|```
   256|当前状态:
   257|- 当前 Phase: [1-架构 / 2-执行 / 3-收尾]（从代码完整度判断）
   258|- 已完成功能: [来自 Step 3 的盘点]
   259|- 进行中: [询问用户]
   260|- 下一步: [询问用户]
   261|```
   262|
   263|### 5.5 features/
   264|
   265|```
   266|每个已完成的功能在对应会话文件夹中创建 FEATURE.md：
   267|- 需求描述: [功能是干什么的]
   268|- 修改的文件: [列出相关文件]
   269|- API: [列出端点]
   270|```
   271|
   272|### 5.6 decisions/
   273|
   274|```
   275|每个反推出来的决策在对应会话文件夹中创建 ADR-NNN.md：
   276|- 决策: 选了 XXX
   277|- 备选方案: [如果能推断出来]
   278|- 原因: [如果能从注释/commit 推断]
   279|```
   280|
   281|### 5.7 glossary.md
   282|
   283|```
   284|从代码中提取领域术语：
   285|- 如果项目是电商 → SKU/SPU/OMS/WMS...
   286|- 如果是 SaaS → Tenant/Workspace/Subscription...
   287|```
   288|
   289|### 5.8 pitfalls.md
   290|
   291|```
   292|保留模板。如果用户提到了已知坑，填写。
   293|```
   294|
   295|---
   296|
   297|## Step 6: 差异报告
   298|
   299|完成填充后，输出审计报告：
   300|
   301|```markdown
   302|## 📊 项目审计报告
   303|
   304|### 基本信息
   305|- 项目名: XXX
   306|- 技术栈: TypeScript + Express + PostgreSQL
   307|- 代码规模: 45 个 .ts 文件，约 8,500 行
   308|- 测试文件: 3 个（覆盖率偏低）
   309|
   310|### 功能清单（7 个）
   311|| 编号 | 功能 | 状态 | 文档 |
   312||------|------|------|------|
   313|| FEAT-001 | 用户认证 | ✅ 完成 | features/001-user-auth.md |
   314|| FEAT-002 | 数据 CRUD | ✅ 完成 | features/002-data-crud.md |
   315|| FEAT-003 | 文件上传 | 🟡 部分 | features/003-file-upload.md |
   316|
   317|### 差异/风险
   318|| 项 | 说明 |
   319||----|------|
   320|| ⚠️ 测试少 | 只有 3 个测试文件，核心业务逻辑未覆盖 |
   321|| ⚠️ 无 CI | 没有 .github/workflows/ |
   322|| ✅ 文档就绪 | docs/ 已填完，可进入 Phase 1 |
   323|
   324|### 下一步建议
   325|1. [用户确认的下一步]
   326|```
   327|
   328|---
   329|
   330|## Step 7: 更新 PROGRESS.md
   331|
   332|将 PROGRESS.md 状态设为「审计完成 → 就绪」，等待用户下达第一个开发指令。
   333|
   334|---
   335|
   336|## 审计原则
   337|
   338|1. **宁可多问，不要猜。** 无法从代码确定的（设计意图、选型原因），标注「待确认」问用户
   339|2. **先广度，后深度。** Step 1-3 快速覆盖，Step 4-5 逐步深入
   340|3. **文档是快照，不是真理。** 审计报告标注时间戳，后续开发会持续更新
   341|4. **差异不是错误，是指引。** docs/ 描述的理想 vs 代码的实际 → 差异就是下一步的工作量
   342|