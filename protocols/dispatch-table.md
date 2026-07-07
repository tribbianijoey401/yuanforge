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
| **优先级** | ✅ | `P0/P1/P2/P3` | P0=紧急, P2=默认。Architect 设置 |
| **标题** | ✅ | 人类可读 | 一句话描述 |
| **Role** | ✅ | `product-analyst` / `architect` / `ui-designer` / `frontend-dev` / `backend-dev` / `spec-reviewer` / `security-auditor` / `quality-auditor` / `ux-reviewer` / `tester` / `doc-engineer` | 执行者角色 |
| **上游依赖** | ✅ | Task ID 列表，逗号分隔 | 无依赖填 `-` |
| **⏱超时(分)** | ✅ | 整数 | 默认: product-analyst=30, architect=120, ui-designer=60, dev=30, reviewer=15, security=30, quality=20, ux=15, tester=20, doc-engineer=10。Architect 可覆写 |
| **产出物** | ✅ | 文件路径，逗号分隔 | 完成后产出的文件 |
| **门禁** | ✅ | `G1` / `G2` / `G3` / `G4` | 该 Task 对应的质量 Gate |
| **风险标签** | 🆕 | `P0/P1/P2` | Product Analyst 产出，决定 Security Auditor 投入 |

**示例：**
```markdown
### 任务派发表

| Task ID | 优 | 标题 | Role | 上游依赖 | ⏱超时 | 产出物 | 门禁 | 风险 |
|---------|----|------|------|---------|-------|--------|------|------|
| task-001 | P0 | 需求澄清 | product-analyst | - | 30 | docs/xxxx/用户故事+验收标准.md | G1 | — |
| task-002 | P0 | 架构设计 | architect | task-001 | 120 | docs/xxxx/PLAN.md, docs/ARCHITECTURE.md | G1 | — |
| task-003 | P1 | 数据模型 | backend-dev | task-002 | 30 | src/models/user.py, tests/ | G2 | P1 |
| task-004 | P1 | 用户管理 API | backend-dev | task-003 | 30 | src/api/users.py, tests/ | G2 | P1 |
| task-005 | P1 | 用户管理前端 | frontend-dev | task-002 | 30 | src/ui/UserList.tsx, tests/ | G2 | P1 |
| task-006 | P1 | 集成测试 | tester | task-004,task-005 | 20 | tests/integration/ | G3 | — |
| task-007 | P2 | 文档归档 | doc-engineer | task-006 | 10 | docs/CHANGELOG.md | G4 | — |
```

---

## 与 Task Spec 的关系

Plan 中的 Task 是**索引**。每个 Task 的详细执行 spec 放在会话文件夹中：

```
docs/YYYYMMDD-描述/
├── PLAN.md                              ← Plan（含 Dispatch Table）
├── TASK_BOARD.md                        ← 运行时任务板
├── SESSION_LOG.md
├── FEATURE.md
├── ADR-NNN.md
└── BUG-NNN.md
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
❌ 同一个 Task 既是 dev 又是 reviewer      → 违反铁律 Ⅲ/Ⅴ
```
