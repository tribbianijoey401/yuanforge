# SESSION — 会话文档规格书

> 管辖 docs/ 下每个会话文件夹（`YYYYMMDD-描述/`）内的所有文档。
> 一个会话 = 一次需求/一个 Plan 的执行周期。

---

## 会话文件夹结构

```
docs/YYYYMMDD-描述/
├── PLAN.md           ← 本会话 Plan（Architect 产出，冻结）
├── TASK_BOARD.md     ← 多 Agent 共享任务板（Conductor 创建，所有 Agent 读写）
├── SESSION_LOG.md    ← 本会话日志
├── FEATURE.md        ← 功能文档
├── ADR-NNN-xxx.md    ← 决策记录（可选，做决策时创建）
└── BUG-NNN-xxx.md    ← Bug 记录（可选，发现 Bug 时创建）
```

### 文件夹命名规则
`YYYYMMDD-简短描述`。如 `20260707-增加认证`。

---

## 1. PLAN.md

### 目的
本会话的 Plan。Architect 产出，Conductor 按此派发。

### 格式
遵循 `.yuan/rules/plan-format.md`。含 Dispatch Table。

### 生命周期
| 阶段 | 操作 | 执行者 |
|------|------|--------|
| Phase 1 | 创建 | Architect |
| 用户确认后 | 锁定，不再修改 | — |

---

## 2. SESSION_LOG.md

### 目的
记录本会话的关键产出和决策。回答「这次会话干了什么」。

### 格式

```markdown
# 会话日志

> 会话: [YYYYMMDD-描述]
> 开始: YYYY-MM-DD HH:MM
> 结束: YYYY-MM-DD HH:MM
> 模式: [严格/快速]
> 接续自: [上一个会话文件夹名，首个会话填 无]

## 任务完成情况

| 任务 | 状态 | 产出 |
|------|------|------|
| T01 | ✅测试通过 | src/auth/login.py |
| T02 | ✅完成 | src/models/user.py |
| T03 | 🔨进行中 | — |
| T04 | ⏳等待 | — |

> 任务 ID 来自 PLAN.md 的 Dispatch Table，跨会话保持稳定。

## 完成
- [Task/功能 简述]

## 决策
- [做了什么重要决策？关联 ADR]

## 踩坑
- [遇到什么坑？关联 pitfalls]

## 产出物
- 文件: [路径]
- Commit: [hash]
```

### 生命周期
| 阶段 | 操作 | 执行者 |
|------|------|--------|
| 会话开始时 | 创建，填开始时间 + 接续自 | Conductor |
| 会话结束时 | 填任务完成情况表 + 完成/决策/踩坑/产出物 | Conductor |

---

## 3. FEATURE.md

### 目的
记录本会话实现的功能。描述需求、设计、修改文件。

### 格式

```markdown
# FEATURE: [功能名称]

> 会话: [YYYYMMDD-描述]
> 状态: [完成]
> 负责角色: [Architect/Coder]

## 需求描述
[一句话]

## 设计思路
[怎么设计的]

## 修改的文件
| 文件 | 改动 | 说明 |

## API/接口（如有）
| 方法 | 路径 | 说明 |

## 关联
| 关系 | 文档 |
|------|------|
| Plan | [PLAN.md](./PLAN.md) |
| ADR | [ADR-xxx](./ADR-xxx.md) |
| Bug | [BUG-xxx](./BUG-xxx.md) |
```

### 生命周期
| 阶段 | 操作 | 执行者 |
|------|------|--------|
| Phase 1 | 创建，填需求+设计 | Architect |
| Phase 2 完成 | 补充修改文件+API | Coder |

---

## 4. ADR-NNN-xxx.md

### 目的
记录技术决策：选了什么、为什么、备选方案。

### 格式

```markdown
# ADR-NNN: [决策标题]

> 会话: [YYYYMMDD-描述]
> 状态: [采纳]
> 日期: YYYY-MM-DD

## 背景
[为什么要做这个决策？]

## 决策
[选了哪个方案？]

## 备选方案
| 方案 | 优点 | 缺点 |
|------|------|------|
| A | | |
| B（✅） | | |

## 后果
- 正面: [好处]
- 负面: [风险]
```

### 生命周期
| 阶段 | 操作 | 执行者 |
|------|------|--------|
| 做技术选型时 | 创建 | 决策者 |
| 决策废弃时 | 追加废弃说明，不改原文件 | 决策者 |

---

## 5. BUG-NNN-xxx.md

### 目的
记录 Bug：现象、根因、修复、教训。

### 格式

```markdown
# BUG-NNN: [标题]

> 会话: [YYYYMMDD-描述]
> 严重程度: 🔴阻断 / 🟡影响 / 🟢轻微
> 状态: [已修复]
> 发现者: [角色]

## 现象

## 根因

## 修复

## 教训

## 归档判断
| 问题 | 回答 |
| 会重复出现？ | [是/否] |
| → 处理 | [留在 bugs / 加入 pitfalls / 提炼 Skill] |
```

### 生命周期
| 阶段 | 操作 | 执行者 |
|------|------|--------|
| 发现 Bug | 创建，填现象 | 发现者 |
| 修复后 | 补根因+修复+教训 | 修复者 |
| Phase 4 | 归档判断 | Conductor |

---

## 会话文件夹完整生命周期

```
[新需求/新会话开始]
    ↓ Conductor
1. 创建文件夹 docs/YYYYMMDD-描述/
2. 创建 PLAN.md（Architect 填）
3. 创建 SESSION_LOG.md（Conductor 填开始时间）
    ↓ Phase 1
4. Architect 填 PLAN.md + FEATURE.md（需求+设计）
5. 做决策时 → 创建 ADR-NNN.md
    ↓ G1 ✓ → Phase 2
6. Coder 执行，遇 Bug → 创建 BUG-NNN.md
    ↓ Phase 2 完成
7. Coder 更新 FEATURE.md（修改文件+API）
8. Conductor 更新 SESSION_LOG.md（完成/决策/踩坑）
    ↓ Phase 4
9. Conductor 遍历 BUG → 归档判断 → PROGRESS 更新
10. 会话完成，PROGRESS 移至历史会话
```
