---
name: project-bootstrap
description: >
  创建新项目或嫁接现有项目时加载。触发：用户说「创建项目」「初始化」
  「用 YuanForge 启动」「新建项目」、从一个 idea 开始，或「嫁接 YuanForge」
  「给现有项目接入 Yuan」。两种模式：
  ① 全新模式 — 复制元框架、创建 docs/ 说明书体系（含 features/bugs/decisions
  子目录 + 模板）、初始化 Git。
  ② 嫁接模式 — 将 .yuan/ contracts/ protocols/ templates/ AGENTS.md
  复制到现有项目，然后触发 project-audit 审计现有代码并填充 docs/。
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

> 根据 `.yuan/rules/docs-framework.md` v2 规范创建项目结构化知识库。

```bash
# 创建目录结构
mkdir -p docs/features docs/bugs docs/decisions

# ============================
# 全局文档
# ============================

# INDEX.md — 入口
cat > docs/INDEX.md << 'EOF'
# [项目名] 项目说明书

> **职责:** 项目入口，Agent 首次接手的第一份阅读材料
> **维护者:** Conductor
> **更新时间:** YYYY-MM-DD HH:MM
> **前置阅读:** 无

---

## ⚡ 30 秒速览

- **项目是什么:** [一句话]
- **技术栈:** [待定]
- **当前状态:** 初始化
- **当前 Feature:** 无
- **下一步:** Architect 分析需求 → 产出 Plan

---

## 📚 文档地图

### 全局文档（每次必读）
| 文档 | 何时读 | 优先级 |
|------|--------|--------|
| [PROGRESS.md](./PROGRESS.md) | 每次必读 | 🔴 必读 |
| [ARCHITECTURE.md](./ARCHITECTURE.md) | 首次接手、架构变更时 | 🔴 必读 |
| [pitfalls.md](./pitfalls.md) | 每次必读 | 🔴 必读 |
| [SETUP.md](./SETUP.md) | 首次接手、跑项目时 | 🟡 按需 |
| [CONVENTIONS.md](./CONVENTIONS.md) | 写代码前 | 🟡 按需 |

### 生长文档（按需查找）
| 目录 | 内容 | 编号格式 |
|------|------|---------|
| [features/](./features/) | 功能文档 | `NNN-xxx.md` |
| [bugs/](./bugs/) | Bug 记录 | `BUG-NNN-xxx.md` |
| [decisions/](./decisions/) | 决策记录 | `ADR-NNN-xxx.md` |
| [glossary.md](./glossary.md) | 术语表 | - |

---

## 🤖 Agent 强制阅读顺序

1. 本文件 (INDEX.md)
2. PROGRESS.md — 当前状态
3. ARCHITECTURE.md — 系统全貌
4. pitfalls.md — 已知陷阱
5. 按需求查找 features/ bugs/ decisions/
EOF

# PROGRESS.md — 进度中枢
cat > docs/PROGRESS.md << 'EOF'
# 项目进度

> **职责:** 回答「项目到哪了？下一步做什么？」
> **维护者:** Conductor
> **更新时间:** YYYY-MM-DD HH:MM
> **前置阅读:** INDEX.md

---

## 当前状态

| 项 | 值 |
|----|-----|
| **当前 Phase** | 无 |
| **当前 Stage** | 无 |
| **当前 Feature** | 无 |
| **当前 Task** | 无 |
| **当前 Plan** | 无 |
| **模式** | 严格模式 |

---

## 功能清单

暂无

---

## 活跃 Bug

暂无

---

## 阻塞项

暂无

---

## 下一步

1. Architect 分析需求
2. 产出 Implementation Plan
3. 用户确认 Plan 后进入 Phase 2

---

## 项目元信息

| 项 | 值 |
|----|-----|
| **项目名称** | [项目名] |
| **技术栈** | [待定] |
| **项目状态** | 初始化 |
| **创建时间** | YYYY-MM-DD |
| **仓库地址** | [Git URL] |
EOF

# ARCHITECTURE.md — 架构全景
cat > docs/ARCHITECTURE.md << 'EOF'
# 架构文档

> **职责:** 系统的设计蓝图
> **维护者:** Architect
> **更新时间:** YYYY-MM-DD HH:MM
> **前置阅读:** INDEX.md

---

## 项目概述

TODO: 填写项目描述

---

## 技术栈

| 层 | 技术 | 版本 | 选型原因 | 关联决策 |
|----|------|------|---------|---------|
| 语言 | [待定] | - | - | - |
| 框架 | [待定] | - | - | - |
| 数据库 | [待定] | - | - | - |

---

## 模块划分

TODO: Architect 填写。每个模块须标注关联 Feature。

---

## 数据流

TODO: Architect 填写
EOF

# SETUP.md — 环境指南
cat > docs/SETUP.md << 'EOF'
# 环境搭建指南

> **职责:** 在新环境中把项目跑起来
> **维护者:** DevOps
> **更新时间:** YYYY-MM-DD HH:MM
> **前置阅读:** INDEX.md

---

## 前置要求

TODO: DevOps 填写

---

## 快速开始

TODO: DevOps 填写
EOF

# CONVENTIONS.md — 规范约定
cat > docs/CONVENTIONS.md << 'EOF'
# 项目规范

> **职责:** 编码、命名、Git 约定
> **维护者:** 全体
> **更新时间:** YYYY-MM-DD HH:MM
> **前置阅读:** INDEX.md

---

## 命名规范

TODO: 全体约定

---

## 代码风格

TODO: 全体约定

---

## Git 规范

- **Commit 格式:** Conventional Commits (`feat:`, `fix:`, `refactor:`, `test:`, `docs:`, `chore:`)
- **一个 Commit 一件事**

---

## 文档规范

- 所有 md 文件使用 docs-framework 规定的元信息头部
- 架构决策 → `decisions/ADR-NNN-xxx.md`
- 新术语 → `glossary.md`
- 踩坑 → `pitfalls.md`
- 务必填写文档间的互相引用链接
EOF

# glossary.md — 术语表
cat > docs/glossary.md << 'EOF'
# 项目术语表

> **职责:** 项目特有概念的定义辞典
> **维护者:** 全体
> **更新时间:** YYYY-MM-DD HH:MM
> **前置阅读:** INDEX.md

---

| 术语 | 英文 | 定义 | 相关文档 |
|------|------|------|---------|
| YuanForge | YuanForge | 元锻造 Vibecoding 元框架 | - |
EOF

# pitfalls.md — 踩坑库
cat > docs/pitfalls.md << 'EOF'
# 踩坑记录

> **职责:** 已知陷阱。Agent 必读，避免重复踩坑。
> **维护者:** 全体
> **更新时间:** YYYY-MM-DD HH:MM
> **前置阅读:** INDEX.md

---

## PIT-001: [示例] 模板 — 删除此条后开始使用

- **日期:** YYYY-MM-DD
- **类型:** [后端 / 前端 / DB / 部署 / CI / 流程 / 环境]
- **严重程度:** 🔴 阻断 / 🟡 绕路 / 🟢 提醒

### 现象

[发生了什么？]

### 根因

[为什么？]

### 修复

[怎么修的？]

### 教训

[下次怎么做？]

### 归档判断

| 问题 | 回答 |
|------|------|
| 会重复出现？ | [是/否] |
| 可提炼为 Skill？ | [是/否] |
| → 处理 | [留在 pitfalls / 提炼 Skill / 反馈 YuanForge] |
EOF

# ============================
# 生长层模板
# ============================

# features/_template.md
cat > docs/features/_template.md << 'EOF'
# FEAT-NNN: [功能名称]

> **状态:** [规划中 / 开发中 / 已完成 / 已废弃]
> **创建时间:** YYYY-MM-DD
> **完成时间:** YYYY-MM-DD（未完成不填）
> **负责 Agent:** [Architect / Coder]

---

## 需求描述

[用户要什么？]

---

## 设计思路

[怎么设计的？]

---

## 关联文档

| 关系 | 文档 |
|------|------|
| 📋 Plan | `.yuan/plans/[文件名].md` |
| 📋 决策 | [ADR-xxx](../decisions/ADR-xxx-xxx.md) |
| 🏗 架构 | [ARCHITECTURE.md](../ARCHITECTURE.md#模块-x) |
| 🐛 相关 Bug | [BUG-xxx](../bugs/BUG-xxx-xxx.md) |

---

## 修改的文件

| 文件 | 改动 | 说明 |
|------|------|------|
| TODO | - | - |

---

## 完成检查

- [ ] Spec Review PASS
- [ ] Quality Review APPROVED
- [ ] 测试通过
- [ ] 已合并 main

---

## 变更日志

| 日期 | 变更 | 操作者 |
|------|------|--------|
| YYYY-MM-DD | 创建 | Architect |
EOF

# bugs/_template.md
cat > docs/bugs/_template.md << 'EOF'
# BUG-NNN: [Bug 标题]

> **严重程度:** 🔴 阻断 / 🟡 影响使用 / 🟢 轻微
> **状态:** [发现 / 分析中 / 修复中 / 已修复 / 已关闭]
> **发现时间:** YYYY-MM-DD
> **修复时间:** YYYY-MM-DD（未修复不填）
> **发现者:** [Agent 角色]

---

## 现象

[发生了什么？]

---

## 根因

[深层原因？]

---

## 关联文档

| 关系 | 文档 |
|------|------|
| 📦 引入的 Feature | [FEAT-xxx](../features/xxx-xxx.md) |
| 📋 相关决策 | [ADR-xxx](../decisions/ADR-xxx-xxx.md) |
| ⚠️ 相关踩坑 | [pitfalls.md § PIT-xxx](../pitfalls.md) |
| 📝 修复 Commit | `commit hash` |

---

## 修复

| 文件 | 改动 | 说明 |
|------|------|------|
| TODO | - | - |

---

## 教训

[下次怎么避免？]

---

## 归档判断

| 问题 | 回答 |
|------|------|
| 会重复出现？ | [是/否] |
| 可提炼为 Skill？ | [是/否] |
| → 处理 | [留在 bugs/ / 提炼 Skill / 加入 pitfalls] |
EOF

# decisions/_template.md
cat > docs/decisions/_template.md << 'EOF'
# ADR-NNN: [决策标题]

> **状态:** [提议 / 已采纳 / 已废弃 / 已被替代]
> **日期:** YYYY-MM-DD
> **决策者:** [角色]

---

## 背景

[为什么要做这个决策？]

---

## 决策

[我们决定做什么？]

---

## 备选方案

| 方案 | 优点 | 缺点 |
|------|------|------|
| [方案 A] | [优点] | [缺点] |
| [方案 B]（✅ 选中） | [优点] | [缺点] |

---

## 后果

- **正面:** [好处]
- **负面:** [风险/限制]
- **迁移路径:** [如果要改，怎么改？]

---

## 关联

| 关系 | 文档 |
|------|------|
| 影响的 Feature | [FEAT-xxx](../features/xxx-xxx.md) |
| 替代的决策 | [ADR-xxx](ADR-xxx-xxx.md)（如废弃） |
| 相关 Bug | [BUG-xxx](../bugs/BUG-xxx-xxx.md) |
EOF
```

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
├── docs/                       # 📚 项目说明书（按 docs-framework v2 规范）
│   ├── INDEX.md                # 入口 + 文档地图
│   ├── PROGRESS.md             # 进度中枢
│   ├── ARCHITECTURE.md         # 架构全景
│   ├── SETUP.md                # 环境指南
│   ├── CONVENTIONS.md          # 规范约定
│   ├── glossary.md             # 术语表
│   ├── pitfalls.md             # 踩坑库
│   ├── features/               # 需求/功能（每功能一文档）
│   │   └── _template.md
│   ├── bugs/                   # Bug 记录（每 Bug 一文档）
│   │   └── _template.md
│   └── decisions/              # 决策日志（每决策一文档）
│       └── _template.md
├── .yuan/                    # 框架引擎（不变）
│   ├── agents/
│   ├── rules/
│   ├── skills/
│   ├── docs/                   # YuanForge 自身记忆
│   └── plans/
└── src/                        # 源码（待创建）
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
mkdir -p docs/{features,bugs,decisions}
cp yuanforge/.yuan/templates/docs/*.md            docs/
cp yuanforge/.yuan/templates/docs/features/_template.md   docs/features/
cp yuanforge/.yuan/templates/docs/bugs/_template.md       docs/bugs/
cp yuanforge/.yuan/templates/docs/decisions/_template.md  docs/decisions/
```

此时 docs/ 都是空模板，内容待 Step G3 填充。

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
