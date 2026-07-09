# docs/ 说明书体系规范

> **YuanForge 项目说明书 v3** — 以会话文件夹组织的结构化知识库。
> 所有 doc 格式的权威定义在 `.yuan/docs/` 的 9 份规格书中。

---

## 核心定位

```
docs/ = 项目的结构化知识网络

全局层（固定文件，项目级别）
├── INDEX.md          入口 + 文档地图
├── PROGRESS.md       进度中枢
├── ARCHITECTURE.md   架构全景
├── SETUP.md          环境指南
├── CONVENTIONS.md    规范约定
├── glossary.md       术语表
└── pitfalls.md       踩坑库

会话层（按时间组织，一个会话一个文件夹）
└── YYYYMMDD-描述/
    ├── PLAN.md       本会话 Plan
    ├── SESSION_LOG.md 会话日志
    ├── FEATURE.md    功能文档
    ├── ADR-NNN.md    决策记录（可选）
    └── BUG-NNN.md    Bug 记录（可选）
```

---

## 规格书索引

所有 doc 的格式、生命周期、创建规则定义在 `.yuan/docs/`：

| 规格书 | 管辖 |
|--------|------|
| [GLOBAL.md](../docs/GLOBAL.md) | INDEX / SETUP / CONVENTIONS / glossary / pitfalls |
| [PROGRESS.md](../docs/PROGRESS.md) | PROGRESS.md |
| [ARCHITECTURE.md](../docs/ARCHITECTURE.md) | ARCHITECTURE.md |
| [TASK_BOARD.md](../docs/TASK_BOARD.md) | TASK_BOARD.md — 多 Agent 共享任务板 |
| [SESSION.md](../docs/SESSION.md) | 会话文件夹（PLAN/LOG/FEATURE/ADR/BUG） |

---

## Agent × 文档 职责矩阵

| 文档 | Conductor | Architect | Coder | Reviewer | Tester | DevOps |
|------|-----------|-----------|-------|----------|--------|--------|
| INDEX.md | M | R | R | R | R | R |
| PROGRESS.md | **M** | R | R | R | R | R |
| ARCHITECTURE.md | R | **M** | R | R | R | R |
| SETUP.md | - | - | R | - | R | **M** |
| CONVENTIONS.md | W | W | R+W | R+W | W | W |
| glossary.md | W | W | W | W | W | W |
| pitfalls.md | W | W | W | W | W | W |
| 会话文件夹 | **M** | M | W | W | W | W |

---

## 会话文件夹生命周期

```
新会话开始
  ↓ Conductor
1. 创建 docs/YYYYMMDD-描述/
2. 创建 PLAN.md（Architect 填）
3. 创建 SESSION_LOG.md（Conductor 记开始）
  ↓
Phase 1-3 执行中
  → 做决策 → 创建 ADR-NNN.md
  → 发现 Bug → 创建 BUG-NNN.md
  → 完成功能 → 更新 FEATURE.md
  ↓
Phase 4 回顾
  → Conductor 补全 SESSION_LOG.md
  → 遍历 BUG → 归档判断
  → PROGRESS.md 移至历史会话
```

---

## 与其他规则的关系

| 规则 | 关系 |
|------|------|
| iron-rules.md | 铁律 Ⅵ「文档即代码」— 本文档是其具体实现 |
| plan-format.md | Plan 存会话文件夹的 PLAN.md |
| project-bootstrap | 读 `.yuan/docs/` 规格书 → 生成 docs/ |
| project-audit | 读 `.yuan/docs/` 规格书 → 审计现有项目 |
