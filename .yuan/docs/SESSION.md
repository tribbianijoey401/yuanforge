# SESSION — 会话文档规格书

> 管辖 docs/ 下每个会话文件夹（`YYYYMMDD-描述/`）内的所有文档。
> 一个会话 = 一次需求/一个 Plan 的执行周期。

---

## 会话文件夹结构

```
docs/YYYYMMDD-描述/
├── PLAN.md           ← 本会话 Plan（Architect 产出，冻结）
├── TASK_BOARD.md     ← 多 Agent 共享任务板（Conductor 创建，所有 Agent 读写）
├── SESSION_LOG.md    ← 本会话日志（Human 视图）
├── agents/           ← Agent 状态快照（Machine 视图，崩溃恢复用）🆕
│   └── <role>.yaml
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

| 任务 | 状态 | 简述 | 决策 | 产出 | Commit |
|------|------|------|------|------|--------|
| T01 | ✅测试通过 | JWT 认证 API | bcrypt（团队熟悉，见 ADR-001） | src/auth/login.py, tests/test_auth.py | a1b2c3d |
| T02 | ✅完成 | User 数据模型 | email 作唯一标识 | src/models/user.py | d4e5f6g |
| T03 | 🔨进行中 | 登录 UI 组件 | — | — | — |
| T04 | ⏳等待 | 前端路由守卫 | — | — | — |

> 任务 ID 来自 PLAN.md 的 Dispatch Table，跨会话保持稳定。
>
> **简述** = 一句话描述做了什么（如"JWT 认证 API 含 token 刷新"），让新 Agent 秒懂。
> **决策** = 关键技术选择 + 理由 + ADR 编号（无决策则填 `—`）。
> **产出** = 文件路径列表（逗号分隔），新 Agent 直接 `read_file`。
> **Commit** = 对应的 git commit hash（未提交则填 `—`），方便 `git show` 回溯。

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
| 会话进行中 | **每次任务终态时立即更新**「任务完成情况」表（简述/决策/产出/Commit） | Conductor |
| 会话结束时 | 汇总「完成」「决策」「踩坑」「产出物」段 | Conductor |

> **关键：任务完成情况表是渐进式更新的。** 不能等到会话结束才填——万一崩溃，新 Conductor 需要它作为恢复锚点。

---

## 3. FEATURE.md

### 目的
记录本会话实现的功能。描述需求、设计、修改文件。

### 格式

```markdown
# FEATURE: [功能名称]

> 会话: [YYYYMMDD-描述]
> 状态: [完成]
> 负责角色: [Architect/Frontend/Backend Dev]

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
| Phase 2 完成 | 补充修改文件+API | Frontend/Backend Dev |

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
6. Frontend/Backend Dev 执行，遇 Bug → 创建 BUG-NNN.md
    ↓ Phase 2 进行中
7. Conductor 渐进更新 SESSION_LOG「任务完成情况」表（每次任务终态时）
    ↓ Phase 2 完成
8. Frontend/Backend Dev 更新 FEATURE.md（修改文件+API）
9. Conductor 更新 SESSION_LOG.md（完成/决策/踩坑）
    ↓ Phase 4
10. Conductor 遍历 BUG → 归档判断 → PROGRESS 更新
11. Conductor 知识蒸馏（Workspace Close）:
    a. FEATURE.md → knowledge/features/FEAT-NNN.md（对象实例，含 frontmatter）
    b. ADR-NNN.md → knowledge/decisions/ADR-NNN.md（完整保留 + frontmatter）
    c. BUG-NNN.md → 归档判断:
       └─ 会重复出现 → knowledge/pitfalls/PIT-NNN.md（对象实例）
       └─ 一次性 → 留在 Workspace 中归档
    d. 未完成任务 → workspace/backlog.md 更新
12. Conductor 归档: 移动会话文件夹 → archive/YYYYMMDD-描述/
```

### 蒸馏后的目录效果

```
蒸馏前（Workspace 活跃时）:
  docs/
    YYYYMMDD-描述/          ← 唯一的 Workspace（通常 1 个）
      FEATURE.md            原始格式
      ADR-NNN.md
      BUG-NNN.md
  
蒸馏后（Workspace Close 后）:
  docs/
    knowledge/               ← 长期知识（蒸馏产物，逐次增长）
      features/FEAT-NNN.md  对象实例，含完整 frontmatter
      decisions/ADR-NNN.md
      pitfalls/PIT-NNN.md
    archive/                 ← 已关闭 Workspace 快照
      YYYYMMDD-描述/
        FEATURE.md          原始格式（保留作为追溯）
        ...
```

---

## Workspace Close — 知识蒸馏

### 目的

Workspace 的价值不在 Workspace 本身，在它产出的**事实**。蒸馏就是把长期有价值的知识从 Runtime 中提取出来，沉淀到 Knowledge 层，再丢弃运行垃圾。

```
蒸馏 ≠ 归档

归档 = 把整个文件夹冻起来 → "以后可能会需要" → 永远增长
蒸馏 = 提取有价值的事实 → 丢弃运行垃圾 → Knowledge 线性增长，Archive 不膨胀
```

### 蒸馏规则

| 源文件 | 蒸馏去向 | 动作 | 执行者 |
|--------|---------|------|--------|
| FEATURE.md | `knowledge/features/FEAT-NNN.md` | **重新创建为对象实例**：填完整 frontmatter（id/object_type/owner/status/summary/depends/verified_commit/confidence），正文精简为需求描述+设计思路+API+修改文件 | Conductor |
| ADR-NNN.md | `knowledge/decisions/ADR-NNN.md` | **完整复制 + 加 frontmatter**：保留背景/决策/备选方案/后果，加对象元数据 | Conductor |
| BUG-NNN.md | **归档判断** → `knowledge/pitfalls/PIT-NNN.md` 或留在 archive | 会重复出现 → 蒸馏为 Pitfall 对象（填 severity/type/cause/fix）。一次性 → 不蒸馏，留在 Workspace 归档中 | Conductor |
| PLAN.md | `workspace/backlog.md` | 未完成任务的 Task ID 追加到 backlog | Conductor |
| TASK_BOARD.md | — | **不蒸馏**。Runtime 状态，随 Workspace 归档 | — |
| SESSION_LOG.md | — | **不蒸馏**。Human 日志，随 Workspace 归档 | — |

### FEATURE.md → knowledge/features/ 转换示例

**蒸馏前**（Workspace 中的 FEATURE.md）：
```markdown
# FEATURE: 用户认证系统
> 会话: 20260709-用户认证
> 状态: 完成
> 负责角色: Architect

## 需求描述
实现 JWT 认证，含 token 刷新

## 设计思路
bcrypt 哈希 + JWT access/refresh token 双 token 模式
...
```

**蒸馏后**（knowledge/features/FEAT-AUTH.md）：
```yaml
---
id: FEAT-AUTH
object_type: feature
lifecycle: knowledge
owner: architect
status: verified
summary: "JWT-based authentication with refresh token rotation"
depends: [ADR-003]
verified_commit: a1b2c3d
confidence: verified
updated_by: conductor
updated_at: "2026-07-09T17:00:00Z"
acceptance_criteria:
  - "用户可用 email+password 注册并获取 JWT"
  - "Token 过期后可用 refresh token 刷新"
api_endpoints:
  - POST /auth/register
  - POST /auth/login
  - POST /auth/refresh
files:
  - src/auth/handler.py
  - src/auth/service.py
  - tests/auth/test_login.py
session: "20260709-用户认证系统"
---
# Feature: 用户认证系统

## 需求描述
实现 JWT 认证，含 token 刷新。

## 设计思路
bcrypt 哈希 + JWT access/refresh token 双 token 模式。
详见 ADR-003。

## API 端点
| 方法 | 路径 | 说明 |
|------|------|------|
| POST | /auth/register | 注册 |
| POST | /auth/login | 登录 |
| POST | /auth/refresh | 刷新 token |

## 关联
- Plan: [archive/20260709-用户认证/PLAN.md](../archive/20260709-用户认证/PLAN.md)
- ADR: [ADR-003](../knowledge/decisions/ADR-003.md)
```

### BUG → Pitfall 判断标准

| 问题 | 回答"是"→ 蒸馏 | 回答"否"→ 留在 Archive |
|------|:---:|:---:|
| 这个 Bug 的根因会在其他项目中重复出现吗？ | → knowledge/pitfalls/ | → archive 保留 |
| 这个 Bug 的修复模式值得新 Agent 提前知道吗？ | → knowledge/pitfalls/ | → archive 保留 |
| 这个 Bug 的教训可以形成一条规则吗？ | → 提炼 Skill | → archive 保留 |

### 蒸馏报告格式

Conductor 在蒸馏完成后，在 SESSION_LOG 中追加蒸馏报告：

```markdown
## 知识蒸馏

> 蒸馏时间: YYYY-MM-DD HH:MM
> 蒸馏者: Conductor

### 蒸馏产出
| 源 | 目标 | 类型 | ID |
|----|------|------|-----|
| FEATURE.md | knowledge/features/ | feature | FEAT-AUTH |
| ADR-003.md | knowledge/decisions/ | decision | ADR-003 |
| BUG-005.md | knowledge/pitfalls/ | pitfall | PIT-012 |

### 未蒸馏
| 源 | 原因 |
|----|------|
| BUG-006.md | 一次性环境问题，不会重复 |
| TASK_BOARD.md | Runtime 状态，不蒸馏 |

### 未完成任务
| Task ID | 状态 | 已写入 |
|---------|------|--------|
| T05 | 🔨进行中 | workspace/backlog.md |
```

---

## 崩溃恢复协议

### 场景

Conductor 异常中断（Agent 窗口崩溃、平台故障、网络断开）后，新 Conductor 启动时无法依赖「正常跨会话启动」流程——因为 SESSION_LOG 可能不完整、TASK_BOARD 里 🔨 任务已废弃、Git working tree 可能是脏的。

### 恢复流程

新 Conductor 启动后，在 **Phase 1 之前** 执行崩溃检测和恢复：

```
1. 读 PROGRESS.md → 当前会话指针
   ├─ 如果「当前会话」指向一个已存在的文件夹 → 可能崩溃
   └─ 如果「当前会话」为空或无会话 → 正常启动，跳过恢复

2. 检查会话文件夹完整性：
   ├─ SESSION_LOG.md 是否存在？
   ├─ SESSION_LOG「任务完成情况」表是否有内容？
   └─ TASK_BOARD.md 是否存在？

3. 判断场景：
   ├─ SESSION_LOG 完整 + TASK_BOARD 存在 → 正常跨会话启动
   ├─ SESSION_LOG 存在但任务表为空 + TASK_BOARD 存在 → 崩溃（Conductor 创建了文件但未派发）
   ├─ SESSION_LOG 存在但任务表部分填充 + TASK_BOARD 存在 → 崩溃（中途断掉）
   └─ SESSION_LOG 不存在 + TASK_BOARD 不存在 → 空文件夹，按新会话启动

4. 执行恢复（仅崩溃场景）：
   a. 读 TASK_BOARD.md，提取所有非终态任务（⏳/🟢/🔨/🔄/❌阻塞）
   b. 检查 Git 状态 — `git status --porcelain` + `git log -1 --oneline`
      ├─ 有未提交修改 → 记录「⚠️ 脏 working tree」到恢复报告
      └─ 干净 → 跳过
   c. 检查 SESSION_LOG 已有记录 → 标记哪些任务已有「简述/决策/产出/Commit」
   d. 对比 TASK_BOARD 与 SESSION_LOG 的差异 → 生成「恢复报告」
   e. 🔨 进行中的任务 → 回退为 🟢就绪（写入故障记录：类型=崩溃恢复）
   f. 更新 PROGRESS.md「当前会话」指针（如有必要创建新会话文件夹）
   g. 将恢复报告写入新 SESSION_LOG.md 的「崩溃恢复」段

5. 正常进入 Phase 1
```

### 恢复优先级

| 优先级 | 操作 | 理由 |
|--------|------|------|
| P0 | 检查 Git 脏状态 | 脏 tree 是上一个 Agent 改了一半的证据，新 Agent 需要知道 |
| P1 | TASK_BOARD 非终态任务提取 | 唯一真相源，不受 SESSION_LOG 完整度影响 |
| P2 | SESSION_LOG 已有记录标定 | 帮助新 Conductor 知道「上次做到哪了」 |
| P3 | 生成恢复报告 | 人类可读，便于用户确认恢复是否正确 |

### 恢复报告格式

```markdown
## 崩溃恢复

> 检测时间: YYYY-MM-DD HH:MM
> 恢复原因: Conductor 异常中断（SESSION_LOG 不完整 / TASK_BOARD 有 🔨 任务 / 其他）

### Git 状态
| HEAD | 脏文件 |
|------|--------|
| a1b2c3d | src/auth/login.py (modified), tests/test_auth.py (untracked) |

### 恢复操作
| 任务 | 原状态 | 新状态 | 已有进度 |
|------|--------|--------|---------|
| T03 | 🔨进行中 | 🟢就绪（崩溃恢复） | SESSION_LOG 记录: 简述="登录 UI 组件", Commit=— |
| T04 | ⏳等待 | ⏳等待（保留） | — |

### 注意事项
- ⚠️ Git working tree 有未提交修改，新 Agent 先 `git stash` 或检查后决定保留/丢弃
```

---

## Agent 状态快照

### 目的

Agent Snapshot 是崩溃恢复的 **Machine 视图**。与 SESSION_LOG（Human 视图）互补：

| | SESSION_LOG | Agent Snapshot |
|----|:---:|:---:|
| 读者 | 人 | Agent |
| 格式 | Markdown 表格 | YAML 结构化 |
| 更新者 | Conductor | Agent 自己 |
| 更新频率 | 每次任务终态 | 每次 checkpoint |
| 内容 | "做了什么" | "做到哪了、怎么接着做" |

### 存储位置

```
docs/YYYYMMDD-描述/agents/
├── backend-dev.yaml      ← Backend Dev 的状态快照
├── frontend-dev.yaml     ← Frontend Dev 的状态快照
├── architect.yaml        ← Architect 的状态快照
└── ...
```

### 格式

```yaml
# Agent Snapshot: backend-dev
# 此文件由 Agent 在任务执行过程中自动写入
# 崩溃恢复时，新 Agent 读取此文件即可接续工作

agent:
  role: backend-dev
  task_id: "T03"
  status: executing        # executing | checkpoint | completed | failed

current:
  goal: "实现 JWT 认证 API 的 token 刷新端点"
  step: "正在写 refresh token 的数据库查询逻辑"
  step_index: 4            # 在第几个子步骤

files:
  modified:
    - src/auth/service.py
    - src/auth/handler.py
  created:
    - tests/auth/test_refresh.py
  staged: false            # git 尚未 add

reasoning:
  summary: "选择在 service 层做 refresh token 验证，而非 handler 层——便于后续复用"
  assumptions:
    - "refresh token 存储在数据库的 refresh_tokens 表中"
    - "token 过期时间 7 天，与 access token 共用同一密钥"
  open_questions:
    - "refresh token 是否需要在 logout 时主动失效？当前假设不需要"

dependencies:
  resolved:
    - "API 契约来自 Architect（ADDR-003）"
    - "User 模型来自 T02 的产出"
  pending: []

next_action: "完成 refresh token DB 查询后，写单元测试验证 token 旋转逻辑"

checkpoint:
  time: "2026-07-09T14:25:00Z"
  commit: "d4e5f6g"       # 最后一个 commit（可能不是此任务的 commit）
```

### 字段说明

| 字段 | 说明 |
|------|------|
| `agent.role` | Agent 角色名 |
| `agent.task_id` | 当前执行的 Task ID |
| `agent.status` | executing（执行中）/ checkpoint（已存档）/ completed（已完成）/ failed（失败） |
| `current.goal` | 当前任务的目标描述 |
| `current.step` | 当前正在做的具体步骤 |
| `current.step_index` | 在第几个子步骤 |
| `files.modified` | 已修改的文件列表 |
| `files.created` | 新创建的文件列表 |
| `files.staged` | git 是否已 add |
| `reasoning.summary` | 一段话总结当前思路 |
| `reasoning.assumptions` | 当前基于的假设 |
| `reasoning.open_questions` | 尚未解决的问题 |
| `dependencies` | 已知的依赖（已解决 vs 待解决） |
| `next_action` | 恢复时下一个要执行的步骤 |
| `checkpoint.time` | 快照时间 |
| `checkpoint.commit` | 最后一个 commit hash |

### 更新规则

- Agent 在每个子步骤完成后写入 checkpoint
- 最少每 5 分钟写一次（即使子步骤未完成）
- Agent 完成任务后标记 `status: completed`，写最终 snapshot
- Agent 失败时标记 `status: failed`，写 failure snapshot（含 failure_reason）

### 恢复规则

```
新 Agent 领取任务时:
  1. 读 TASK_BOARD → 确认任务是 🔨进行中 还是 🟢就绪
  2. 读 agents/<role>.yaml:
     ├─ 不存在 → 全新开始
     ├─ status=completed → 任务已完成，检查 TASK_BOARD 状态是否匹配
     ├─ status=failed → 读 failure_reason，决定是否重新尝试
     └─ status=executing/checkpoint → 从 current.step + next_action 接续
  3. 检查 files.modified → git status 对比 → 处理脏文件
  4. 接续工作
```

### 与崩溃恢复协议的关系

崩溃恢复协议（见上文）的步骤 4.c 中，Conductor 读 `SESSION_LOG` 获取已完成的宏观信息；**Agent Snapshot 补充了微观信息**——具体做到哪个文件、哪一步、什么思路。两者结合提供完整的恢复上下文。

> **当前阶段**：Agent Snapshot 是规范定义。当前 Agent 实现中，Snapshot 的写入是可选的增强。Conductor 不强制要求 Agent 写 Snapshot。

