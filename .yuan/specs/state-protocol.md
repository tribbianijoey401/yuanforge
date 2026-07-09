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

## 三、Workspace 状态机（4 状态）

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
```

### 转换规则

| 从 | 到 | 条件 |
|----|-----|------|
| created | executing | Phase 1 开始（Product Analyst 启动） |
| executing | distilling | 所有 Task 终态 |
| executing | distilling | TTL 过期（强制蒸馏） |
| distilling | archived | 蒸馏完成 |

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

---

## 八、状态机铁律

| # | 规则 |
|---|------|
| 1 | 所有状态转换必须经过本文义的一条有效路径 |
| 2 | 禁止「跳跃」— 从 A 直接到 C 而跳过 B |
| 3 | 终态不可逆 — 已部署/已取消/已归档 不可回退 |
| 4 | 崩溃恢复不改变状态机定义 — 只将 🔨 回退到 🟢 |

---

## 九、与其他协议的关系

| 协议 | 依赖方式 |
|------|---------|
| Object Protocol | 定义了本文管理其状态的对象 |
| Action Protocol | Action 触发本文的状态转换 |
| Workflow Protocol | Workflow 决定何时触发哪个转换 |
| Adapter Protocol | Adapter 执行状态转换的具体动作 |
