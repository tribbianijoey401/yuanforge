# 📚 YuanForge 项目说明书

> **YuanForge（元锻造）** — 可复制的 Vibecoding 项目母体。
> 基于 Harness 工程理念：驾驭 Agent、编排 Skill、铁律驱动。

---

## 🚀 快速导航

| 你想… | 读这个 |
|--------|--------|
| 了解项目当前状态和下一步 | → [PROGRESS.md](./PROGRESS.md) |
| 搭建开发环境、跑起来 | → [SETUP.md](./SETUP.md) |
| 了解系统架构和模块划分 | → [ARCHITECTURE.md](./ARCHITECTURE.md) |
| 写代码前了解规范 | → [CONVENTIONS.md](./CONVENTIONS.md) |
| 查某个术语的意思 | → [glossary.md](./glossary.md) |
| 避免踩已知的坑 | → [pitfalls.md](./pitfalls.md) |
| 看历史技术决策 | → [decisions/](./decisions/) |
| 看某个需求的完整记录 | → [features/](./features/) |
| 查某个 Bug 的来龙去脉 | → [bugs/](./bugs/) |

---

## 📚 文档地图

### 全局文档（必读）

| 文档 | 何时读 | 优先级 |
|------|--------|--------|
| [PROGRESS.md](./PROGRESS.md) | 每次必读 | 🔴 必读 |
| [ARCHITECTURE.md](./ARCHITECTURE.md) | 首次接手、架构变更时 | 🔴 必读 |
| [pitfalls.md](./pitfalls.md) | 每次必读 | 🔴 必读 |
| [SETUP.md](./SETUP.md) | 首次接手、跑项目时 | 🟡 按需 |
| [CONVENTIONS.md](./CONVENTIONS.md) | 写代码前 | 🟡 按需 |

### 生长文档（按编号查）

| 目录 | 内容 | 格式 |
|------|------|------|
| [features/](./features/) | [N] 个功能文档 | `001-xxx.md` |
| [bugs/](./bugs/) | [N] 个 Bug 记录 | `BUG-001-xxx.md` |
| [decisions/](./decisions/) | [N] 个决策记录 | `ADR-001-xxx.md` |
| [glossary.md](./glossary.md) | [N] 个术语 | 术语表 |

---

## 👷 Agent 阅读顺序

新 Agent 接手项目时，按以下顺序加载文档：

```
1. INDEX.md (本文件)        ← 知道有哪些文档、在哪
2. PROGRESS.md              ← 知道项目当前在哪、下一步做什么
3. ARCHITECTURE.md          ← 知道系统怎么设计的
4. pitfalls.md              ← 知道有哪些坑不能踩
5. SETUP.md                 ← 知道怎么把项目跑起来
6. CONVENTIONS.md           ← 知道代码规范
```

---

## 🔗 框架层文档

框架内核（平台无关）位于 `.yuan/`：

| 路径 | 内容 |
|------|------|
| `.yuan/rules/iron-rules.md` | 九条铁律 |
| `.yuan/rules/plan-format.md` | Plan 工程化格式 |
| `.yuan/rules/docs-framework.md` | 本说明书体系规范 |
| `.yuan/agents/` | 5 个 Agent 角色定义 |
| `.yuan/skills/` | 9 个 Skill 定义 |
| `.yuan/platforms/` | 平台适配器 |

---

## 📋 文档创建时机速查

| 情况 | 创建什么 | 谁来 |
|------|---------|------|
| 新功能开始设计 | `features/NNN-xxx.md` | Architect |
| 选了一个技术方案 | `decisions/ADR-NNN-xxx.md` | 决策者 |
| 测试跑挂了 | `bugs/BUG-NNN-xxx.md` | 发现者 |
| 用户报了一个 Bug | `bugs/BUG-NNN-xxx.md` | Conductor |
| 代码审查发现问题 | `bugs/BUG-NNN-xxx.md` | Reviewer |
| 引入新术语 | 追加 `glossary.md` 一行 | 全体 |
| 踩了坑/环境限制 | 追加 `pitfalls.md` 一条 | 全体 |
| Feature 完成 | 更新 features/ 文档 → ✅ | Coder |
| Bug 修完 | 更新 bugs/ 文档 → 已修复 | 修复者 |

---

> *驾驭 Agent，而非被 Agent 驾驭。*
