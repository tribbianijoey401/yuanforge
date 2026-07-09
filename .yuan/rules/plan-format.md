# Plan 工程化格式规范

> Plan 不是给人类看的笔记，而是 Agent 军团的**作战指令书**。
> 任何 Architect Agent 产出 Plan 时，必须严格遵守此格式。
> Conductor Agent 依赖此格式解析 Task、构建 DAG、派发任务。

---

## Plan 文件结构

```markdown
# Plan: [功能名称]

## 概况
## 技术方案
## 模块划分
## Dispatch Plan
### 依赖关系
### 任务派发表
## 质量门禁
```

---

## 各段规范

### 1. 概况

```markdown
## 概况

- **目标**: 一句话描述要交付什么
- **创建时间**: YYYY-MM-DD
- **Architect**: [产出此 Plan 的 Agent 角色]
- **关联需求**: [用户原始需求摘要]
```

### 2. 技术方案

```markdown
## 技术方案

### 技术栈选择

| 层 | 选型 | 原因 |
|----|------|------|
| 语言 | Python 3.11 | xxx |
| 框架 | FastAPI | xxx |
| 数据库 | PostgreSQL | xxx |

### 架构决策

[关键决策简述，详细 ADR 见 docs/DECISIONS.md]
```

### 3. 模块划分

```markdown
## 模块划分

| 模块 | 职责 | 对应 Task | 关键文件 |
|------|------|----------|---------|
| 用户模型 | 数据层 | task-002 | src/models/user.py |
| 用户 API | 接口层 | task-003 | src/api/users.py |
| 前端界面 | 展示层 | task-004 | src/ui/UserList.tsx |
```

### 4. Dispatch Plan（调度指令）

这是 Plan 最关键的段落。Conductor Agent 读这一段就知道：
- 有哪些 Task
- 每个 Task 谁来做（role）
- Task 之间的依赖关系（谁等谁）
- 哪些 Task 可以并行

#### 4.1 依赖关系（自然语言）

```markdown
### 依赖关系

- task-002（数据模型）依赖 task-001 的 ARCHITECTURE.md，可与 task-004 并行
- task-003（后端 API）依赖 task-002 的数据模型，不可在 task-002 完成前开始
- task-004（前端界面）只依赖 task-001 的接口定义，与 task-003 可并行
- task-005（集成测试）必须在 task-002、task-003、task-004 全部完成后触发
- task-006（部署）依赖 task-005 通过
```

**规则：**
- 用自然语言描述，不要用代码
- 每行一个依赖声明
- 明确说"可与 X 并行"来标记独立关系
- Conductor 根据这段描述和下面的派发表，自行构建 DAG

#### 4.2 任务派发表

```markdown
### 任务派发表

| Task ID | 优 | 标题 | Role | 上游依赖 | ⏱超时 | 产出物 | 门禁 | 风险 |
|---------|----|------|------|---------|-------|--------|------|------|
| task-002 | P1 | 数据模型 | backend-dev | task-001 | 30 | src/models/user.py, tests/ | G2 | P1 |
| task-003 | P1 | 用户管理 API | backend-dev | task-002 | 30 | src/api/users.py, tests/ | G2 | P1 |
| task-004 | P1 | 用户管理前端 | frontend-dev | task-001 | 30 | src/ui/UserList.tsx, tests/ | G2 | P1 |
| task-005 | P1 | 集成测试 | tester | task-003,task-004 | 20 | tests/integration/ | G3 | — |
| task-006 | P2 | 文档归档 | doc-engineer | task-005 | 10 | docs/CHANGELOG.md | G4 | — |
```

**字段说明：**

| 字段 | 必填 | 说明 |
|------|------|------|
| **Task ID** | ✅ | `task-NNN` 格式，NNN 从 001 开始连续编号 |
| **优** | ✅ | 优先级：P0=紧急, P1=高, P2=中(默认), P3=低 |
| **标题** | ✅ | 人类可读的 Task 描述 |
| **Role** | ✅ | 角色名：`product-analyst` / `architect` / `ui-designer` / `frontend-dev` / `backend-dev` / `spec-reviewer` / `security-auditor` / `quality-auditor` / `ux-reviewer` / `tester` / `doc-engineer` |
| **上游依赖** | ✅ | Task ID 列表，逗号分隔。无依赖填 `-` |
| **⏱超时** | ✅ | 分钟数，Architect 覆写默认值 |
| **产出物** | ✅ | 完成后的产出文件列表，逗号分隔 |
| **门禁** | ✅ | 该 Task 触发的 Gate：G1 / G2 / G3 / G4 |
| **风险** | ✅ | Product Analyst 产出：P0/P1/P2，决定 Security Auditor 投入 |

### 5. 质量门禁

```markdown
## 质量门禁

| Gate | 检查内容 | 通过标准 | 执行者 |
|------|---------|---------|--------|
| G1 | Plan 完整性 + 用户确认设计理解书 | Dispatch Table 无遗漏、依赖正确、用户确认 | 用户 |
| G2 | 四审查官并行 | 🔴 Blocker 全部解决 | spec-reviewer, security-auditor, quality-auditor, ux-reviewer |
| G3 | 集成测试 | 🟡 Hard Gate — 全量测试 PASS | tester |
| G4 | 文档归档 | Doc Engineer 归档完成 | doc-engineer |
```

---

## Plan 文件命名与存放

```bash
# 文件命名
{YYYY-MM-DD}_{功能名}.md

# 示例
2026-06-29_user-auth.md
2026-06-30_payment-gateway.md

# 存放路径
docs/YYYYMMDD-描述/PLAN.md
```

---

## 与 Task Spec 的关系

Plan 中的 Task 是一个**索引**。每个 Task 的详细执行 spec 放在会话文件夹中：

```
docs/YYYYMMDD-描述/
├── PLAN.md                              ← Plan（含 Dispatch Table）
├── TASK_BOARD.md                        ← 运行时任务板
├── SESSION_LOG.md
├── FEATURE.md
├── ADR-NNN.md
└── BUG-NNN.md
```

**Plan 轻，Task 重。** Plan 让 Conductor 快速理解全貌，Task 文件让 Dev 获取完整上下文。

---

## 反模式（禁止）

```markdown
❌ 依赖关系写 "等后端好了再搞前端" — 用精确的 Task ID
❌ Task 标题写 "实现用户登录功能，包括前端、后端、数据库" — 拆成多个 Task
❌ 上游依赖写 "全部完成" — 列出具体 Task ID
❌ 产出物写 "相关代码" — 列出具体文件路径
❌ Dispatch Table 缺 Task — Conductor 无法调度
❌ 同一个 Task 既是后端又是前端 — 违反上下文隔离（铁律 Ⅴ）
```
