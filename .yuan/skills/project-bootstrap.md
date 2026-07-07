---
name: project-bootstrap
description: >
  创建新项目或嫁接现有项目时加载。触发：用户说「创建项目」「初始化」
  「用 YuanForge 启动」「新建项目」、从一个 idea 开始，或「嫁接 YuanForge」
  「给现有项目接入 Yuan」。两种模式：
  ① 全新模式 — 运行 yuanforge-init 初始化项目结构。
  ② 嫁接模式 — 将框架文件复制到现有项目，然后触发 project-audit。
  读写：docs/ 全部初始创建（新模式）或审计填充（嫁接模式）。
version: 2.0.0
---

# 项目启动 Skill

> 定义如何使用 YuanForge 元框架初始化一个新项目。

---

## 触发条件

用户说以下任何一句时激活：
- "创建一个新项目" / "用 YuanForge 启动 XX 项目" / "初始化 XX"
- "嫁接 YuanForge" / "给现有项目接入 Yuan" / "把 YuanForge 加到我的项目"
- "这是半路项目" / "接手现有项目"

激活后判断模式：
- 用户无现有代码 → **模式一：全新项目**（Step 1-4）
- 用户有现有项目 → **模式二：嫁接项目**（Step G1-G3）

---

## 模式一：全新项目

### Step 1: 复制元框架

```bash
cp -r yuanforge my-new-project
cd my-new-project
```

### Step 2: 初始化 Git

```bash
rm -rf .git          # 删除元框架的 git 历史
git init
git branch -m main
git add -A
git commit -m "init: project bootstrap from YuanForge"
```

### Step 3: 创建 docs/ 说明书体系

> 根据 `.yuan/docs/` 规格书（GLOBAL/PROGRESS/ARCHITECTURE/SESSION）创建项目结构化知识库。

```bash
# 创建目录结构
mkdir -p docs

# ============================
# 全局文档（7 个）
# ============================

# 从 .yuan/docs/GLOBAL.md 规格书提取 INDEX 模板
cat > docs/INDEX.md << 'EOF'
# [项目名] 项目说明书

> [一句话描述]

## ⚡ 30 秒速览
- **项目是什么:** [一句话]
- **技术栈:** [待定]
- **当前状态:** 初始化
- **当前会话:** 暂无
- **下一步:** Architect 分析需求 → 产出 Plan

## 🚀 快速导航
| 你想… | 读这里 |
|--------|--------|
| 了解当前状态 | → [PROGRESS.md](./PROGRESS.md) |
| 搭建环境 | → [SETUP.md](./SETUP.md) |
| 了解架构 | → [ARCHITECTURE.md](./ARCHITECTURE.md) |
| 写代码前 | → [CONVENTIONS.md](./CONVENTIONS.md) |
| 查术语 | → [glossary.md](./glossary.md) |
| 避坑 | → [pitfalls.md](./pitfalls.md) |

## 📚 文档地图
### 全局文档
| 文档 | 何时读 | 优先级 |
|------|--------|--------|
| PROGRESS.md | 每次必读 | 🔴 |
| ARCHITECTURE.md | 首次接手 | 🔴 |
| pitfalls.md | 每次必读 | 🔴 |
| SETUP.md | 首次接手 | 🟡 |
| CONVENTIONS.md | 写代码前 | 🟡 |

## 🤖 Agent 阅读顺序
1. 本文件 → 2. PROGRESS.md → 3. ARCHITECTURE.md → 4. pitfalls.md
EOF

# TASK_BOARD.md（空模板，Conductor 在 Phase 1 后填充）
cat > docs/TASK_BOARD.md << 'EOF'
# 任务板

> 会话: 待定
> 创建: YYYY-MM-DD HH:MM（Conductor）

## 任务状态
| ID | 任务 | 角色 | 依赖 | 状态 | 产出 |
|----|------|------|------|------|------|

## 上下文传递
| 从 | 到 | 传递内容 |
|----|-----|---------|

## 返工记录
| 任务 | 次数 | 原因 | 审查人 |
|------|------|------|--------|

## 阻塞
| 时间 | 任务 | 原因 |
|------|------|------|
EOF

# PROGRESS.md
cat > docs/PROGRESS.md << 'EOF'
# 项目进度
> 最后更新: YYYY-MM-DD

## 当前状态
| 项 | 值 |
|----|-----|
| **当前 Phase** | 初始化 |
| **当前会话** | 暂无 |
| **模式** | 严格模式 |

## 功能清单
暂无

## 活跃 Bug
暂无

## 阻塞项
暂无

## 历史会话
暂无

## 下一步
1. Architect 分析需求 → 产出 Plan

## 项目元信息
| 项 | 值 |
|----|-----|
| **项目名称** | [项目名] |
| **技术栈** | [待定] |
| **创建时间** | YYYY-MM-DD |
EOF

# SETUP.md
cat > docs/SETUP.md << 'EOF'
# 环境指南

## 前置依赖
| 依赖 | 版本 | 安装方式 |
|------|------|---------|

## 快速开始
```bash
git clone [仓库地址]
[安装命令]
[启动命令]
```

## 验证
```bash
[测试命令]
```
EOF

# CONVENTIONS.md
cat > docs/CONVENTIONS.md << 'EOF'
# 项目规范

## 命名规范
| 类型 | 规范 | 示例 |

## Git 规范
- Commit: `type: 简短描述`
- 一个 Commit 一件事

## 安全
- ❌ 禁止硬编码密钥
- ✅ 使用环境变量
EOF

# glossary.md
cat > docs/glossary.md << 'EOF'
# 术语表

## 业务术语
| 术语 | 英文 | 定义 |

## 缩写
| 缩写 | 全称 | 说明 |
EOF

# pitfalls.md
cat > docs/pitfalls.md << 'EOF'
# 踩坑记录

暂无记录
EOF

# ARCHITECTURE.md（空模板，Architect 在 Phase 1 填写）
cat > docs/ARCHITECTURE.md << 'EOF'
# 架构文档

> Architect 在 Phase 1 填写。

## 项目概述
[TODO]

## 技术栈
| 层 | 技术 | 选型原因 |
|----|------|---------|

## 模块划分
| 模块 | 职责 | 关键文件 |
|------|------|---------|
EOF
```

> 完整的格式定义见 `.yuan/docs/` 4 份规格书。Agent 创建 docs 时应读取对应规格书确保格式正确。

### Step 4: 首次 Commit

```bash
git add -A
git commit -m "init: project bootstrap from YuanForge"
```

### Step 5: 准备开发

现在你可以对 Agent 说：
> "开始开发 [你的第一个功能]"

Agent 将自动加载 `docs/INDEX.md` → `docs/PROGRESS.md` 启动工作流。

---

## 文件清单

元框架复制后的项目结构：

```
my-new-project/
├── README.md
├── .gitignore
├── AGENTS.md                    # 通用入口
├── docs/                        # 📚 项目说明书
│   ├── INDEX.md                 # 入口 + 文档地图
│   ├── PROGRESS.md              # 进度中枢
│   ├── ARCHITECTURE.md          # 架构全景
│   ├── SETUP.md                 # 环境指南
│   ├── CONVENTIONS.md           # 规范约定
│   ├── glossary.md              # 术语表
│   ├── pitfalls.md              # 踩坑库
│   └── [YYYYMMDD-描述]/          # 会话文件夹（按需创建）
│       ├── PLAN.md
│       ├── TASK_BOARD.md
│       ├── SESSION_LOG.md
│       ├── FEATURE.md
│       ├── ADR-NNN.md
│       └── BUG-NNN.md
├── .yuan/                       # 框架内核
│   ├── agents/
│   ├── rules/
│   ├── skills/
│   ├── docs/                    # doc 规格书
│   ├── platforms/
│   └── plans/
└── src/                         # 源码
```

---

## 模式二：嫁接现有项目

> 当你已经有一个写了一半的项目，想把 YuanForge 框架接进去。

### Step G1: 复制框架内核

```bash
# 在你的项目根目录执行（从 yuanforge 复制）
cp -r yuanforge/.yuan        ./
cp -r yuanforge/contracts     ./
cp -r yuanforge/protocols     ./
cp -r yuanforge/templates     ./
cp    yuanforge/AGENTS.md     ./
```

> 如果项目已有 .gitignore，合并 yuanforge 的 .gitignore 内容，不要覆盖。

### Step G2: 初始化 docs/ 说明书（空模板）

```bash
mkdir -p docs
# 按 .yuan/docs/ 规格书创建全局文档（同 Step 3）
```

此时 docs/ 只有 7 个全局文档（INDEX/PROGRESS/ARCHITECTURE/SETUP/CONVENTIONS/glossary/pitfalls），内容待 Step G3 填充。

### Step G3: 审计现有代码 → 填充说明书

**加载 `project-audit` skill，执行完整的 7 步审计流程：**

```
1. 覆盖扫描 → 识别技术栈、构建工具、Git 历史
2. 架构分析 → 模块划分、数据流、入口点
3. 功能盘点 → 列出所有已完成/进行中的功能
4. 决策回溯 → 从依赖和注释反推技术决策
5. 填充说明书 → 把审计结果写入 docs/
6. 差异报告 → docs/ 描述 vs 实际代码的差异
7. 更新 PROGRESS → 状态设为「就绪」
```

审计完成后，Agent 会输出一份审计报告，列出：
- 已发现的所有功能
- 已记录的技术决策
- docs/ 与实际代码的差异
- 下一步建议

### Step G4: 首次 Commit

```bash
git add -A
git commit -m "init: graft YuanForge framework + project audit"
```

### Step G5: 开始开发

审计完成后，对 Agent 说：

> "按照 YuanForge 框架，开发 [下一个功能]"

Agent 会读取 docs/PROGRESS.md 了解当前进度，然后按 vibecoding-workflow 执行。

---

## 两种模式对比

| 维度 | 模式一：全新 | 模式二：嫁接 |
|------|------------|------------|
| 适用场景 | 从 idea 开始 | 已有半路项目 |
| 框架内核 | 从 yuanforge 复制 | 从 yuanforge 复制 |
| docs/ 怎么填 | 空模板，等 Phase 1 | project-audit 审计填充 |
| src/ | 空的，等开发 | 已有代码，不动 |
| 触发 Skill | 直接创建 | 创建 + project-audit |
