# Goal Protocol — 意图层协议

> **协议定位**：定义 YuanForge 的意图层——用户为什么要做这件事。
> **Goal 是持久化的意图（Persistent Intent）。** 它不是命令，不是状态机，更不是调度器。
> 它只描述"成功的样子"。
>
> **铁律**：Goal 不参与调度、派发或状态机维护。Goal 的状态由其包含 Task 的状态纯函数推导。

---

## 一、设计第一性原理

```
Goal 回答的问题：
  为什么做？
  成功是什么样？
  什么时候停？
  什么情况下需要人类确认？

Goal 不回答的问题：
  谁来做？（那是 Workflow）
  怎么做？（那是 Adapter）
  现在轮到哪个 Task？（那是 Loop）
```

**协议最小化**：Goal 不是 Runtime 对象。Goal 只是 Task 的 `goal` 字段的逻辑分组。
所有 Goal 信息从 TASK_BOARD 推导，不单独存储 Goal 状态。

---

## 二、Goal 定义

Goal 由 Architect 在 Plan 中声明，写入每个 Task 的 `goal` 字段。

```yaml
# Plan 中的 Goal 声明（Architect 产出）
goal:
  id: "auth-module"
  summary: "实现用户认证与权限管理"
  verification:
    - "所有 API 测试通过"
    - "E2E 测试覆盖核心流程"
    - "安全审查无 Blocker"
  constraints:
    - "Go + Gin, React + TS"
    - "bcrypt 哈希, JWT 2h 过期"
    - "遵循 iron-rules"
  stop_conditions:
    - "Human Gate 触发"
    - "连续 3 次返工"
  parent: null          # 父 Goal ID，实现 Goal Stack
  priority: 1
```

### Goal 字段说明

| 字段 | 类型 | 必填 | 说明 |
|------|------|:---:|------|
| `id` | string | ✅ | Goal 唯一标识 |
| `summary` | string | ✅ | 一句话描述 Goal 意图 |
| `verification` | array | ✅ | 成功标准（可验证的检查点） |
| `constraints` | array | ✅ | 技术约束（语言/框架/安全要求） |
| `stop_conditions` | array | — | 停止条件（触发 Human Gate 的场景） |
| `parent` | string | — | 父 Goal ID（实现 Goal Stack 嵌套） |
| `priority` | int | — | 优先级（数字越小越优先） |

---

## 三、Goal 推导规则

> **Goal 是 Task 的逻辑分组，不是独立对象。**

### Goal 状态推导

| 推导 | 条件 |
|------|------|
| Goal DONE | 该 Goal 下所有 Task 均为终态（✅已部署 / ❌取消） |
| Goal ACTIVE | 至少一个 Task 处于非终态且非阻塞 |
| Goal BLOCKED | 至少一个 Task 为 ❌阻塞 且无阻塞解除条件 |
| Goal READY | 至少一个 Task 为 🟢就绪 |

**铁律**：禁止在任何代码或文件中维护 `Goal.state` 字段。Goal 状态必须每次从 Task 状态实时推导。

### Goal Stack（嵌套 Goal）

```
Goal G1 (parent=null, priority=1)
  ├─ Goal G1.1 (parent=G1, priority=2)
  │    └─ Task T01..T05
  └─ Goal G1.2 (parent=G1, priority=3)
       └─ Task T06..T10
```

- 子 Goal 完成 → 父 Goal 自动推进
- 父 Goal 取消 → 所有子 Goal 级联取消
- Conductor 按 `priority` 升序选择下一个 Goal 推进

---

## 四、Human Gate（人工授权点）

> **只有"会改变用户世界"的操作才需要人类显式确认。**

### 四级 Human Gate

| 级别 | 触发点 | 说明 |
|------|--------|------|
| **G1 需求确认** | Product Analyst 完成需求文档后 | 用户确认用户故事 + 验收标准 |
| **G2 计划确认** | Architect 完成设计并通过审查后 | 用户确认 Plan + API 契约 |
| **G3 高危操作** | 删除数据库/部署生产/清空文件等 | 用户显式授权 |
| **G4 目标完成** | Goal 达成，所有 Task 终态 | 用户决定下一步 |

### Human Gate 执行流程

```
1. Conductor 检测触发 Human Gate 的条件
2. 写 Checkpoint（冻结当前状态）
3. 暂停 Loop，通知用户："遇到人工确认点：[Gate 级别]，[原因]。请回复 '确认' 或 '修改'"
4. 等待用户自然语言授权
5. 用户回复后，Conductor 解析意图 → 继续或修改
6. 启动新的 Loop（不是恢复旧 Loop）
```

**铁律**：Conductor 遇到 Human Gate 必须暂停，不得自行决定继续。

---

## 五、与其他协议的关系

| 协议 | 依赖方式 |
|------|---------|
| Object Protocol | Goal 信息嵌入 Task 的 `goal` 字段，不独立定义 Goal 对象 |
| State Protocol | Goal 状态从 Task 状态推导，无独立状态机 |
| Workflow Protocol | Workflow 的每个 Phase 服务于 Goal 的验证标准 |
| Action Protocol | Action 不操作 Goal，只操作 Goal 下的 Task |
| Adapter Protocol | Goal 信息通过 Plan 传递给 Adapter，Adapter 不直接操作 Goal |
