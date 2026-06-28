# Dispatch Table 协议规范

> **Dispatch Table 是 Agent 之间的调度协议。** 它是 Plan 文件中的一个 Markdown 段落，Conductor Agent 解析它来自主派发任务。
> 语言：**自然语言，不是代码。** 任何 LLM Agent 都能读、都能写、都能执行。

---

## 在 Plan 中的位置

Dispatch Table 永远是 Plan 文件的 `## Dispatch Plan` 段落，包含两个子段：

```markdown
## Dispatch Plan

### 依赖关系
[自然语言描述]

### 任务派发表
[Markdown 表格]
```

---

## 依赖关系段规范

用自然语言描述 Task 之间的依赖。每行一个声明。

**格式：**
```
- {task-AAA}（{简述}）依赖 {task-BBB} 的 {产出物}，{可否并行}
```

**必须明确的信息：**
- 谁依赖谁（用 Task ID）
- 依赖什么（产出物名称）
- 能否与其他 Task 并行（明确说"可与 X 并行"/"不可在 X 完成前开始"）

**示例：**
```markdown
### 依赖关系

- task-002（数据模型）依赖 task-001 的 ARCHITECTURE.md，可与 task-004 并行
- task-003（后端 API）依赖 task-002 的数据模型，不可在 task-002 完成前开始
- task-004（前端界面）只依赖 task-001 的接口定义，与 task-003 可并行
- task-005（集成测试）必须在 task-002、task-003、task-004 全部完成后触发
- task-006（部署配置）依赖 task-005 通过
```

---

## 任务派发表规范

| 字段 | 必填 | 格式 | 说明 |
|------|------|------|------|
| **Task ID** | ✅ | `task-NNN` | NNN 从 001 开始，连续编号 |
| **标题** | ✅ | 人类可读 | 一句话描述 |
| **Role** | ✅ | `architect` / `coder` / `reviewer` / `tester` / `devops` | 执行者角色 |
| **上游依赖** | ✅ | Task ID 列表，逗号分隔 | 无依赖填 `-` |
| **产出物** | ✅ | 文件路径，逗号分隔 | 完成后产出的文件 |
| **门禁** | ✅ | `G2` / `G3` / `G4` | 该 Task 对应的质量 Gate |

**示例：**
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

---

## 与 dispatch 目录的关系

Plan 中的 Task 是**索引**。每个 Task 的详细执行 spec 放在独立文件中：

```
.yuanforge/
├── plans/
│   └── 2026-06-29_user-auth.md         ← Plan（含 Dispatch Table）
└── dispatch/
    ├── task-002-data-model.md           ← Task 详细 spec
    ├── task-003-backend-api.md
    ├── task-004-frontend-ui.md
    ├── task-005-integration-test.md
    └── task-006-deploy-config.md
```

---

## Conductor 如何解析

Conductor 读 Dispatch Table 后的推理链：

1. 解析「任务派发表」→ 提取所有 Task
2. 解析「依赖关系」→ 构建 DAG
3. 找出 `上游依赖 = "-"` 的 Task → **第一批 ready**
4. 并行派发所有 ready Task
5. 任意 Task 完成后 → 检查是否有 Task 的「上游依赖」全满足 → 新的 ready
6. 重复直到全部 done

---

## 反模式

```markdown
❌ 依赖关系写 "等后端好了再搞前端"          → 用精确的 Task ID
❌ Task 标题写 "实现登录（含前后端+数据库）" → 拆成多个 Task
❌ 上游依赖写 "全部完成"                    → 列出具体 Task ID
❌ 产出物写 "相关代码"                       → 列出具体文件路径
❌ 同一个 Task 既是 coder 又是 reviewer      → 违反铁律 Ⅲ/Ⅴ
```
