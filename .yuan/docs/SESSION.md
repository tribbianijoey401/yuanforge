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
    ↓ Phase 2 进行中
7. Conductor 渐进更新 SESSION_LOG「任务完成情况」表（每次任务终态时）
    ↓ Phase 2 完成
8. Coder 更新 FEATURE.md（修改文件+API）
9. Conductor 更新 SESSION_LOG.md（完成/决策/踩坑）
    ↓ Phase 4
10. Conductor 遍历 BUG → 归档判断 → PROGRESS 更新
11. 会话完成，PROGRESS 移至历史会话
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

