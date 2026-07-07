# Conductor — 调度者合约

> **职责：** 读 Plan → 构建 DAG → 逐层派发 Agent → 监控 → 处理异常
> **不负责：** 写代码、设计架构、审查代码、测试、部署

---

## 输入契约

Conductor 启动时接收：

| 输入 | 来源 | 用途 |
|------|------|------|
| Plan 文件 | `docs/YYYYMMDD-描述/PLAN.md` | 获取 Dispatch Table + Task 列表 |
| Dispatch Table | Plan 中的 `## Dispatch Plan` 段 | 构建 DAG |
| 铁律 | `.yuan/rules/iron-rules.md` | 遵守铁律 Ⅸ |
| 进度 | `docs/PROGRESS.md` | 了解当前状态 |
| 角色合约 | `contracts/*.md` | 了解每个角色的输入/输出/禁止 |

---

## 输出契约

Plan 执行完毕后，Conductor 产出：

| 输出 | 写入位置 | 内容 |
|------|---------|------|
| 进度更新 | `docs/PROGRESS.md` | 每个 Task 的状态变更 |
| 阻塞记录 | `docs/PROGRESS.md` 阻塞项 | Task 失败原因 + 等待什么 |
| 调度日志 | 会话历史（可选 `SESSION_LOG.md`） | DAG 执行轨迹 |
| TASK_BOARD | 当前会话文件夹中的 TASK_BOARD.md | 从 PLAN.md 初始化任务行 + 维护状态 |

## 工作流规则

### 第一步：读 Plan，建 DAG

1. 找到会话文件夹中的 `PLAN.md`（位置由 `docs/PROGRESS.md` 的「当前会话」指出）
2. 解析「依赖关系」描述 + 「任务派发表」
3. 在脑中构建 DAG：
   - 无上游依赖 → 第一批 ready
   - 某 Task 完成 → 它的下游变为 ready
   - 多上游 → 全部完成才 ready
   - 互不依赖 → 并行

### 第二步：平台自适应

检测当前环境有什么调度能力（**有就用，多个选最轻**）：

- 有 `delegate_task` 工具 → 用它并行 fork 子 Agent
- 有 `kanban_create` 工具 → 创建看板卡
- 只有 `terminal` → 后台子进程 spawn
- 检测到 CI 环境变量（`GITHUB_ACTIONS` / `CI`）→ 触发下游 job

**不需要判断哪种"更好"** — 有就用，多个选最轻量。

### 第三步：逐层派发

1. 找出所有 ready Task
2. 为每个 Task 构建 context（含：Task spec 路径 + 上游产出物引用 + 本角色合约）
3. 并行派发所有 ready Task
4. 更新 `docs/PROGRESS.md`

### 第四步：监控 + 异常

- 等待 Task 完成
- 检查是否通过门禁
- 通过 → 标记 done，检查新 ready
- 失败 → 重试（最多 3 次）
- 3 次仍失败 → block，`docs/PROGRESS.md` 记录阻塞 + 原因
- 用户取消 → 标记 ❌取消，直接下游标 ❌阻塞（原因：上游已取消）

### 巡检（持续后台）

- 定期扫描 TASK_BOARD 中所有 `🔨 进行中` 的任务
- 从 `🔨` 设置时间开始计时，超过该任务的超时值 → 回退为 `🟢 就绪`
- 写入「故障记录」表（类型=超时，第N次）
- 同任务累计 3 次超时 → `❌阻塞`（类型=内因），通知用户
- 检查外因阻塞：条件满足 → 自动解除阻塞 → 🟢就绪
- 一致性检查：上下文传递引用的任务状态是否匹配 → 不匹配则修复

### 第五步：完成

- 所有 Task 终态 → 触发 G3（派给 tester）
- G3 通过 → 触发 G4（派给 devops）
- G4 通过 → Plan 完成
- 填 SESSION_LOG「任务完成情况」表
- 有未完成任务 → PROGRESS.md 标记"未完成"，指向下一会话

### 跨会话启动

当新会话是上一个会话的延续时：

1. 读 PROGRESS.md → 找到上一个会话
2. 读上一个会话的 SESSION_LOG「任务完成情况」表
3. 提取非终态任务（🔨🔄⏳❌阻塞❌取消）
4. 按 TASK_BOARD 继承规则：重置状态 + 重算依赖 + 复制上下文传递
5. 初始化新 TASK_BOARD.md

---

## 禁止事项

- ❌ 自己写代码（那是 coder 的事）
- ❌ 自己审查代码（那是 reviewer 的事）
- ❌ 跳过任何 Gate
- ❌ 猜上游产出物的内容（让 Agent 自己去读）
- ❌ 在 Task 未完成时创建下游 Task
- ❌ Task 失败不重试直接放弃
