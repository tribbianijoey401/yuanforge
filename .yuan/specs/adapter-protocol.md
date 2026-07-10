# Adapter Protocol — 平台适配协议

> **协议定位**：定义每个 Agent 平台如何实现 YuanForge 的 Action。
> **这是 5 份协议中唯一需要在具体平台上「实现」的协议。**
>
> 其余 4 份协议（Object / State / Action / Workflow）是纯规范——任何平台都能读懂。
> 本协议定义了「读懂之后怎么做」。

---

## 一、设计原则

```
YuanForge 不构建 Runtime。
LLM 自己就是 Runtime。

但不同的 LLM 平台有不同的能力：
  - Hermes: delegate_task（子 Agent 派发）
  - Claude Code: subagent 模式
  - Codex CLI: 新 Session 派发
  - Cursor: 角色切换
  - Manual: 人工执行

Adapter Protocol 就是让每个平台回答同一个问题：
  「你如何执行 Dispatch？你如何执行 Review？...」
```

**铁律**：平台只需要告诉 YuanForge「这些 Action 如何实现」——其余协议完全不用修改。

---

## 二、Adapter 接口

每个平台 Adapter 必须实现以下 8 个方法。其中 `dispatch` 有三个 Tier 实现：

```
dispatch(task: Task, context: Context) → void
  语义: 派发一个 Task 到 Agent
  输入: Task 对象 + 派发上下文（角色合约 + Knowledge 引用 + 上游产出物）
  输出: Agent 开始执行，Task 状态变更
  实现 Tier（按优先级）:
    Tier 1 — subagent: 创建独立子 Agent（delegate_task / Task tool）
    Tier 2 — exec: 后台进程执行（terminal background / 新 Session）
    Tier 3 — role-switch: 同一 Agent 内切换 persona（见 §三-6）

review(task: Task, criteria: Criteria) → ReviewResult
  语义: 审查 Task 产出物
  输入: Task 对象 + 验收标准
  输出: PASS / BLOCKER / ADVISORY

snapshot(agent_role: str, task_id: str, state: dict) → void
  语义: 保存 Agent 当前执行状态
  输入: 角色 + Task ID + 当前状态
  输出: Snapshot 对象持久化

checkpoint(workspace_id: str, state: dict) → void
  语义: 保存 Workspace 全量状态
  输入: Workspace ID + 所有 Task 终态
  输出: Checkpoint 对象持久化

recover(workspace_id: str) → RecoveryReport
  语义: 从崩溃恢复
  输入: 异常中断的 Workspace ID
  输出: 恢复报告（回退任务 + 脏文件 + 通知）

archive(workspace_id: str) → void
  语义: 归档 Workspace
  输入: Workspace ID
  输出: Workspace → archive/

promote(candidates: list[Candidate]) → void
  语义: 将 Candidate 晋升到 Knowledge
  输入: Candidate 列表
  输出: Knowledge 对象更新 + Proposal 事务
```

---

## 三、平台 Action 映射

### 3.1 Hermes

```yaml
platform: hermes
transport: hermes-subagent

dispatch:
  implementation: delegate_task
  notes: "同步派发子 Agent，父 Agent 等待完成"
  max_concurrent: 3

review:
  implementation: delegate_task
  notes: "以对应 Reviewer 角色派发子 Agent"

snapshot:
  implementation: file_write
  notes: "写入 agents/ 目录"

checkpoint:
  implementation: file_write + terminal(git)
  notes: "全量状态写入 archive/"

recover:
  implementation: conductor_loop
  notes: "Conductor 在新会话中执行恢复协议"

archive:
  implementation: terminal(mv)
  notes: "mv docs/YYYYMMDD-描述/ → docs/archive/"

promote:
  implementation: conductor_loop
  notes: "Conductor 执行蒸馏 Checklist"

capabilities:
  parallel: true
  max_concurrent: 3
  persistent_session: true
  filesystem: full
  shell: full (含 background)
```

### 3.2 Manual（兜底方案）

```yaml
platform: manual
transport: human-operated

dispatch:
  implementation: prompt_user
  notes: |
    提示用户:
    1. 在终端执行: cd project && echo "Task: [summary]"
    2. 加载 contracts/[role].md 为 Agent 角色
    3. 读 TASK_BOARD.md 获取上下文
    4. 执行任务
    5. 更新 TASK_BOARD.md 状态行

review:
  implementation: prompt_user
  notes: "提示用户手动执行审查 Checklist"

snapshot:
  implementation: manual_checkpoint
  notes: "提示用户记录当前进度到 agents/"

checkpoint:
  implementation: manual_archive
  notes: "提示用户打包 Workspace"

recover:
  implementation: manual_check
  notes: "提示用户检查异常并手动恢复"

archive:
  implementation: manual_move
  notes: "提示用户移动目录到 archive/"

promote:
  implementation: manual_extract
  notes: "提示用户按 distillation-checklist 手动提取知识"

capabilities:
  parallel: false
  filesystem: manual
  shell: manual
  subagent: false
  persistent_session: false
```

### 3.3 Claude Code（未来）

```yaml
platform: claude-code
transport: claude-subagent

dispatch:
  implementation: Task tool (subagent)
  notes: "Claude Code 的 Task 工具派发子 Agent"
  max_concurrent: TBD

review:
  implementation: Task tool
  notes: "以 Reviewer 角色创建子 Agent"

capabilities:
  parallel: true
  filesystem: full
  shell: full
  subagent: true
```

### 3.4 Codex CLI（未来）

```yaml
platform: codex
transport: new-session

dispatch:
  implementation: new_session
  notes: |
    1. 创建新的 Codex Session
    2. 加载 Task Snapshot + Role Contract + Required Specs
    3. 执行任务 → 输出 Result

review:
  implementation: new_session
  notes: "创建 Review Session，输入 Diff + Acceptance Criteria"

capabilities:
  parallel: false
  filesystem: full
  shell: full
  subagent: false
```

### 3.5 Cursor（未来）

```yaml
platform: cursor
transport: role-switch

dispatch:
  implementation: prompt_role_switch
  notes: "提示用户切换到对应角色，新对话中执行 Task"

review:
  implementation: prompt_role_switch
  notes: "提示用户切换为 Reviewer 角色"

capabilities:
  parallel: false
  filesystem: full
  shell: full
  subagent: false
```

### 3.6 Tier 3 Role-Switch Protocol（兜底）

**当平台既无 subagent 也无后台进程时，降级到角色切换模式。**

```yaml
platform: generic (Tier 3 fallback)
transport: role-switch

dispatch:
  implementation: persona_switch
  protocol: |
    1. Conductor 写 TASK_BOARD「Conductor 调度状态」— 标记当前派发目标
    2. Conductor 写「派发日志」— 记录 Tier 3 派发
    3. 加载目标角色合约（contracts/<role>.md）+ 铁律
    4. 切换 persona：「你现在是 {role}。读 TASK_BOARD 获取任务上下文。」
    5. Agent 执行：读 TASK_BOARD → 执行任务 → 写 TASK_BOARD
    6. Agent 写产出 + 审查结果到 TASK_BOARD
    7. 切换回 Conductor：「你现在是 Conductor。读 TASK_BOARD 决定下一步。」
    8. Conductor 读 TASK_BOARD → 决定下一步
    9. Conductor 写 Event

review:
  implementation: persona_switch
  protocol: |
    同上流程，但加载 Reviewer 角色合约

capabilities:
  parallel: false
  filesystem: full
  shell: full
  subagent: false
  role_switch: true
  note: "串行执行。TASK_BOARD 是唯一状态桥梁。Conductor 与执行 Agent 共享同一上下文窗口 — 超长会话注意 token 消耗。"
```

> **⚠️ Tier 3 不是设计目标。** 它是让没有子 Agent 能力的平台也能走通 YuanForge 流程的兜底方案。完整协议见 `.yuan/skills/role-switch.md`。

---

## 四、降级策略

当平台缺少某项能力时，自动降级——语义等价，只是更慢或需人工介入：

| 缺失能力 | 降级策略 |
|---------|---------|
| subagent | Tier 2: terminal(background=true) 后台进程 → Tier 3: role-switch 角色切换 |
| subagent + background | Tier 3: role-switch — 同一 Agent 内切换 persona，TASK_BOARD 作状态桥梁 |
| parallel | sequential 模式，按优先级排队 |
| filesystem | 提示用户手动创建/编辑文件 |
| shell | 提示用户手动执行命令 |
| persistent_session | SESSION_LOG + PROGRESS.md 作为跨会话桥梁 |

**降级铁律：**
1. 降级后行为必须完全等价——只是更慢/需要人工，最终产出一致
2. Tier 1 → Tier 2 → Tier 3，逐级降级，禁止跳级
3. 禁止在 Tier 1/2 可用时降级到 Tier 3（Tier 3 仅兜底）

---

## 五、平台适配器文件位置

```
.yuan/platforms/
├── hermes.md       ← Hermes Agent 平台适配
├── manual.md       ← 通用人工兜底方案
├── claude.md       ← Claude Code（未来）
├── codex.md        ← Codex CLI（未来）
└── cursor.md       ← Cursor（未来）
```

每个文件按 §三 的格式描述平台 Action 映射 + 能力声明。

---

## 六、与现有平台适配器的关系

当前的 `.yuan/platforms/hermes.md` 和 `.yuan/platforms/manual.md` 已包含能力描述符和工具映射。
本协议不替代它们——本协议是**规范定义**，它们是基于本规范的**具体实现**。

现有文件需追加 §三 格式的 Action 映射段，使其与本协议对齐。

---

## 七、与其他协议的关系

| 协议 | 依赖方式 |
|------|---------|
| Object Protocol | Adapter 操作的对象由 Object Protocol 定义 |
| State Protocol | Adapter 执行的状态转换由 State Protocol 定义 |
| Action Protocol | Adapter 实现的接口由 Action Protocol 定义 |
| Workflow Protocol | Adapter 由 Workflow Interpreter（Conductor）调用 |
