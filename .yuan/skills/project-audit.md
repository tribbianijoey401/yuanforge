---
name: project-audit
description: >
审计现有项目，填充 YuanForge docs/ 说明书。触发：用户说「审计项目」
「接手项目」「了解现有项目」「嫁接 YuanForge」「填充说明书」「分析现有代码」
「项目审计」。也用于 project-bootstrap 的嫁接模式。
读取项目全部代码，填写 PROGRESS/ARCHITECTURE/decisions/glossary/
pitfalls/features/SETUP/CONVENTIONS。产出审计报告，列出 docs/ 与实际代码的差异。
version: 1.0.0
---

# 项目审计 Skill

> **目的：** 让 YuanForge 能接手一个已有代码的半路项目。
> 审计 = 阅读全部代码 → 理解现状 → 填充说明书 → 发现差异。

---

## 触发条件

用户说以下任何一句时激活：
- "审计项目" / "分析现有项目" / "了解这个项目"
- "把 YuanForge 嫁接到这个项目" / "填充说明书"
- "接手这个项目" / "这是半路项目，帮我梳理"

---

## 审计流程（7 步）

```
┌─────────────────────────────────────────────────────┐
│                Phase 0: 项目审计                       │
│                                                      │
│  Step 1: 覆盖扫描（5 分钟）                           │
│     ├── 文件树全览                                    │
│     ├── 识别技术栈（package.json/requirements.txt/...）│
│     ├── 识别构建工具（Makefile/docker-compose/...）   │
│     └── Git 历史速览（最近 20 条 commit）              │
│                                                      │
│  Step 2: 架构分析                                    │
│     ├── 读入口文件（main.py/index.ts/...）            │
│     ├── 读核心模块（src/ 下的主要目录）                │
│     ├── 读配置文件（config/env/...）                  │
│     └── 画模块依赖关系图                              │
│                                                      │
│  Step 3: 功能盘点                                    │
│     ├── 读路由/API 定义 → 列出所有端点                │
│     ├── 读数据模型 → 列出所有实体                     │
│     ├── 读测试 → 了解测试覆盖范围                     │
│     └── 与用户确认："我看到这些功能，对吗？"          │
│                                                      │
│  Step 4: 技术决策回溯                                │
│     ├── 从 package.json/requirements.txt 反推选型    │
│     ├── 从注释/README/commit 中找设计意图             │
│     └── 无法确定 → 标注「待确认」，询问用户           │
│                                                      │
│  Step 5: 填充说明书                                  │
│     ├── docs/PROGRESS.md    ← 当前进度               │
│     ├── docs/ARCHITECTURE.md ← 架构全景               │
│     ├── docs/SETUP.md       ← 如何跑起来              │
│     ├── docs/CONVENTIONS.md ← 从代码中归纳规范        │
│     ├── docs/glossary.md    ← 领域术语                │
│     ├── 当前会话文件夹/         ← ADR-NNN.md 等        │
│     ├── 当前会话文件夹/         ← FEATURE.md        │
│     └── docs/pitfalls.md    ← （如有已知坑）          │
│                                                      │
│  Step 6: 差异报告                                    │
│     ├── docs/ 描述的 vs 实际代码的差异                │
│     ├── 缺失的文档/测试/配置                          │
│     └── 输出 Markdown 报告                           │
│                                                      │
│  Step 7: 更新 PROGRESS → 就绪                         │
└─────────────────────────────────────────────────────┘
```

---

## Step 1: 覆盖扫描

### 1.1 获取项目全貌

```bash
# 文件树（去掉 node_modules/.venv 等噪声）
find . -not -path '*/node_modules/*' -not -path '*/.git/*' \
-not -path '*/__pycache__/*' -not -path '*/.venv/*' \
-type f | head -100

# 如果项目很大，只看关键目录
ls -la src/ app/ lib/ api/ 2>/dev/null
```

### 1.2 识别技术栈

查找以下特征文件，确定技术栈：

| 文件 | 推断 |
|------|------|
| `package.json` | Node.js / TypeScript / JavaScript |
| `requirements.txt` / `pyproject.toml` | Python |
| `go.mod` | Go |
| `Cargo.toml` | Rust |
| `Gemfile` | Ruby |
| `pom.xml` / `build.gradle` | Java / Kotlin |
| `Dockerfile` | 部署方式 |
| `docker-compose.yml` | 服务编排 |
| `.github/workflows/` | CI/CD |

### 1.3 Git 历史速览

```bash
git log --oneline -20
git log --oneline --all --graph -30  # 看分支情况
```

---

## Step 2: 架构分析

### 2.1 入口文件

```bash
# 找到入口点
grep -r "if __name__" --include="*.py" -l | head -5   # Python
grep -r "app.listen\|server.start" --include="*.ts" --include="*.js" -l | head -5  # Node
```

读取入口文件，理解：
- 启动时加载了什么？
- 有哪些中间件/插件？
- 路由是怎么组织的？

### 2.2 核心模块

```
# 目录结构 → 模块划分
src/
├── models/      → 数据模型 → 有哪些实体？
├── routes/      → API 路由 → 有哪些端点？
├── services/    → 业务逻辑 → 核心功能是什么？
├── middleware/   → 中间件   → 有哪些横切关注点？
└── utils/       → 工具函数 → 有哪些通用能力？
```

### 2.3 数据模型

```bash
# Python: SQLAlchemy / Django models
grep -r "class.*Model\|class.*Base" --include="*.py" -l | head -10

# Node: Prisma / TypeORM / Mongoose
grep -r "model\|schema" --include="*.ts" --include="*.js" -l | head -10
```

读取数据模型文件，列出所有实体和关系。

---

## Step 3: 功能盘点

### 3.1 API 端点

```bash
# Python FastAPI/Flask
grep -r "@app\.\|@router\.\|@bp\." --include="*.py" -l | head -10

# Node Express/Koa
grep -r "\.get\|\.post\|\.put\|\.delete" --include="*.ts" --include="*.js" -l | head -10
```

### 3.2 列出所有功能

对每个端点，用自然语言描述：
- `GET /api/users` → 获取用户列表
- `POST /api/users` → 创建用户
- ...

### 3.3 与用户确认

```
审计发现以下功能，请确认：
1. 用户注册/登录（JWT 认证）
2. 用户列表查询（支持分页）
3. ...

还有我遗漏的吗？哪些功能还未完成？
```

---

## Step 4: 技术决策回溯

### 4.1 从依赖反推

```json
// package.json → "dependencies"
{
"express": "^4.18",      // → 为什么选 Express 而非 Fastify？
"prisma": "^5.0",        // → 为什么选 Prisma 而非 TypeORM？
"postgresql": "...",     // → 为什么选 PostgreSQL 而非 MySQL？
}
```

### 4.2 从代码注释中找

```bash
grep -r "TODO\|FIXME\|HACK\|NOTE\|为什么\|因为" --include="*.py" --include="*.ts" | head -20
```

### 4.3 无法确定 → 标注「待确认」

```
以下选型原因不确定，请补充：
- 为什么用 Redis？（没有找到相关说明）
- 为什么前端用 Vue 而非 React？（没有 ADR 记录）
```

---

## Step 5: 填充说明书

按以下顺序填写 docs/，每填完一个就输出确认：

### 5.1 ARCHITECTURE.md

```
项目概述:
- 项目名: [从 package.json/README 获取]
- 一句话描述: [从 README 或代码推断]
- 技术栈表: [语言/框架/数据库/缓存/消息队列...]
- 模块划分: [从目录结构反推 + 每个模块的职责]
- 数据流: [请求 → 路由 → 服务层 → 数据层 → 响应]
```

### 5.2 SETUP.md

```
从 Makefile/README/docker-compose 中提取：
- 前置依赖: Node 18+, PostgreSQL 15+, ...
- 安装步骤: npm install / pip install -r requirements.txt
- 环境变量: 从 .env.example 或代码中搜索 process.env / os.getenv
- 启动命令: npm run dev / python main.py
```

### 5.3 CONVENTIONS.md

```
从代码中归纳：
- 命名风格: camelCase? snake_case? PascalCase?
- 目录约定: src/ vs app/ vs lib/
- 提交格式: 从 git log 归纳
```

### 5.4 PROGRESS.md

```
当前状态:
- 当前 Phase: [1-架构 / 2-执行 / 3-收尾]（从代码完整度判断）
- 已完成功能: [来自 Step 3 的盘点]
- 进行中: [询问用户]
- 下一步: [询问用户]
```

### 5.5 features/

```
每个已完成的功能在对应会话文件夹中创建 FEATURE.md：
- 需求描述: [功能是干什么的]
- 修改的文件: [列出相关文件]
- API: [列出端点]
```

### 5.6 decisions/

```
每个反推出来的决策在对应会话文件夹中创建 ADR-NNN.md：
- 决策: 选了 XXX
- 备选方案: [如果能推断出来]
- 原因: [如果能从注释/commit 推断]
```

### 5.7 glossary.md

```
从代码中提取领域术语：
- 如果项目是电商 → SKU/SPU/OMS/WMS...
- 如果是 SaaS → Tenant/Workspace/Subscription...
```

### 5.8 pitfalls.md

```
保留模板。如果用户提到了已知坑，填写。
```

---

## Step 6: 差异报告

完成填充后，输出审计报告：

```markdown
## 📊 项目审计报告

### 基本信息
- 项目名: XXX
- 技术栈: TypeScript + Express + PostgreSQL
- 代码规模: 45 个 .ts 文件，约 8,500 行
- 测试文件: 3 个（覆盖率偏低）

### 功能清单（7 个）
| 编号 | 功能 | 状态 | 文档 |
|------|------|------|------|
| FEAT-001 | 用户认证 | ✅ 完成 | features/001-user-auth.md |
| FEAT-002 | 数据 CRUD | ✅ 完成 | features/002-data-crud.md |
| FEAT-003 | 文件上传 | 🟡 部分 | features/003-file-upload.md |

### 差异/风险
| 项 | 说明 |
|----|------|
| ⚠️ 测试少 | 只有 3 个测试文件，核心业务逻辑未覆盖 |
| ⚠️ 无 CI | 没有 .github/workflows/ |
| ✅ 文档就绪 | docs/ 已填完，可进入 Phase 1 |

### 下一步建议
1. [用户确认的下一步]
```

---

## Step 7: 更新 PROGRESS.md

将 PROGRESS.md 状态设为「审计完成 → 就绪」，等待用户下达第一个开发指令。

---

## 审计原则

1. **宁可多问，不要猜。** 无法从代码确定的（设计意图、选型原因），标注「待确认」问用户
2. **先广度，后深度。** Step 1-3 快速覆盖，Step 4-5 逐步深入
3. **文档是快照，不是真理。** 审计报告标注时间戳，后续开发会持续更新
4. **差异不是错误，是指引。** docs/ 描述的理想 vs 代码的实际 → 差异就是下一步的工作量
