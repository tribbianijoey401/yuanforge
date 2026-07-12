# Role-Switch Protocol — Tier 3 角色切换

> **这是兜底方案，不是设计目标。** 仅当 Tier 1（subagent）和 Tier 2（后台进程）都不可用时使用。
> **禁止在 Tier 1/2 可用时降级到此模式。**

---

## 何时触发

- Conductor 平台探测结果：`delegate_task` 不可用 + `terminal(background=true)` 不可用
- 典型场景：Manual 模式、Cursor、不支持的 Agent 平台

---

## 协议流程

### Conductor → 目标 Agent

```
第 1 步：Conductor 写 TASK_BOARD
  ├── 「Conductor 调度状态」段：标记「正在派发 T-ID → 角色」
  └── 「派发日志」段：追加「[时间] T-ID Tier 3 → 角色 开始」

第 2 步：Conductor 切换 persona
  ├── 加载 contracts/<role>.md（目标角色合约）
  ├── 加载 .yuan/rules/iron-rules.md（铁律）
  └── 切换指令：
      「你现在是 {role}。以下是你的任务：
       1. 读 TASK_BOARD.md — 获取任务上下文和启动协议
       2. 按铁律和角色合约执行任务
       3. 完成后更新 TASK_BOARD — 状态行、上下文传递、审查结果
       4. 完成后说：'任务完成。请切换回 Conductor。'」
```

### 目标 Agent 执行

```
Agent（{role} persona）执行：

1. 读 TASK_BOARD.md
   ├── 「Agent 启动协议」段 → 逐条打勾
   ├── 「任务状态」表 → grep 自己角色的 🟢就绪 行
   ├── 「当前状态快照」 → Git HEAD / 脏文件
   └── 「上下文传递」表 → grep 自己 T-ID 的行

2. 读上游产出物（按需）

3. 执行任务
   ├── 按铁律 Ⅱ TDD: Red → Green → Refactor
   ├── 按角色合约的职责和禁止事项
   └── 如遇 Bug → 创建 BUG-NNN.md

4. 更新 TASK_BOARD
   ├── 「任务状态」表 → 🔨→✅
   ├── 「上下文传递」表 → 写给下游
   └── 「审查结果」表（如果是审查官）→ 记录判决+要点

5. 发出完成信号：「任务完成。请切换回 Conductor。」
```

### 切换回 Conductor

```
Agent（切换回 Conductor persona）：

1. 读 TASK_BOARD.md
   ├── 「Conductor 调度状态」 → 了解刚才做了什么
   ├── 「任务状态」表 → 确认任务结果
   └── 「审查结果」表（如果有）→ 确认审查结果

2. 更新 TASK_BOARD
   ├── 「派发日志」 → 追加完成行
   └── 「Conductor 调度状态」 → 更新为「就绪，等待下一步」

3. 写 Event → echo TASK_STATUS_CHANGED >> events.jsonl

4. 按调度循环决定下一步（见 Workflow Protocol「五、Conductor 调度循环」）
```

---

## 为什么需要 TASK_BOARD 的 4 个新段

| 段 | Tier 1/2 替代品 | Tier 3 没有它会怎样 |
|----|----------------|-------------------|
| **审查结果** | subagent return value → Conductor 上下文 | 角色切换后报告内容丢失。Dev 拿到 🔄返工 但不知道为什么 |
| **Conductor 调度状态** | Conductor 自身的"思维" | 切换回来时忘记派发过谁 |
| **派发日志** | subagent 自动回传状态 | 无法审计调度轨迹 |
| **Agent 启动协议** | subagent context 自动注入 | 新 persona 空上下文，不知道从哪开始 |

---

## 局限性

| 局限 | 说明 | 缓解 |
|------|------|------|
| 串行执行 | 无法并行派发多个 Agent | 按优先级排队 |
| Token 爆炸 | Conductor + 所有角色共享上下文窗口 | 每个 Agent 完成后立即精简上下文；超长任务拆分会话 |
| 状态链断裂 | Agent 忘记切换回 Conductor | TASK_BOARD「Conductor 调度状态」作为恢复锚点 |
| 上下文污染 | 角色 A 的推理残留在角色 B 的上下文中 | 切换时显式指令：「忘记之前的角色，你现在是 {new_role}」 |

---

## 禁止事项

- ❌ 在 Tier 1/2 可用时使用此模式
- ❌ Agent 执行后不写 TASK_BOARD（角色切换后信息丢失）
- ❌ Conductor 切换回来后不读 TASK_BOARD（凭记忆决策）
- ❌ 跳过 Agent 启动协议 Checklist
