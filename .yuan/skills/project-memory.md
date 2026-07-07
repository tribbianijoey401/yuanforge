---
name: project-memory
description: >
  维护 YuanForge 的 .yuan/docs/ 项目记忆体系时加载。触发：Phase 4 回顾、
  需要归档 PITFALLS、写 SESSION_LOG、维护框架级记忆。负责 6 份 Memory 文件
  的生命周期管理。注意：这是框架层记忆，不是项目 docs/（项目层规范见
  .yuan/docs/）。
version: 2.0.0
---

# 项目记忆管理

> **Yuan 的项目大脑。** 上下文会压缩，会话会结束——但项目记忆永存。
> 任何 Agent 首次加载项目时，读完 Memory 就知道一切。

---

## ⚠️ 两层 docs 体系区分

| 目录 | 用途 | 谁维护 | 何时读取 |
|------|------|--------|---------|
| **`.yuan/docs/`** | YuanForge **框架自身**的记忆 | YuanForge 维护者 | 维护框架时 |
| **`docs/`** | **具体项目**的说明书 | 项目 Agent 军团 | 开发项目时 |

**本文档描述 `.yuan/docs/`（框架层）。**
项目层的 `docs/` 规范见 [`.yuan/rules/docs-framework.md`](../rules/docs-framework.md)。

---

## 核心原则

1. **Agent 首次加载 = 完整继任** — 读完 Memory 后能无缝继续开发
2. **上下文压缩友好** — 每份文档都紧凑可扫描，不依赖大段文本
3. **进度驱动** — PROGRESS.md 是王，任何 Agent 先读它
4. **坑即知识** — PITFALLS.md 把踩坑经验结构化，是学习回环的输入

---

## Memory 文件体系

| 文件 | 优先级 | 读取时机 | 用途 |
|------|--------|---------|------|
| **PROGRESS.md** | 🔴 必读 | 每次启动 | 当前在哪？下一步做什么？ |
| **ARCHITECTURE.md** | 🔴 必读 | 首次 + 架构变更 | 系统怎么设计的？ |
| **PITFALLS.md** | 🔴 必读 | 每次启动 | 踩过什么坑？别重复 |
| **DECISIONS.md** | 🟡 按需 | 技术选型时 | 为什么选这些技术？ |
| **GLOSSARY.md** | 🟡 按需 | 遇到陌生术语 | 这个词什么意思？ |
| **SESSION_LOG.md** | 🟢 深挖 | 需要了解历史 | 上次干了什么？ |

---

## Agent 加载流程

```
[Agent 启动]
    │
    ├── 1. read_file("docs/PROGRESS.md")
    │      → 获悉：当前 Phase/Stage/Task、阻塞项、下一步
    │
    ├── 2. read_file("docs/ARCHITECTURE.md")
    │      → 了解系统全貌
    │
    ├── 3. read_file("docs/pitfalls.md")
    │      → 避开已知陷阱
    │
    ├── 4. 如果当前有 Plan：
    │      read_file("当前会话文件夹中的 PLAN.md")
    │      → 读取当前 Task 的详细规格
    │
    └── 5. （可选）read_file(".yuan/docs/")
           → 了解最近做了什么
```

---

## 各文件规范

### PROGRESS.md — 进度中枢

**何时更新：每完成一个 Task、每切换 Stage、每解决一个阻塞项。**

```markdown
## 当前状态
| 当前 Phase | 2-执行 |
| 当前 Stage | Stage 2: 核心功能 |
| 当前 Task  | Task 2.2: 注册端点 |
| 当前 Plan  | 当前会话文件夹中的 PLAN.md 示例 |

## 已完成
- [x] Task 1.1: 初始化项目
- [x] Task 2.1: 密码哈希工具

## 下一步
1. 完成 Task 2.2 注册端点
2. G2 审查 Task 2.2
3. 进入 Task 2.3 登录端点
```

**关键规则：**
- 每次更新顶部「当前状态」— 这是 Agent 第一个看到的信息
- 完成后立即打勾
- 阻塞项要写明原因

---

### PITFALLS.md — 踩坑知识库

**何时更新：每次踩坑后立即记录（不要等 Phase 4）。**

每条坑的格式：
```markdown
### PIT-NNN: [一句话标题]

**日期:** YYYY-MM-DD
**类型:** [本项目 / 前端 / 后端 / DB / 部署 / 流程]
**严重程度:** 🔴 / 🟡 / 🟢

**现象:** 发生了什么？
**原因:** 为什么？
**修复:** 怎么解决的？
**教训:** 下次怎么办？

**归档判断:**
- 其他项目也会遇到？ [是/否]
- 有明确操作步骤？ [是/否]
- → [留在此文件 / 提炼为 Skill / 反馈到 Yuan]
```

**关键规则：**
- 边做边记，不要等到 Phase 4 再回忆
- 每条必须填写「归档判断」— 这是学习回环的核心
- Agent 启动时必须读 PITFALLS.md — 记了不看等于白记

---

### SESSION_LOG.md — 会话轨迹

**何时更新：每次会话结束时。**

```markdown
### Session N: YYYY-MM-DD — [主题]

- **完成:** [Task 列表]
- **决策:** [关联 DECISIONS.md]
- **踩坑:** [关联 PITFALLS.md 编号]
- **下一步:** [下次从哪继续]
- **Commit:** abc1234
```

**关键规则：**
- 保持 3-5 行，不写流水账
- 关键决策必须指向 DECISIONS.md
- 新会话追加在末尾

---

### ARCHITECTURE.md — 架构中枢

**何时更新：架构变更时。**

内容：项目概述、模块划分、数据流、关键设计模式、外部依赖、部署架构。

---

### DECISIONS.md — 决策日志 (ADR)

**何时更新：做技术选型时。**

格式：ADR（背景 → 决策 → 备选方案 → 后果）。

---

### GLOSSARY.md — 术语表

**何时更新：引入新概念时。**

---

## 与回环学习的整合

```
Phase 1-3: 开发中
  │  踩坑 → 立即记入 PITFALLS.md
  │  Agent 每次启动 → 必读 PITFALLS.md（避开已知坑）
  │
Phase 4: 回顾
  │  遍历 PITFALLS.md 中所有「归档判断」
  │  ├── 本项目特有 → 留在此文件
  │  ├── 领域通用 → skill_manage(action='create/patch')
  │  └── 框架通用 → 反馈到 Yuan 铁律/Skill
  │
  ▼
  下次新项目 = 继承所有提炼后的 Skill
```

---

## 与平台 Memory/Skill 工具的分工

> 不同 Agent 平台有各自的持久化工具（如 Hermes 的 `memory`/`skill`、系统级配置等）。
> 本体系只管理**项目级**知识，平台级偏好留给平台自己的工具。

| 存什么 | 放哪 |
|--------|------|
| 项目进度、架构、决策、术语、踩坑 | → `docs/*.md（规格见 .yuan/docs/）`（本体系） |
| 用户偏好（简洁回复、语言等） | → 平台自己的 memory/配置工具 |
| 环境配置（OS、路径、工具版本） | → 平台自己的 memory/配置工具 |
| 可复用的操作流程 | → 平台自己的 skill 工具 |
