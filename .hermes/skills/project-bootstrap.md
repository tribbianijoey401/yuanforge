---
name: project-bootstrap
description: "从 YuanForge 元框架启动新项目"
version: 1.0.0
---

# 项目启动 Skill

> 定义如何使用 YuanForge 元框架初始化一个新项目。

---

## 触发条件

用户说以下任何一句时激活：
- "创建一个新项目"
- "用 YuanForge 启动 XX 项目"
- "初始化 XX"

---

## 流程

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

### Step 3: 填写项目元信息

创建/更新项目元信息文件：

```bash
echo "# My New Project" > README.md
echo "项目描述..." >> README.md
```

### Step 4: 创建初始架构文档

```bash
# 初始化 ARCHITECTURE.md
echo "# 架构决策记录" > .hermes/docs/ARCHITECTURE.md
echo "" >> .hermes/docs/ARCHITECTURE.md
echo "## 项目概述" >> .hermes/docs/ARCHITECTURE.md
echo "TODO: 填写项目概述" >> .hermes/docs/ARCHITECTURE.md

# 初始化 DECISIONS.md
echo "# 技术决策日志 (ADR)" > .hermes/docs/DECISIONS.md
echo "" >> .hermes/docs/DECISIONS.md
echo "## 2026-XX-XX: 项目初始化" >> .hermes/docs/DECISIONS.md
echo "- 基于 YuanForge 元框架" >> .hermes/docs/DECISIONS.md
echo "- 技术栈：待定" >> .hermes/docs/DECISIONS.md

# 初始化 GLOSSARY.md
echo "# 项目术语表" > .hermes/docs/GLOSSARY.md
```

### Step 5: 首次 Commit

```bash
git add -A
git commit -m "init: project bootstrap from YuanForge"
```

### Step 6: 准备开发

现在你可以对 Hermes Agent 说：
> "开始开发 [你的第一个功能]"

---

## 文件清单

元框架复制后的项目结构：

```
my-new-project/
├── README.md
├── .gitignore
├── .hermes/
│   ├── agents/          # Agent 角色（就位）
│   ├── rules/           # 铁律（就位）
│   ├── skills/          # 核心 Skill（就位）
│   ├── docs/            # 项目记忆（待填写）
│   └── plans/           # 实现计划（空）
├── templates/           # 项目模板
└── src/                 # 源码（待创建）
```
