# Dispatch Table 协议规范

> **Dispatch Table 是 Agent 之间的调度协议。** 平台无关——任何 LLM Agent 或 Runtime Engine 都能解析并执行。
> 语言：**自然语言（人类） + Schema（机器）。** Markdown 是人类视图，Schema 是机器视图。

---

## 一、Dispatch Schema（机器可解析）

### 1.1 Task 定义

```yaml
task:
  id: "T03"
  priority: P2
  title: "实现 JWT token 刷新端点"
  role: "backend-dev"
  depends_on: ["T02"]
  timeout_minutes: 30
  output: ["src/auth/refresh.py", "tests/auth/test_refresh.py"]
  gate: "G2"
   risk: "R1"
  acceptance_criteria:
    - "refresh token 必须轮转"
    - "旧 token 必须在刷新后失效"
  context:                         # 派发时注入的最少上下文
    required_knowledge: ["ADR-003"]
    input_from: ["T02"]
```

### 1.2 字段定义

| 字段 | 类型 | 必填 | 说明 |
|------|------|:---:|------|
| `id` | string | ✅ | 格式 `T{NN}`，如 T01 |
| `priority` | enum | ✅ | P0/P1/P2/P3 |
| `title` | string | ✅ | 人类可读描述 |
| `role` | enum | ✅ | 12 个角色之一 |
| `depends_on` | array | ✅ | 依赖的 Task ID 列表，无依赖填 `[]` |
| `timeout_minutes` | int | ✅ | 超时分钟数 |
| `output` | array | ✅ | 预期产出文件路径 |
| `gate` | enum | ✅ | G1/G2/G3/G4 |
| `risk` | enum | — | R0/R1/R2（Product Analyst 产出） |
| `acceptance_criteria` | array | — | 验收标准 |
| `context.required_knowledge` | array | — | 派发时注入的 Knowledge ID |
| `context.input_from` | array | — | 上游 Task ID（上下文来源） |

---

## 二、确定性派发规则（Runtime Engine 执行）

以下规则是**确定性的**——不依赖 LLM 推理，任何平台都能实现：

### 2.1 初始化

```
1. 读 Dispatch Table → 提取所有 Task
2. 所有 Task 初始状态 = ⏳等待
3. depends_on = [] 的 Task → 🟢就绪
```

### 2.2 Promote（任务升级）

```
Rule: PROMOTE
  触发: 任意 Task 进入终态（✅完成/✅审查通过/✅测试通过/❌取消）
  动作:
    for each Task where status == ⏳等待:
      if all(dep in 终态 for dep in Task.depends_on):
        Task.status = 🟢就绪
```

### 2.3 Dispatch（任务派发）

```
Rule: DISPATCH
  触发: 存在 🟢就绪 Task + 有空闲 Agent
  动作:
    1. 选出优先级最高的 🟢就绪 Task
    2. 构建 Dispatch Context:
       - Task 自身的 title + acceptance_criteria
       - context.required_knowledge → 加载对应 knowledge/ 文件
       - context.input_from → 加载上游 Task 的 output 文件
    3. 派发到匹配 role 的 Agent
    4. Task.status = 🔨进行中
```

### 2.4 Timeout（超时）

```
Rule: TIMEOUT
  触发: Task.status == 🔨进行中 AND (now - started_at) > timeout_minutes
  动作:
    Task.status = 🟢就绪
    Task.attempts += 1
    if Task.attempts >= 3:
      Task.status = ❌阻塞
```

### 2.5 Cancel Cascade（取消级联）

```
Rule: CANCEL_CASCADE
  触发: Task.status = ❌取消
  动作:
    for each Task where Task.depends_on contains cancelled_task.id:
      Task.status = ❌阻塞
      Task.block_reason = "上游 T{cancelled_task.id} 已取消"
```

### 2.6 Block Check（阻塞检查）

```
Rule: BLOCK_CHECK
  触发: 每次巡检
  动作:
    检查所有 ❌阻塞 Task:
      if block_type == "外因":
        if 外部条件满足:
          Task.status = 🟢就绪
```

---

## 三、在 Plan 中的位置（向后兼容）

Dispatch Table 仍是 Plan 文件的 `## Dispatch Plan` 段落：

```markdown
## Dispatch Plan

### 依赖关系
- T03（JWT 刷新端点）依赖 T02 的 User 模型，不可在 T02 完成前开始
- T04（前端登录页）依赖 T03 的 API 契约，可与 T05 并行

### 任务派发表

| ID | 优 | 标题 | Role | 上游依赖 | ⏱超时 | 产出物 | 门禁 | 风险 | 验收标准 |
|----|----|------|------|---------|-------|--------|------|------|---------|
| T01 | P0 | 需求澄清 | product-analyst | - | 30 | 用户故事+验收标准.md | G1 | — | — |
| T02 | P0 | 架构设计 | architect | T01 | 120 | PLAN.md | G1 | — | — |
| T03 | P1 | JWT 刷新端点 | backend-dev | T02 | 30 | src/auth/refresh.py | G2 | P1 | token轮转+旧token失效 |
| T04 | P1 | 登录页面 | frontend-dev | T02 | 30 | src/ui/Login.tsx | G2 | P1 | 响应式+错误提示 |
```

> **Markdown 是人类视图，Schema（§一）是机器视图。** Runtime Engine 解析 Markdown 表格中的字段映射到 Schema。

---

## 四、Conductor 如何解析（LLM 兜底）

当 Runtime Engine 不可用时，Conductor 使用 LLM 推理作为兜底：

1. 解析「任务派发表」→ 提取所有 Task
2. 解析「依赖关系」→ 构建 DAG
3. 找出 `上游依赖 = "-"` 的 Task → 第一批 ready
4. 并行派发所有 ready Task
5. 任意 Task 完成后 → PROMOTE 规则 → 新的 ready
6. 重复直到全部 done

> **当前阶段**：无独立 Runtime Engine，Conductor 通过 LLM 推理执行派发。但派发逻辑（§二）已明确为确定性规则，未来可直接由 Runtime Engine 执行。
