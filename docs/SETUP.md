# 🚀 环境指南 (SETUP.md)

> **本文件回答："怎么把项目跑起来？"**
> Doc Engineer 负责维护此文件。首次接手项目时必读。

---

## 项目信息

| 项 | 值 |
|----|-----|
| **项目名称** | YuanForge（元锻造） |
| **项目类型** | Vibecoding 元框架（无代码项目） |
| **运行时依赖** | 任意 Agent 平台（Hermes / Cursor / Claude Code / Codex CLI ...） |

---

## 前置依赖

| 依赖 | 说明 |
|------|------|
| 任意 Agent 平台 | Hermes / Cursor / Claude Code / Codex CLI / GitHub Copilot ... |
| Git | 版本控制 |

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

YuanForge 不绑定平台。选你习惯的 Agent 工具：

| 平台 | 操作 |
|------|------|
| **Hermes Agent** | 直接说「开发一个 TODO API」 |
| **Cursor** | 打开项目，Agent 自动读取 AGENTS.md |
| **Claude Code** | `claude` 启动，自动加载 AGENTS.md |
| **任何平台** | 参考 `.yuan/platforms/manual.md` |

无论哪个平台，Yuan 的工作流都一样：
1. Architect 分析需求 → 设计架构 → 产出 Plan
2. 你确认 Plan
3. Conductor 解析 Dispatch Table → 并行派发 Agent
4. Dev → 4 Reviewers → Tester → Doc Engineer 逐层流转
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
# 确认 Git 可用
git --version

# 确认你的 Agent 平台可用（以下任一）
hermes --version        # Hermes Agent
cursor --version        # Cursor
claude --version        # Claude Code
codex --version         # Codex CLI
```

---

## 常见问题

### Q: 从哪里开始？
A: 阅读 [INDEX.md](./INDEX.md) → [PROGRESS.md](./PROGRESS.md)，然后对你的 Agent 说你的需求。

### Q: 需要装什么编程语言的运行时？
A: 不需要预先安装。YuanForge 会根据项目需求自动选择技术栈，Agent 会自己安装依赖。

---

> *最后更新: 2026-07-07*
