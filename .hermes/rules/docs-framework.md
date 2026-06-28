# docs/ 说明书框架规范

> **YuanForge 项目说明书体系 v2** — 全 Agent、全 Skill 适用的结构化知识库。
> `docs/` 是项目基石。任何 Agent 接手、任何 Skill 执行，都通过它读写协同。
> **不是 8 个文件，而是一个互相引用的知识网络。**

---

## 核心定位

```
docs/ = 项目的结构化知识网络

┌──────────────────────────────────────────────────────┐
│                     docs/                             │
│                                                       │
│  全局层（固定文件）                                     │
│  ├── INDEX.md          入口 + 快速导航                  │
│  ├── PROGRESS.md       进度中枢                        │
│  ├── ARCHITECTURE.md   架构全景                        │
│  ├── SETUP.md          环境指南                        │
│  ├── CONVENTIONS.md    规范约定                        │
│  ├── glossary.md       术语表                          │
│  └── pitfalls.md       踩坑库                          │
│                                                       │
│  生长层（按需创建）                                     │
│  ├── features/         每个需求一个文档                 │
│  │   ├── 001-xxx.md    ← 记录设计、关联Plan、改了什么    │
│  │   └── 002-xxx.md                                   │
│  ├── bugs/             每个 Bug 一个文档               │
│  │   ├── BUG-001-xxx.md ← 记录现象、根因、关联Feature   │
│  │   └── BUG-002-xxx.md                               │
│  └── decisions/        每个决策一个文档                 │
│      ├── ADR-001-xxx.md ← 记录为什么这样选              │
│      └── ADR-002-xxx.md                               │
│                                                       │
│  互相引用 → 顺着链接追溯到根                            │
└──────────────────────────────────────────────────────┘
```

**核心设计：**
- Bug → 链接到 Feature（知道是哪次改动引入的）
- Feature → 链接到 ADR（知道为什么这样设计）
- Feature → 链接到 Plan（知道改了哪些文件）
- pitfalls → 链接到 Bug（知道踩坑的具体案例）

---

## 目录结构

```
project/
├── docs/
│   ├── INDEX.md              ← 🔑 入口：项目概述 + 文档地图 + Agent 阅读顺序
│   ├── PROGRESS.md           ← ⚡ 进度中枢：汇总全部进行中的 Feature/Bug
│   ├── ARCHITECTURE.md       ← 🏗 架构全景
│   ├── SETUP.md              ← 🚀 环境指南
│   ├── CONVENTIONS.md        ← 📐 规范约定
│   ├── glossary.md           ← 📖 术语表（累积型，单文件）
│   ├── pitfalls.md           ← ⚠️  踩坑库（累积型，单文件）
│   │
│   ├── features/             ← 📦 需求/功能（每功能一文件）
│   │   ├── _template.md      ← 功能文档模板
│   │   ├── 001-xxx.md
│   │   └── 002-xxx.md
│   │
│   ├── bugs/                 ← 🐛 Bug 记录（每 Bug 一文件）
│   │   ├── _template.md      ← Bug 文档模板
│   │   ├── BUG-001-xxx.md
│   │   └── BUG-002-xxx.md
│   │
│   └── decisions/            ← 📋 决策日志（每决策一文件，方便引用）
│       ├── _template.md      ← ADR 模板
│       ├── ADR-001-xxx.md
│       └── ADR-002-xxx.md
└── .hermes/                  ← 框架引擎（不变）
```

---

## 互相引用规范

### 引用格式

```markdown
[FEAT-001 用户认证系统](../features/001-user-auth.md)
[BUG-003 登录超时](../bugs/BUG-003-login-timeout.md)
[ADR-002 选择 PostgreSQL](../decisions/ADR-002-choose-postgres.md)
```

### 引用关系图

```
Feature 文档中应链接：
  → 关联的 ADR（为什么这样设计）
  → 关联的 Plan（.hermes/plans/xxx.md）
  → 关联的 Bug（哪些 Bug 是这个功能引起的）
  → ARCHITECTURE 中的相关模块

Bug 文档中应链接：
  → 关联的 Feature（哪个功能引入的）
  → 关联的 ADR（根因对应的设计决策）
  → 修改的源码文件（src/xxx/yyy.py）
  → pitfalls 中对应的条目（如有）

ADR 文档中应链接：
  → 影响的 Feature（这个决策影响了哪些功能）
  → 替代的旧 ADR（如果是废弃决策）
```

### 编号规则

| 前缀 | 格式 | 示例 | 编号者 |
|------|------|------|--------|
| Feature | `NNN`（三位数字，按创建顺序） | `001`, `002` | Conductor |
| Bug | `BUG-NNN` | `BUG-001`, `BUG-002` | 发现者 |
| Decision | `ADR-NNN` | `ADR-001`, `ADR-002` | 决策者 |

**编号从 001 开始递增，永不重复。** 已删除/废弃的编号保留不回收。

---

## Agent × 文档 职责矩阵 v2

> **R = 必读，W = 负责写，M = 维护（读+写），- = 不涉及**

| 文档/目录 | Conductor | Architect | Coder | Reviewer | Tester | DevOps |
|-----------|-----------|-----------|-------|----------|--------|--------|
| INDEX.md | **M** | R | R | R | R | R |
| PROGRESS.md | **M** | R | R | R | R | R |
| ARCHITECTURE.md | R | **M** | R | R | R | R |
| SETUP.md | - | - | R | - | R | **M** |
| CONVENTIONS.md | W | W | R+W | R+W | W | W |
| glossary.md | W | W | W | W | W | W |
| pitfalls.md | W | W | **W** | W | **W** | W |
| **features/** | **M** | **M** | R | R | R | R |
| **bugs/** | W | W | **W** | W | **W** | W |
| **decisions/** | W | **M** | - | - | - | W |

**关键规则：**
- 每个新 Feature 启动时，Conductor 在 `features/` 创建对应文档
- Architect 在架构阶段填写 Feature 文档的设计部分
- Coder 在实现阶段补充「修改的文件」清单
- 发现 Bug 时，发现者立即在 `bugs/` 创建文档
- Bug 修复者补充根因、修复方案、关联 Feature
- 任何技术决策必须落 `decisions/` 独立文件

---

## Skill × 文档 读写规则 v2

| Skill | 读 | 写 |
|-------|-----|-----|
| project-bootstrap | - | 创建 docs/ 结构（含 features/bugs/decisions 目录 + _template.md） |
| vibecoding-workflow | PROGRESS, ARCHITECTURE, pitfalls, features/* | PROGRESS, features/新文档, decisions/新决策 |
| writing-plans | ARCHITECTURE, PROGRESS, pitfalls, features/相关 | PROGRESS, features/（设计部分） |
| test-driven-development | CONVENTIONS, PROGRESS, features/相关 | bugs/（测试发现的 Bug）, pitfalls |
| requesting-code-review | ARCHITECTURE, CONVENTIONS, features/相关 | bugs/（审查发现的问题） |
| systematic-debugging | pitfalls, ARCHITECTURE, bugs/*, features/* | bugs/（根因记录）, pitfalls（如新坑） |

---

## 生长层文件模板

### features/_template.md

```markdown
# FEAT-NNN: [功能名称]

> **状态:** [规划中 / 开发中 / 已完成 / 已废弃]
> **创建时间:** YYYY-MM-DD
> **完成时间:** YYYY-MM-DD（未完成则不填）
> **负责 Agent:** [Architect / Coder]

---

## 需求描述

[用户要什么？一句话说清]

---

## 设计思路

[整体怎么设计的？关键选择是什么？]

---

## 关联文档

| 关系 | 文档 |
|------|------|
| 📋 Plan | `.hermes/plans/[文件名].md` |
| 📋 决策 | [ADR-xxx 为什么](../decisions/ADR-xxx-xxx.md) |
| 🏗 架构 | [ARCHITECTURE.md 相关模块](../ARCHITECTURE.md#模块-a-名称) |
| 🐛 相关 Bug | [BUG-xxx](../bugs/BUG-xxx-xxx.md) |

---

## 修改的文件

| 文件 | 改动类型 | 说明 |
|------|---------|------|
| `src/xxx/yyy.py` | 新增 | 核心逻辑 |
| `tests/test_xxx.py` | 新增 | 单元测试 |

---

## 接口/数据模型

### API（如有）

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/xxx` | 获取列表 |
| POST | `/api/xxx` | 创建 |

### 数据库变更（如有）

| 表/字段 | 类型 | 说明 |
|---------|------|------|
| `users.email` | VARCHAR | 新增邮箱字段 |

---

## 完成检查

- [ ] Spec Review PASS
- [ ] Quality Review APPROVED
- [ ] 测试全部通过
- [ ] 已合并到 main
- [ ] 文档已更新

---

## 变更日志

| 日期 | 变更 | 操作者 |
|------|------|--------|
| YYYY-MM-DD | 创建文档 | Architect |
| YYYY-MM-DD | 实现完成 | Coder |
```

---

### bugs/_template.md

```markdown
# BUG-NNN: [Bug 标题]

> **严重程度:** 🔴 阻断 / 🟡 影响使用 / 🟢 轻微
> **状态:** [发现 / 分析中 / 修复中 / 已修复 / 已关闭]
> **发现时间:** YYYY-MM-DD
> **修复时间:** YYYY-MM-DD（未修复则不填）
> **发现者:** [Agent 角色]

---

## 现象

[发生了什么？用户/测试看到的错误是什么？]

```
# 错误日志或复现步骤
[粘贴]
```

---

## 根因

[为什么发生？深层原因是什么？]

---

## 关联文档

| 关系 | 文档 |
|------|------|
| 📦 引入此 Bug 的 Feature | [FEAT-xxx](../features/xxx-xxx.md) |
| 📋 相关决策 | [ADR-xxx](../decisions/ADR-xxx-xxx.md) |
| ⚠️ 相关踩坑 | [pitfalls.md § PIT-xxx](../pitfalls.md) |
| 📝 修复 Commit | `commit hash` |

---

## 修复

[怎么修的？改了哪些文件？]

| 文件 | 改动 | 说明 |
|------|------|------|
| `src/xxx/yyy.py` | 修改 | [说明] |

---

## 教训

[下次怎么避免？有没有可以提炼的规律？]

---

## 归档判断

| 问题 | 回答 |
|------|------|
| 会重复出现？ | [是/否] |
| 可提炼为 Skill？ | [是/否] |
| → 处理 | [留在 bugs/ / 提炼 Skill / 加入 pitfalls] |
```

---

### decisions/_template.md

```markdown
# ADR-NNN: [决策标题]

> **状态:** [提议 / 已采纳 / 已废弃 / 已被替代]
> **日期:** YYYY-MM-DD
> **决策者:** [角色]

---

## 背景

[为什么要做这个决策？上下文是什么？]

---

## 决策

[我们决定做什么？]

---

## 备选方案

| 方案 | 优点 | 缺点 |
|------|------|------|
| [方案 A] | [优点] | [缺点] |
| [方案 B]（✅ 选中） | [优点] | [缺点] |
| [方案 C] | [优点] | [缺点] |

---

## 后果

- **正面:** [带来什么好处？]
- **负面:** [引入什么风险/限制？]
- **迁移路径:** [如果要改，怎么改？]

---

## 关联

| 关系 | 文档 |
|------|------|
| 影响的 Feature | [FEAT-xxx](../features/xxx-xxx.md) |
| 替代的决策 | [ADR-xxx](ADR-xxx-xxx.md)（如废弃此决策） |
| 相关 Bug | [BUG-xxx](../bugs/BUG-xxx-xxx.md) |
```

---

## 全局层文档格式

> 全局层文档（INDEX.md、PROGRESS.md、ARCHITECTURE.md、SETUP.md、CONVENTIONS.md、glossary.md、pitfalls.md）保持单文件，格式与 v1 基本一致，改动如下：

### INDEX.md 增加子目录导航

文档地图表扩展：

```markdown
## 📚 文档地图

### 全局文档（必读）
| 文档 | 何时读 | 优先级 |
|------|--------|--------|
| PROGRESS.md | 每次必读 | 🔴 必读 |
| ARCHITECTURE.md | 首次接手、架构变更时 | 🔴 必读 |
| pitfalls.md | 每次必读 | 🔴 必读 |
| SETUP.md | 首次接手、跑项目时 | 🟡 按需 |
| CONVENTIONS.md | 写代码前 | 🟡 按需 |

### 生长文档（按编号查）
| 目录 | 内容 | 格式 |
|------|------|------|
| [features/](./features/) | [N] 个功能文档 | `001-xxx.md` |
| [bugs/](./bugs/) | [N] 个 Bug 记录 | `BUG-001-xxx.md` |
| [decisions/](./decisions/) | [N] 个决策记录 | `ADR-001-xxx.md` |
| [glossary.md](./glossary.md) | [N] 个术语 | 术语表 |
```

### PROGRESS.md 增加链接汇总

```markdown
## 当前状态

| 项 | 值 |
|----|-----|
| **当前 Phase** | 2-执行 |
| **当前 Feature** | [FEAT-003 支付模块](./features/003-payment.md) |
| **当前 Task** | Task 2.1: 支付回调 |
| **当前 Plan** | `.hermes/plans/2026-06-28_payment.md` |

## 功能清单

| 编号 | 功能 | 状态 | 文档 |
|------|------|------|------|
| FEAT-001 | 用户认证 | ✅ 已完成 | [001-user-auth.md](./features/001-user-auth.md) |
| FEAT-002 | 数据列表 | ✅ 已完成 | [002-data-list.md](./features/002-data-list.md) |
| FEAT-003 | 支付模块 | 🔨 开发中 | [003-payment.md](./features/003-payment.md) |

## 活跃 Bug

| 编号 | Bug | 严重程度 | 关联 Feature | 文档 |
|------|-----|---------|-------------|------|
| BUG-001 | 登录超时 | 🟡 | [FEAT-001](./features/001-user-auth.md) | [BUG-001](./bugs/BUG-001-login-timeout.md) |
```

### ARCHITECTURE.md 增加功能引用

模块划分表增加「关联 Feature」列：

```markdown
### 模块 A: 用户系统
- **职责:** 注册、登录、权限管理
- **文件路径:** `src/auth/`
- **关联 Feature:** [FEAT-001 用户认证](./features/001-user-auth.md)
- **关联决策:** [ADR-001 JWT vs Session](./decisions/ADR-001-jwt-auth.md)
```

---

## docs/ 生命周期 v2

```
项目初始化（project-bootstrap）
  │  创建 docs/ 目录 + 3 个子目录
  │  创建全部全局文档（模板）
  │  创建 _template.md × 3
  │
Phase 1: 架构
  │  Architect 写 ARCHITECTURE.md
  │  Architect 创建 features/001-xxx.md（设计部分）
  │  Architect 创建 decisions/ADR-001-xxx.md
  │  DevOps 写 SETUP.md
  │  Conductor 更新 PROGRESS.md + INDEX.md
  │
Phase 2: 执行
  │  每个 Task 完成后：
  │    Coder 补充 features/ 中的「修改的文件」表
  │    Conductor 更新 PROGRESS
  │  遇 Bug：
  │    发现者创建 bugs/BUG-NNN.md（记录现象）
  │    修复者补充根因 + 修复 + 链接到 Feature
  │  新决策：
  │    决策者创建 decisions/ADR-NNN.md
  │
Phase 3: 收尾
  │  验证所有 features/ 文档「修改的文件」表完整
  │  确认所有 bugs/ 已关闭或标注状态
  │  DevOps 确认 SETUP.md 准确
  │
Phase 4: 回顾
  │  遍历 bugs/ 中的「归档判断」
  │  提炼 → Skill / pitfalls
  │  评估「同一 Feature 反复出 Bug」→ 可能需要架构复盘
```

---

## 文档创建时机速查表

> Agent 需要判断什么情况创建什么文档

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

## 与其他规则的关系

| 规则 | 关系 |
|------|------|
| iron-rules.md | 铁律 Ⅵ「文档即代码」— 本文档是其具体实现 |
| plan-format.md | Plan 存 `.hermes/plans/`，features/ 文档链接到对应 Plan |
| project-memory skill | YuanForge 自身的 `.hermes/docs/` 记忆管理（与本文档区分） |
| project-bootstrap skill | 入口：引用本文档创建初始 docs/ 结构 |

---

> *docs/ 不是附属品，是项目脊梁。Feature 描述做了什么，Bug 追溯到为什么错，Decision 解释为什么选。Agent 换了一百个，文档在，项目就在。*
