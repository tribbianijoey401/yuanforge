# Action Protocol — 动作协议

> **依赖**: runtime-protocol → state-protocol

> **协议定位**：定义 YuanForge 系统中所有平台必须支持的统一动作。
> **本协议只定义「动作的语义」。**
>
> 不定义怎么做（那是 Platform Adapter）、不定义何时做（那是 Workflow Protocol）。

---

## 一、设计原则

```
Runtime 不执行。
Runtime 只产生 Action。

Action 是 Workflow 的唯一输出。
Platform Adapter 是 Action 的唯一执行者。
```

**铁律**：所有平台必须支持本文定义的 8 个 Action。不支持的平台用 `manual` 降级——但语义必须等价。

---

## 二、Action 总览

| Action | 语义 | 触发者 | 产出 |
|--------|------|--------|------|
| **Dispatch** | 派发一个 Task 到 Agent | Conductor | Agent 开始执行 |
| **Complete** | Agent 完成 Task | Agent | 状态变更 + 产出文件 |
| **Review** | 审查 Task 产出 | Reviewer | 审查结果 |
| **Snapshot** | 保存 Agent 当前状态 | Agent / Conductor | Snapshot 对象 |
| **Checkpoint** | 保存 Workspace 全量状态 | Conductor | Checkpoint 对象 |
| **Promote** | 将 Workspace 产出晋升到 Knowledge | Conductor | Knowledge 对象更新 |
| **Archive** | 归档 Workspace | Conductor | Workspace 移入 archive/ |
| **Recover** | 从崩溃中恢复 | Conductor | 恢复的 Workspace 状态 |

---

## 三、Action 详解

### 3.1 Dispatch

```
语义: 将一个 🟢就绪 的 Task 交给对应角色的 Agent 执行。

输入:
  - task: Task 对象
  - context: 派发上下文
    - role_contract: 角色合约路径
    - required_knowledge: 必读 Knowledge ID 列表
    - input_from: 上游 Task ID 列表
    - acceptance_criteria: 验收标准

输出:
  - Agent 开始执行 Task
  - Task 状态: 🟢就绪 → 🔨进行中

平台无关约束:
  - 新 Agent 不得继承父会话记忆
  - 所有上下文必须通过 context 显式传递
```

### 3.2 Complete

```
语义: Agent 完成 Task 执行，产出代码/文档/设计。

输入:
  - task_id: Task ID
  - output_files: 产出文件列表
  - commit_hash: 原子提交的 commit hash

输出:
  - Task 状态: 🔨进行中 → ✅完成
  - TASK_BOARD 上下文传递段更新
  - Event: TASK_STATUS_CHANGED
```

### 3.3 Review

```
语义: 审查 Agent 对 Task 产出物进行评估。

输入:
  - task_id: Task ID
  - review_type: spec / security / quality / ux
  - acceptance_criteria: 验收标准
  - diff: 变更内容

输出:
  - 审查结果: PASS / BLOCKER / ADVISORY
  - 审查报告（独立呈现，不合并）
  - Task 状态: ✅完成 → ✅审查通过 / 🔄返工
  - Event: REVIEW_RESULT

审查档位:
  - 🔴 Blocker: 不解决不合入
  - 🟡 Hard Gate: 必须全绿
  - 🟢 Advisory: 可豁免，同类≥3 自动升级

平台无关约束:
  - 审查报告必须独立呈现，不合并/不重排序/不跨轴比较
  - 任意 Blocker → 通知其他审查官暂停
```

### 3.4 Snapshot

```
语义: 保存 Agent 在当前时刻的执行状态——用于崩溃恢复。

输入:
  - agent_role: 角色
  - task_id: Task ID
  - current_step: 当前步骤描述
  - files_modified: 已修改文件列表

输出:
  - Snapshot 对象写入 agents/ 目录
  - 状态: executing → checkpoint

触发: Agent 定期写入（建议 5 分钟间隔）或 Conductor 巡检时触发
```

### 3.5 Checkpoint

```
语义: 保存 Workspace 的完整状态——归档时生成。

输入:
  - workspace_id: Workspace ID
  - task_states: 所有 Task 最终状态
  - knowledge_outputs: 蒸馏产出的 Knowledge ID
  - git_head: 归档时 commit hash

输出:
  - Checkpoint 对象
  - 状态: created → archived

触发: Workspace Close 蒸馏完成后
```

### 3.6 Promote

```
语义: 将 Workspace 中完成的工作晋升为 Knowledge。

输入:
  - workspace_id: Workspace ID
  - candidates: Candidate 列表（FEATURE/ADR/BUG→Pitfall）

输出:
  - Knowledge 对象更新（features/decisions/pitfalls/）
  - 蒸馏报告写入 SESSION_LOG
  - Event: DISTILLATION_COMPLETE + KNOWLEDGE_UPDATED
  - Graph 重建

触发: Workspace 进入 distilling 状态时

平台无关约束:
  - 必须经过 Proposal 事务层（Knowledge 写保护）
  - BUG→Pitfall 必须按确定性规则判断
```

### 3.7 Archive

```
语义: 归档已关闭的 Workspace。

输入:
  - workspace_id: Workspace ID
  - archive_path: 归档目标路径

输出:
  - Workspace 目录移入 archive/
  - Workspace 状态: distilling → archived
  - Event: WORKSPACE_CLOSED

触发: Promote 完成后
```

### 3.8 Recover

```
语义: 从崩溃或异常中断中恢复 Workspace。

输入:
  - workspace_id: Workspace ID（如果存在）

输出:
  - 🔨进行中 → 🟢就绪（回退）
  - 恢复报告写入 SESSION_LOG
  - Event: CRASH_RECOVERED

触发: Conductor 在新会话启动时检测到异常中断

恢复流程:
  1. 读 PROGRESS → 找到当前 Workspace
  2. 读 TASK_BOARD → 提取非终态任务
  3. git status → 检查脏文件
  4. 🔨 → 🟢（回退）
  5. 重算依赖
  6. 通知用户
```

---

## 四、Action 与对象的关系

| Action | 操作的对象 | 状态变更 |
|--------|-----------|---------|
| Dispatch | Task | 🟢→🔨 |
| Complete | Task | 🔨→✅ |
| Review | Task | ✅→✅审查/🔄返工 |
| Snapshot | Snapshot | executing→checkpoint |
| Checkpoint | Checkpoint | created→archived |
| Promote | Feature/ADR/Pitfall | 创建/更新 Knowledge 对象 |
| Archive | Workspace | distilling→archived |
| Recover | Task/Workspace | 🔨→🟢 |

---

## 五、与其他协议的关系

| 协议 | 依赖方式 |
|------|---------|
| Object Protocol | Action 操作的对象由 Object Protocol 定义 |
| State Protocol | Action 触发 State Protocol 定义的转换 |
| Workflow Protocol | Workflow 决定何时产生哪个 Action |
| Adapter Protocol | Adapter 执行 Action 的平台特定实现 |
