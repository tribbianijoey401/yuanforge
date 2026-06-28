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

| Task ID | 标题 | Role | 上游依赖 | 产出物 | 门禁 |
|---------|------|------|---------|--------|------|
| task-002 | 用户数据模型 | coder | task-001 | src/models/user.py, tests/models/ | G2 |
| task-003 | 用户管理 API | coder | task-002 | src/api/users.py, tests/api/ | G2 |
| task-004 | 用户管理前端 | coder | task-001 | src/ui/UserList.tsx, tests/ui/ | G2 |
| task-005 | 用户系统集成测试 | tester | task-002,task-003,task-004 | tests/integration/ | G3 |
| task-006 | 部署配置 | devops | task-005 | k8s/user-svc.yaml | G4 |
```

**字段说明：**

| 字段 | 必填 | 说明 |
|------|------|------|
| **Task ID** | ✅ | `task-NNN` 格式，NNN 从 001 开始连续编号 |
| **标题** | ✅ | 人类可读的 Task 描述 |
| **Role** | ✅ | 角色名：`architect` / `coder` / `reviewer` / `tester` / `devops` |
| **上游依赖** | ✅ | Task ID 列表，逗号分隔。无依赖填 `-` |
| **产出物** | ✅ | 完成后的产出文件列表，逗号分隔 |
| **门禁** | ✅ | 该 Task 触发的 Gate：G2（单 Task 审查）/ G3（集成测试）/ G4（部署） |

**规则：**
- **禁止**在 Task 字段中写自然语言需求 — Task 只是一个标识符，详细 spec 在 `dispatch/` 目录
- Task ID 必须与 `dispatch/` 下的文件名对应（如 `task-002` ↔ `dispatch/task-002.yaml`）
- 上游依赖必须精确列出所有前置 Task ID，禁止模糊依赖（如"等后端完成"）
- 并联 Task 不互相列在依赖中

### 5. 质量门禁

```markdown
## 质量门禁

| Gate | 检查内容 | 通过标准 | 执行者 |
|------|---------|---------|--------|
| G1 | Plan 完整性 | Dispatch Table 无遗漏、依赖正确、用户确认 | 用户 |
| G2 | Task 级审查 | Spec 合规 + 代码质量 APPROVED | reviewer |
| G3 | 集成测试 | `pytest tests/ -q` 全 PASS | tester |
| G4 | 交付就绪 | CI 通过 + 文档齐全 + 部署配置 | devops |
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
.yuanforge/plans/
```

---

## 与 dispatch 目录的关系

Plan 中的 Task 是一个**索引**。每个 Task 的详细执行 spec 放在独立文件中，Plan 只做关联。

```
.yuanforge/
├── plans/
│   └── 2026-06-29_user-auth.md    ← Plan（含 Dispatch Table）
└── dispatch/
    ├── task-002-data-model.md      ← Task 详细 spec
    ├── task-003-backend-api.md
    ├── task-004-frontend-ui.md
    ├── task-005-integration-test.md
    └── task-006-deploy-config.md
```

**Plan 轻，Task 重。** Plan 让 Conductor 快速理解全貌，Task 文件让 Coder 获取完整上下文。

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
