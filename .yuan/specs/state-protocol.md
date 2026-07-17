# State Protocol — 状态协议

> **协议定位**：定义对象的状态如何变化。
> **本协议只定义「什么状态能变成什么状态」。**
>
> 不定义谁触发（那是 Workflow Protocol）、不定义怎么触发（那是 Action Protocol）、不定义具体怎么做（那是 Platform Adapter）。
>
> **铁律**：本协议不含任何 Prompt、不含任何实现指引。只有状态转换规则。

---

## 一、设计原则

```
State Protocol 不关心：
  - 谁执行转换
  - 怎么执行转换
  - 用什么工具

State Protocol 只关心：
  - 当前状态是什么
  - 允许变成什么状态
  - 转换条件是什么（如果有）
```

---

## 二、Task 状态机（11 状态）

```
                    ┌──────────┐
                    │ ⏳ 等待   │ ← 初始状态
                    └────┬─────┘
                         │ [依赖满足]
                         ▼
                    ┌──────────┐
          ┌────────│ 🟢 就绪   │←─────────────┐
          │        └────┬─────┘               │
          │             │ [Agent 领取]         │
          │             ▼                      │
          │        ┌──────────┐     [超时]     │
          │        │ 🔨 进行中  │──────────────┘
          │        └────┬─────┘
          │             │ [完成]
          │             ▼
          │        ┌──────────┐
          │   ┌───→│ ✅ 完成   │
          │   │    └────┬─────┘
          │   │         │ [审查]
          │   │    ┌────┴─────┐
          │   │    ▼          ▼
          │   │ ┌──────┐  ┌──────┐
          │   └─│🔄返工 │  │✅审查 │
          │     └──┬───┘  │ 通过  │
          │        │      └──┬───┘
          │        │         │ [测试]
          │        │         ▼
          │        │    ┌──────────┐
          │        │    │✅测试通过 │
          │        │    └────┬─────┘
          │        │         │ [部署]
          │        │         ▼
          │        │    ┌──────────┐
          │        │    │✅已部署   │  ← 终态
          │        │    └──────────┘
          │        │
          │   ┌────┴─────┐
          │   ▼          ▼
          │┌──────┐  ┌──────┐
          ││❌阻塞 │  │❌取消 │  ← 异常终态
          │└──────┘  └──────┘
          │
     [attempts ≥ 3]
          │
          ▼
     ┌──────────┐
     │ ❌ 阻塞   │
     └──────────┘
```

### 转换规则表

| 从 | 到 | 条件 |
|----|-----|------|
| ⏳等待 | 🟢就绪 | depends_on 全部终态 |
| 🟢就绪 | 🔨进行中 | Agent 领取 |
| 🔨进行中 | ✅完成 | Agent 完成工作 |
| 🔨进行中 | 🟢就绪 | 超时（attempts++） |
| 🟢就绪 | ❌阻塞 | attempts ≥ 3 |
| ✅完成 | ✅审查通过 | 审查通过 |
| ✅完成 | 🔄返工 | 审查不通过 |
| 🔄返工 | 🔨进行中 | 修复后重新执行 |
| 🔄返工 | ❌阻塞 | ≥3 次返工 |
| ✅审查通过 | ✅测试通过 | 测试全绿 |
| ✅测试通过 | ✅已部署 | 部署成功 |
| 任意非终态 | ❌取消 | 用户指令 |
| 🔨进行中 | 🟢就绪 | 崩溃恢复 |

### 终态

`✅已部署`、`❌取消` — 进入终态后不再变化。

---

## 三、Workspace 状态机（4 → 5 状态）

```
┌─────────┐     [Phase 1 开始]     ┌───────────┐
│ created  │ ────────────────────→ │ executing  │
└─────────┘                       └─────┬─────┘
                                        │
                          ┌─────────────┤
                          │             │
                    [全部 Task 终态]   [TTL 过期]
                          │             │
                          ▼             ▼
                    ┌───────────┐
                    │distilling │
                    └─────┬─────┘
                          │ [蒸馏完成]
                          ▼
                    ┌───────────┐
                    │ archived  │  ← 终态
                    └───────────┘

附加状态（从 executing 分支）：

                    ┌───────────┐
                    │waiting_user│  ← 等待用户输入（非终态）
                    └─────┬─────┘
                          │ [用户响应]
                          ▼
                    ┌───────────┐
                    │ executing  │  ← 恢复执行
                    └───────────┘
```

### 转换规则

| 从 | 到 | 条件 |
|----|-----|------|
| created | executing | Phase 1 开始（Product Analyst 启动） |
| executing | distilling | 所有 Task 终态 |
| executing | distilling | TTL 过期（强制蒸馏） |
| distilling | archived | 蒸馏完成 |
| executing | waiting_user | 触发 Human Gate（用户确认/权限/架构冻结等） |
| waiting_user | executing | 用户响应后重新启动 Loop（非恢复，是新 Loop） |
| waiting_user | distilling | TTL 过期（强制蒸馏，保留未完成任务到 backlog） |

---

## 四、Knowledge 对象状态机

### Feature

```
draft → designed → implemented → verified → deprecated
            ↑          │             ↑
            └──────────┘             │
            (返工)                    │
                          (重新验证)   │
                                     │
                          ┌──────────┘
                          ▼
                      deprecated
```

| 从 | 到 | 条件 |
|----|-----|------|
| draft | designed | Architect 完成设计 |
| designed | implemented | Dev 完成实现 |
| designed | draft | 设计被否决 |
| implemented | verified | 审查通过 + 测试通过 |
| implemented | implemented | 返工重做（version 递增） |
| verified | deprecated | 功能废弃 |
| verified | implemented | 重新实现 |

### Decision / ADR

```
proposed → accepted → deprecated
                ↓
           superseded
```

| 从 | 到 | 条件 |
|----|-----|------|
| proposed | accepted | 决策采纳 |
| accepted | deprecated | 不适用 |
| accepted | superseded | 被新 ADR 取代 |

### Pitfall

```
active → resolved → archived
   ↑        │
   └────────┘ (再次触发)
```

| 从 | 到 | 条件 |
|----|-----|------|
| active | resolved | 陷阱已修复 |
| resolved | active | 陷阱重新出现 |
| resolved | archived | 不再相关 |

### Module

```
active → deprecated
```

---

## 五、Proposal 状态机（5 状态）

```
draft → submitted → merged
              ├──→ rejected
              └──→ expired
```

| 从 | 到 | 条件 |
|----|-----|------|
| draft | submitted | 提交 |
| submitted | merged | 合并到 Knowledge |
| submitted | rejected | 被拒绝 |
| submitted | expired | 7 天未处理 |

---

## 六、Snapshot 状态机（4 状态）

```
executing → checkpoint → executing (恢复)
executing → completed
executing → failed
```

---

## 七、Checkpoint 状态机（2 状态）

```
created → archived
```

### Checkpoint 数据结构（Loop Engineering）

Checkpoint 记录四类信息，永远保持几 KB 以内：

| 字段 | 说明 |
|------|------|
| `verified_facts` | 已验证事实（如"API 正常"、"Redis 连接池配置正确"） |
| `current_state` | 当前状态快照（如"Task-17 RUNNING"） |
| `next_steps` | 下一步（如"等待 Reviewer"、"执行 TDD Red"） |
| `failed_hypotheses` | 已失败假设（见下方生命周期） |

### 失败假设生命周期

```
ACTIVE
  ↓ [已验证不正确]
VERIFIED_FALSE
  ↓ [蒸馏到 knowledge/]
DISTILLED
  ↓ [归档]
ARCHIVED
```

**规则**：
- Checkpoint 只保留 `ACTIVE` 状态的假设（当前仍在怀疑的）
- 假设一旦 `VERIFIED_FALSE`，立即蒸馏到 `knowledge/pitfalls/` 或留在当前 Checkpoint 的 `failed_hypotheses` 段
- `DISTILLED` 状态的假设从 Checkpoint 中删除，不再占用空间
- `ARCHIVED` 状态的假设随 Workspace 归档

**目的**：LLM 最容易重复犯同一个错误。Checkpoint 记录失败假设，下次恢复时不会重新走上同一条死路。

---

## 八、状态机铁律

| # | 规则 |
|---|------|
| 1 | 所有状态转换必须经过本文义的一条有效路径 |
| 2 | 禁止「跳跃」— 从 A 直接到 C 而跳过 B |
| 3 | 终态不可逆 — 已部署/已取消/已归档 不可回退 |
| 4 | 崩溃恢复不改变状态机定义 — 只将 🔨 回退到 🟢 |

---

## 十、循环约束

### 审查修正循环

| 从 | 到 | 条件 | 闸门 |
|----|-----|------|------|
| ✅完成 | 🔄返工 | 审查不通过 | iteration ≤ 3 |
| 🔄返工 | 🔨进行中 | 修复后重新执行 | iteration ≤ 3 |
| 🔄返工 | ❌阻塞 | iteration > 3 | escalate_to_user |

### 修复回路

| 从 | 到 | 条件 | 闸门 |
|----|-----|------|------|
| ✅审查通过 | 🔄返工 | 测试失败 | iteration ≤ 3 |
| 🔄返工 | 🔨进行中 | 修复后重新执行 | iteration ≤ 3 |
| 🔄返工 | ❌阻塞 | iteration > 3 | escalate_to_user |

### Debug 循环

| 从 | 到 | 条件 | 闸门 |
|----|-----|------|------|
| 🔨进行中 | 🔨进行中 | 进入 Debug 模式 | iteration ≤ 5 |
| 🔨进行中 | ❌阻塞 | iteration > 5 | 标记 known issue，跳过此 Task |

### 死循环保护

| 触发条件 | 动作 |
|---------|------|
| 30 分钟无 TASK_BOARD 状态变化 | 通知用户 |
| 同一 Task 连续 dispatch ≥3 次且无产出 | ❌阻塞，通知用户 |
| 同一 Task 🔄返工 → ✅完成 → 🔄返工 ≥2 次 | 升级架构问题，回 Architect |

---

## 十一、原因指针

每个非终态的 Task 状态必须携带**原因指针**（Cause Pointer）——指向 docs/ 中的原始证据，不是 LLM 摘要。

| Task 状态 | 原因指针指向 | 证据文件 |
|----------|-------------|---------|
| 🔄返工 | TASK_BOARD::审查结果 段 | `workspace/审查报告/T{id}-review-{role}-r{round}.md` |
| ❌阻塞(内因) | TASK_BOARD::阻塞记录 段 | TASK_BOARD.md §阻塞记录 |
| ❌阻塞(外因) | TASK_BOARD::阻塞记录 段 + 外因描述 | — |
| 🔨超时回退 | events/*.jsonl | 最近 `TASK_STATUS_CHANGED` 事件（DISPATCH 类型） |
| 🟢就绪 | TASK_BOARD::上下文传递 段 | 上游产出物文件路径 |

Agent 启动时：
1. 读自己 Task 行的「原因指针」列
2. 顺着指针加载证据文件
3. 自行理解原因（不依赖 LLM 摘要）
4. 决定行动

**原则：Conductor 不转述，只导航。**

---

## 十二、与其他协议的关系

| 协议 | 依赖方式 |
|------|---------|
| Object Protocol | 定义了本文管理其状态的对象 |
| Action Protocol | Action 触发本文的状态转换 |
| Workflow Protocol | Workflow 决定何时触发哪个转换 |
| Adapter Protocol | Adapter 执行状态转换的具体动作 |
