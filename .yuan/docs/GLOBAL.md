# GLOBAL — 全局文档规格书

> 管辖 docs/ 下的全局文档：INDEX.md / SETUP.md / CONVENTIONS.md / glossary.md / pitfalls.md / knowledge/

---

## 1. INDEX.md

### 目的
项目入口。Agent 首次接手时第一份阅读材料，回答「项目是什么、有哪些文档、按什么顺序读」。

### 格式

```markdown
# 📚 [项目名] 项目说明书

> [一句话描述]

## ⚡ 30 秒速览
- **项目是什么:** [一句话]
- **技术栈:** [语言+框架+数据库]
- **当前状态:** [初始化/开发中/已交付]
- **当前会话:** docs/[YYYYMMDD-描述]/
- **下一步:** [一句话]

## 🚀 快速导航
| 你想… | 读这个 |
|--------|--------|
| 了解当前状态 | → [PROGRESS.md](./PROGRESS.md) |
| 搭建环境 | → [SETUP.md](./SETUP.md) |
| 了解架构 | → [ARCHITECTURE.md](./ARCHITECTURE.md) |
| 写代码前 | → [CONVENTIONS.md](./CONVENTIONS.md) |
| 查术语 | → [glossary.md](./glossary.md) |
| 避坑 | → [pitfalls.md](./pitfalls.md) |
| 看历史会话 | → 下方「历史会话」列表 |

## 📚 文档地图
### 全局文档
| 文档 | 何时读 | 优先级 |
|------|--------|--------|
| [PROGRESS.md](./PROGRESS.md) | 每次必读 | 🔴 |
| [ARCHITECTURE.md](./ARCHITECTURE.md) | 首次接手 | 🔴 |
| [pitfalls.md](./pitfalls.md) | 每次必读 | 🔴 |
| [SETUP.md](./SETUP.md) | 首次接手 | 🟡 |
| [CONVENTIONS.md](./CONVENTIONS.md) | 写代码前 | 🟡 |

### 会话文件夹（按时间）
| [YYYYMMDD-描述] | 状态 | 路径 |

## 🤖 Agent 阅读顺序
1. 本文件 → 2. PROGRESS.md → 3. ARCHITECTURE.md → 4. pitfalls.md → 5. 当前会话文件夹
```

### 生命周期
| 阶段 | 操作 | 执行者 |
|------|------|--------|
| 项目初始化 | 从本模板创建，填项目名 | project-bootstrap |
| 每个会话结束 | 更新「当前会话」和「历史会话」表 | Conductor |

---

## 2. SETUP.md

### 目的
在新环境中把项目跑起来。

### 格式

```markdown
# 环境指南

## 项目信息
| 项 | 值 |
|----|-----|
| **项目名称** | [名称] |

## 前置依赖
| 依赖 | 版本 | 安装方式 |
|------|------|---------|

## 快速开始
```bash
git clone [仓库地址]
cd [项目名]
[安装命令]
[启动命令]
```

## 环境变量
| 变量 | 必填 | 说明 |

## 验证
```bash
[测试命令]
```
```

### 生命周期
| 阶段 | 操作 | 执行者 |
|------|------|--------|
| Phase 1 | 创建 | DevOps |
| 依赖变更时 | 更新 | DevOps |

---

## 3. CONVENTIONS.md

### 目的
写代码的规范约定。

### 格式

```markdown
# 项目规范

## 命名规范
| 类型 | 规范 | 示例 |

## 目录约定
```

## Git 规范
- Commit 格式: `type: 简短描述`
- 一个 Commit 一件事

## 安全
- ❌ 禁止硬编码密钥
- ✅ 使用环境变量
```

### 生命周期
| 阶段 | 操作 | 执行者 |
|------|------|--------|
| 项目初始化 | 创建 | project-bootstrap |
| 规范变更 | 更新 | 全体 |

---

## 4. glossary.md

### 目的
项目特有概念的定义辞典。

### 格式

```markdown
# 术语表

## 业务术语
| 术语 | 英文 | 定义 |

## 缩写
| 缩写 | 全称 | 说明 |
```

### 生命周期
| 阶段 | 操作 | 执行者 |
|------|------|--------|
| 引入新术语时 | 追加一行 | 全体 |
| Phase 4 | 检查是否有遗漏 | Conductor |

---

## 5. pitfalls.md

### 目的
已知陷阱库，Agent 必读避免重复踩坑。

### 格式

```markdown
# 踩坑记录

## PIT-NNN: [标题]
- **日期:** YYYY-MM-DD
- **类型:** [后端/前端/DB/部署/流程/环境]
- **严重程度:** 🔴阻断 / 🟡绕路 / 🟢提醒

**现象:**
**原因:**
**修复:**
**教训:**

**归档判断:**
| 问题 | 回答 |
| 会重复出现？ | [是/否] |
| → 处理 | [留在 pitfalls / 提炼 Skill / 反馈 YuanForge] |
```

### 生命周期
| 阶段 | 操作 | 执行者 |
|------|------|--------|
| 踩坑时 | 追加 | 全体 |
| Phase 4 | 遍历归档判断 → 提炼 Skill | Conductor |

---

## 6. knowledge/ — 知识对象目录

### 目的
保存从 Workspace 蒸馏出的长期知识对象。每个文件是一个对象实例，通过 YAML frontmatter 声明身份。

### 目录结构

```
docs/knowledge/
├── features/         ← Feature 对象（FEAT-NNN.md）
├── decisions/        ← Decision 对象（ADR-NNN.md）
├── pitfalls/         ← Pitfall 对象（PIT-NNN.md）
└── modules/          ← Module 对象（MOD-NNN.md）
```

> **对象 Schema 定义**见 `docs/object-model.yaml`。每个文件的 frontmatter 必须符合对应 `object_type` 的字段要求。

### 格式规则

**所有 knowledge/ 文件的共同要求**：

1. 必须以 YAML frontmatter 开头（`---` 包围）
2. frontmatter 必须包含 `id`、`object_type`、`lifecycle`、`owner`、`status`、`summary`、`confidence`
3. `object_type` 决定正文格式（feature=需求+API+文件，decision=背景+决策+后果，etc.）
4. `verified_commit` 建议填写，用于过期检测
5. 正文是精简后的长期版本——蒸馏时从 Workspace 的 FEATURE.md / ADR.md 精简而来

### 各子目录格式

#### features/

**命名**：`FEAT-{简短名}.md`。如 `FEAT-AUTH.md`。

```markdown
---
id: FEAT-xxx
object_type: feature
lifecycle: knowledge
owner: architect
status: verified
summary: "一句话描述此功能"
depends: [ADR-003]
verified_commit: abc123
confidence: verified
---

# Feature: [功能名称]

## 需求描述
[从 FEATURE.md 提炼，2-3 句话]

## 设计思路
[关键设计决策 + ADR 引用]

## API 端点
| 方法 | 路径 | 说明 |
|------|------|------|
| POST | /xxx | xxx |

## 关键文件
- src/xxx/handler.py
- tests/xxx/test.py
```

#### decisions/

**命名**：`ADR-NNN.md`（保留原始 ADR 编号）。

```markdown
---
id: ADR-NNN
object_type: decision
lifecycle: knowledge
owner: architect
status: accepted
date: YYYY-MM-DD
summary: "一句话描述此决策"
depends: []
supersedes: ADR-xxx  (可选)
confidence: verified
---

# ADR-NNN: [决策标题]

## 背景
[原 ADR 背景]

## 决策
[原 ADR 决策 + 理由]

## 备选方案
| 方案 | 优点 | 缺点 |
|------|------|------|
| A | | |
| B（✅） | | |

## 后果
- 正面: [...]
- 负面: [...]
```

#### pitfalls/

**命名**：`PIT-NNN.md`（递增编号）。

```markdown
---
id: PIT-NNN
object_type: pitfall
lifecycle: knowledge
owner: [发现者角色]
status: active
severity: blocker|warning|info
type: backend|frontend|db|deploy|process|env
summary: "一句话描述此陷阱"
verified_commit: abc123
confidence: verified
---

# PIT-NNN: [陷阱标题]

## 现象
[从 BUG-NNN.md 提炼]

## 根因
[简短一句话]

## 修复
[简短一句话]

## 教训
[Agent 应该怎么做来避免？]
```

#### modules/

**命名**：`MOD-{简短名}.md`。如 `MOD-AUTH.md`。

```markdown
---
id: MOD-xxx
object_type: module
lifecycle: knowledge
owner: architect
status: active
summary: "一句话描述此模块"
depends: [MOD-xxx, ADR-xxx]
language: python
framework: FastAPI
directory: src/auth/
features: [FEAT-AUTH, FEAT-LOGIN]
confidence: verified
---

# Module: [模块名称]

## 职责
[此模块负责什么]

## 关键文件
- src/auth/handler.py — API 处理器
- src/auth/service.py — 业务逻辑

## 关联 Feature
- FEAT-AUTH — 用户认证
- FEAT-LOGIN — 登录 UI
```

### 生命周期

| 阶段 | 操作 | 执行者 |
|------|------|--------|
| Workspace Close | 蒸馏产生新的 knowledge 文件 | Conductor |
| 知识更新时 | 通过 Proposal 修改（未来 Phase） | Agent |
| HEAD != verified_commit | 标记 confidence=stale | Agent / Conductor |
| Phase 4 | 检查 knowledge/ 一致性 | Conductor |

### 与 INDEX.md 的关系

INDEX.md 的「文档地图」应包含 knowledge/ 导航：

```markdown
| 你想… | 读这个 |
|--------|--------|
| 了解所有功能 | → knowledge/features/ |
| 了解所有决策 | → knowledge/decisions/ |
| 避坑 | → knowledge/pitfalls/（Agent 必读） |
| 了解模块结构 | → knowledge/modules/ |
```
