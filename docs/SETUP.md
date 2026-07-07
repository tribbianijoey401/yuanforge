# 🚀 环境指南 (SETUP.md)

> **本文件回答："怎么把项目跑起来？"**
> DevOps Agent 负责维护此文件。首次接手项目时必读。

---

## 项目信息

| 项 | 值 |
|----|-----|
| **项目名称** | YuanForge（元锻造） |
| **项目类型** | Vibecoding 元框架（无代码项目） |
| **运行时依赖** | Hermes Agent |

---

## 前置依赖

| 依赖 | 版本要求 | 安装方式 | 用途 |
|------|---------|---------|------|
| Hermes Agent | latest | `pip install hermes-agent` | 运行时引擎 |
| Git | 2.x+ | 系统自带 | 版本控制 |

---

## 快速开始

### 1. 克隆项目

```bash
git clone git@github.com:tribbianijoey401/yuanforge.git
cd yuanforge
```

### 2. 启动新项目（从 YuanForge 复制）

```bash
cp -r yuanforge my-awesome-project
cd my-awesome-project
git init && git add -A && git commit -m "init: from YuanForge"
```

### 3. 开始 Vibecoding

在 Hermes Agent 中说：

```
开始开发一个 TODO API
```

Yuan 会自动：
1. Architect 分析需求 → 设计架构 → 产出 Plan
2. 你确认 Plan
3. Conductor 解析 Dispatch Table → 并行派发 Agent
4. Coder → Reviewer → Tester → DevOps 逐层流转
5. 交付可运行代码

---

## 环境变量

| 变量 | 必填 | 说明 | 示例 |
|------|------|------|------|
| — | — | YuanForge 本身无需环境变量 | — |

具体项目（从 YuanForge 复制的项目）按需添加。

---

## 验证安装

```bash
# 确认 Hermes Agent 可用
hermes --version
```

---

## 常见问题

### Q: 从哪里开始？
A: 阅读 [INDEX.md](./INDEX.md) → [PROGRESS.md](./PROGRESS.md)，然后对 Hermes Agent 说你的需求。

### Q: 需要装什么编程语言的运行时？
A: 不需要预先安装。YuanForge 会根据项目需求自动选择技术栈，Agent 会自己安装依赖。

---

> *最后更新: 2026-07-07*
