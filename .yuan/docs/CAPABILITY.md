# CAPABILITY — 平台能力模型规格书

> 定义每个 Agent 平台的能力描述符，使 Runtime 能根据平台能力自动选择执行策略。

---

## 一、设计原则

```
Workflow 只描述"要做什么"（Task）
Platform Adapter 只负责"怎么执行"（Capability）

Runtime 读 Capability → 自动选择策略
Workflow 永远不关心平台细节
```

---

## 二、Capability 描述符

```yaml
platform: "hermes"                   # 平台标识
version: "1.0"

capabilities:
  subagent:
    supported: true
    max_concurrent: 3
    description: "delegate_task 并行派发子 Agent"

  parallel:
    supported: true
    description: "同角色无依赖 Task 可并行派发"

  filesystem:
    supported: true
    operations: [read, write, patch, search, list]
    description: "完整的文件系统操作"

  shell:
    supported: true
    background: true                 # 支持后台进程
    description: "terminal + process 管理"

  approval:
    supported: true                  # 危险操作需要用户确认
    description: "危险命令自动触发确认"

  patch:
    supported: true
    description: "fuzzy-matching 文件编辑"

  persistent_session:
    supported: true                  # 跨会话记忆
    description: "memory 工具跨会话持久化"

  knowledge_graph:
    supported: false                 # 无原生 Graph 查询
    fallback: "grep knowledge/ frontmatter"
    description: "Graph 查询通过 grep + JSON 解析模拟"

  event_store:
    supported: true
    description: "JSONL 追加写入 events/"

  git:
    supported: true
    description: "terminal 中执行 git 命令"

execution:
  strategies:
    - parallel          # 无依赖 Task 并行
    - sequential        # 有依赖 Task 串行
    - interactive       # 需要用户确认的 Task
    - manual            # 平台无法执行，提示用户手动操作

defaults:
  max_retry: 3
  timeout_buffer_minutes: 5         # 在 Task timeout 基础上加缓冲
  checkpoint_interval_minutes: 5    # Agent Snapshot 写入间隔
```

---

## 三、平台能力矩阵

| 能力 | Hermes | Manual | Cursor (未来) | Claude Code (未来) |
|------|:---:|:---:|:---:|:---:|
| subagent | ✅ 3并发 | ❌ | ✅ | ✅ |
| parallel | ✅ | ❌ | ✅ | ✅ |
| filesystem | ✅ full | ✅ 人工 | ✅ | ✅ |
| shell | ✅ +bg | ✅ 人工 | ✅ | ✅ |
| approval | ✅ | ✅ 人工 | ❌ | ❌ |
| patch | ✅ | ❌ | ✅ | ✅ |
| persistent_session | ✅ | ❌ | ✅ | ✅ |
| knowledge_graph | ⚠️ grep | ❌ | ✅ 原生 | ✅ 原生 |
| event_store | ✅ | ✅ 人工 | ✅ | ✅ |
| git | ✅ | ✅ 人工 | ✅ | ✅ |

---

## 四、Runtime 如何选择执行策略

```
1. 读 platform Capability
2. 读 Dispatch Table → 构建 Task DAG
3. 按 Execution Strategy 决策:

   if capabilities.parallel AND 存在多个无依赖 🟢就绪 Task:
     → strategy = parallel
     → 同时派发所有无依赖 Task

   elif 所有 🟢就绪 Task 有依赖关系:
     → strategy = sequential
     → 按优先级串行派发

   if capabilities.subagent:
     → 每个 Task 派发到独立 subagent
   else:
     → strategy = interactive or manual
     → 提示用户手动执行
```

---

## 五、降级策略

当平台缺少某项能力时，Runtime 自动降级：

| 缺失能力 | 降级策略 |
|---------|---------|
| subagent | sequential 模式，Agent 串行执行每个 Task |
| parallel | sequential 模式，按优先级排队 |
| filesystem | 提示用户手动创建/编辑文件 |
| shell | 提示用户手动执行命令 |
| persistent_session | SESSION_LOG + PROGRESS.md 作为跨会话桥梁 |
| knowledge_graph | grep knowledge/ 目录的 frontmatter |
| event_store | SESSION_LOG「任务完成情况」表替代 |

**降级铁律**：降级后行为必须**完全等价**——只是更慢/需要人工介入，但最终产出一致。

---

## 六、平台适配器接口

```
Platform Adapter 必须实现:

  dispatch(task: Task, context: Context) → Agent
    将 Task + 上下文派发到 Agent，返回 Agent 句柄

  status(task_id: str) → TaskStatus
    查询 Task 当前状态

  cancel(task_id: str) → void
    取消正在执行的 Task

  wait(task_ids: list[str]) → void
    阻塞等待所有指定 Task 完成

  capability() → Capability
    返回平台能力描述符
```

> **当前阶段**：Adapter 接口是规范定义。Hermes 平台通过 Conductor + delegate_task 实现，Manual 平台通过人工执行实现。

---

## 七、与现有规格书的关系

| 规格书 | 关联 |
|--------|------|
| RUNTIME_MODEL.md | Task/Workspace/Snapshot 对象定义——Adapter 操作的对象 |
| dispatch-table.md | Dispatch Schema——Adapter 的输入 |
| PROMOTION.md | Promotion Pipeline——Adapter 不参与，由 Runtime Engine 执行 |
| .yuan/platforms/ | 平台适配器实现——每个平台实现 Adapter 接口 |
