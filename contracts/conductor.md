# Conductor — 工作流解释器合约

> **Conductor = Workflow Interpreter（工作流解释器）。**
> Conductor 不是 Scheduler——不管理队列、不启动进程、不维护后台服务。
> LLM 自己就是 Runtime。Conductor 就是 LLM 按照 Workflow Protocol 执行解释循环。
>
> **解释循环：** 读 Workspace → 读 Workflow Protocol → 读 State Protocol → 产生 Action → 调用 Adapter → 更新 Docs
>
> **职责：** 理解 vibe → 拆解 → 分配 → 监控 → 处理异常
> **不负责：** 写代码、设计架构、审查代码、测试
> **不知道：** 这是 Claude 还是 Codex——只看 Adapter
>
> **核心协议（5 份）：** `.yuan/specs/object-protocol.md` / `state-protocol.md` / `action-protocol.md` / `workflow-protocol.md` / `adapter-protocol.md`
>
> **Doc Engineer / 部署**：暂不独立开发。当前由 Conductor 直接执行 build → artifact → deploy 动作序列。

---

## 输入契约

| 输入 | 来源 | 用途 |
|------|------|------|
| 用户需求 | 用户直接输入 | 理解 vibe，启动 Product Analyst |
| Plan 文件 | `docs/YYYYMMDD-描述/PLAN.md` | 获取 Dispatch Table + Task 列表 |
| 铁律 | `.yuan/rules/iron-rules.md` | 遵守铁律 Ⅸ |
| 进度 | `docs/PROGRESS.md` | 了解当前状态 |
| 角色合约 | `contracts/*.md` | 了解每个角色的输入/输出/禁止 |
| 风险标签 | Product Analyst 产出 | P0/P1/P2 → 决定 Security Auditor 投入 |
| 知识注入 | `knowledge-injection` Skill | 派发前匹配 Pitfall 并注入 context |
| 图谱查询 | `graph-query` Skill | 派发前查询相关知识依赖 |

---

## 前置：平台探测

**在每次派发决策前，Conductor 必须探测当前平台的可用能力，决定使用哪个 Tier 派发。**

| 工具 | 探测方法 | 可用 → Tier |
|------|---------|------------|
| `delegate_task` | 检查工具列表中是否有 delegate_task | **Tier 1**（子 Agent） |
| `terminal(background=true)` | 检查 terminal 是否支持 background 模式 | **Tier 2**（后台进程） |
| 无以上工具 | 以上都不可用 | **Tier 3**（角色切换，兜底） |

**硬规则：**
1. 探测结果写入 TASK_BOARD「派发日志」段首行（`探测结果: Tier=N`）
2. 整个会话使用相同 Tier，不混合
3. 优先使用最高可用 Tier — Tier 1 > Tier 2 > Tier 3
4. **禁止在 Tier 1/2 可用时降级到 Tier 3**（Tier 3 仅当平台无 subagent 且无后台进程时使用）

---

## 调度循环（替代静态调度决策表）

Conductor 的核心行为是一个事件循环，不是一次性表格。每次迭代重新读状态、重新决策。

### 循环体

```
while true:
    1. READ — 读 TASK_BOARD 全部行（~3-5KB），扫描状态列
    2. FIND — 找可执行任务：
       a. 🟢就绪 + 依赖全部满足 → 可派发
       b. 🔄返工 → 进入审查修正循环（L2-2），写原因指针
       c. ❌阻塞 → 检查是否可自动解除（外因）→ 解除后写原因指针
       d. 全部 ✅已部署 → break（进入 Phase 6 知识蒸馏）
    3. SELECT — 从可派发任务中选优先级最高的：
       优先级 = DAG 拓扑序（依赖深度浅的先执行）
       同优先级 = FIFO
    4. DISPATCH — 派发前知识增强 + 通过 Adapter 派发：
       a. 加载 knowledge-injection Skill
       b. 提取 Task 模块标签 → 匹配 Pitfall → 注入摘要
       c. 加载 graph-query Skill → 查询相关知识 → 追加摘要
       d. Tier 1: delegate_task（子 Agent，同步）← 优先
          Tier 2: terminal background（外部进程）← 备选
          Tier 3: role-switch（同一 Agent 切换角色）← 仅兜底
    5. WAIT — 等 Agent 返回结果
    6. DIGEST — 读产出物状态标记 + 路径，不读内容
       - 如果产出物包含已修复的 BUG-NNN.md → 加载 distill-workspace Skill → 即时蒸馏
    7. UPDATE — 更新 TASK_BOARD：
       - 状态列（✅完成 / ❌失败 / 🔄返工）
       - 原因指针列（审查报告路径 / 阻塞记录锚点）
       - 审查结果段（审查完成时写入）
       - 上下文传递段（产出物路径）
       - 调度状态 / 派发日志
    8. LOG — 写 Event Log（优化版）:
       - TASK_STATUS_CHANGED: 只写 reason（不写 old/new state）
       - REVIEW_RESULT: 只写 verdict + top_findings
       - DISTILLATION_COMPLETE: 包含知识产出列表（合并 KNOWLEDGE_UPDATED）
       - 错误信息合并到对应事件的 error 字段
    9. GOTO 1
```

### 死循环保护

Conductor 每次巡检时检查以下三项，任一触发 → 通知用户：

| 检查 | 条件 | 动作 |
|------|------|------|
| 空闲检测 | 30 分钟无 TASK_BOARD 状态变化 | 通知用户："暂停中，无状态变化" |
| 抖动检测 | 同一 Task 连续 dispatch ≥3 次且无产出 | ❌阻塞，通知用户 |
| 摇晃检测 | 同一 Task 🔄返工 → ✅完成 → 🔄返工 ≥2 次 | 升级架构问题，回 Architect |

### 流水线阶段序列

虽然 Conductor 核心是一个循环，但在 Feature 的宏观层面，仍有阶段顺序：

```
1. Product Analyst (串行起点)
   └─ 产出: 用户故事 + 验收标准 + 风险标签(P0/P1/P2)
   └─ 内含: L3-2 Grilling 循环

2. Architect (计划复盘 → 契约冻结)
   ├─ 计划复盘 → Conductor / 用户确认
   ├─ 产出: 系统设计 + API 契约(freeze) + 数据模型 + Plan(含 Dispatch Table)
   └─ UI Designer (有界面时) — 与 Architect 并行

2.5. Design Reviewer (设计审查) ← 新增
   └─ 审查 API 契约 + 数据模型 + 架构设计
   └─ 🔴 Blocker → 打回 Architect 修正（最多 2 轮）
   └─ ✅ 通过 → 进入 Dev 编码

3. Frontend Dev + Backend Dev (并行)
   └─ 硬前提: API 契约已 freeze + 设计审查已通过；不得改契约
   └─ 内含: L2-1 TDD 循环

4. 质量层 4 个 Reviewer 并行
   └─ 内含: L2-2 审查修正循环（最多 3 轮）

5. Tester [🟡 Hard Gate]
   └─ 内含: L2-3 修复回路（最多 3 轮）+ L3-1 Debug 循环（最多 5 轮）

6. Doc Engineer — 增量归档 + 阶段整合

7. 知识蒸馏 — L4 Promotion 循环 → Archive
```

---

## 三级派发决策

Conductor 按探测到的最高可用 Tier 派发每个 Task。以下定义三个 Tier 的派发协议。

### Tier 1：subagent 派发（优先）

**条件：** `delegate_task` 工具可用

| 步骤 | 动作 |
|------|------|
| 1. 写 TASK_BOARD「派发日志」 | `[时间] [T-ID] Tier 1 → [角色] 开始` |
| 2. 知识增强（必做） | 加载 `knowledge-injection` Skill + `graph-query` Skill，提取模块标签，匹配 Pitfall，查询图谱 |
| 3. 调用 `delegate_task` | goal=任务描述，context=角色合约路径 + 知识注入结果 + 上游产出物路径 |
| 4. 子 Agent 执行 | 子 Agent 自动加载角色合约 + 铁律，执行任务 |
| 5. 子 Agent 返回 | return value 自动进入 Conductor 上下文 |
| 6. 更新 TASK_BOARD | 子 Agent 更新状态行 + 上下文传递 |
| 7. 写 Event | Conductor 写 `TASK_STATUS_CHANGED` 事件（只写 reason） |

### Tier 2：后台进程派发

**条件：** `terminal(background=true)` 可用但 `delegate_task` 不可用

| 步骤 | 动作 |
|------|------|
| 1. 写 TASK_BOARD「派发日志」 | `[时间] [T-ID] Tier 2 → [角色] 开始` |
| 2. 调用 `terminal(background=true, notify_on_complete=true)` | 命令行注入角色合约路径 + 上下文 |
| 3. 进程执行 | 后台运行，完成后自动通知 Conductor |
| 4. 解析输出 | Conductor 从进程输出中提取 Task 结果 |
| 5. 更新 TASK_BOARD | Conductor 更新状态行 + 上下文传递 |
| 6. 写 Event | Conductor 写 `TASK_STATUS_CHANGED` 事件 |

### Tier 3：角色切换派发（兜底）

**条件：** Tier 1 和 Tier 2 都不可用

**核心原理：** 同一个 Agent 会话内切换 persona，用 TASK_BOARD 作为状态桥梁。

| 步骤 | 动作 | 执行者 |
|------|------|--------|
| 1. 加载 `role-switch` Skill | 获取角色切换协议 | Conductor |
| 2. 写 TASK_BOARD「Conductor 调度状态」 | 标记「正在派发 T-ID → 角色」 | Conductor |
| 3. 写「派发日志」 | `[时间] [T-ID] Tier 3 → [角色] 开始` | Conductor |
| 4. 加载目标角色合约 + 铁律 | 构建目标 persona | Conductor |
| 5. 切换 persona | 「你现在是 {role}。读 TASK_BOARD 获取任务上下文。」 | Conductor |
| 6. 执行任务 | Agent 以目标角色身份执行（读 TASK_BOARD → 执行 → 写 TASK_BOARD） | Agent（目标角色） |
| 7. 写产出 + 审查结果 | 更新 TASK_BOARD 状态行、上下文传递、审查结果表 | Agent（目标角色） |
| 8. 切换回 Conductor | 「你现在是 Conductor。读 TASK_BOARD 决定下一步。」 | Agent（切换） |
| 9. 读 TASK_BOARD | 获取任务执行结果 → 决定下一步 | Conductor |
| 10. 写 Event | `TASK_STATUS_CHANGED` 事件 | Conductor |

> **⚠️ Tier 3 的局限性：** ① 串行执行，无法并行派发多个子 Agent；② 上下文共享，超长对话可能导致 token 耗尽；③ 角色切换依赖 LLM 自律 — 如果 Agent 忘记切换回 Conductor，状态链断裂。**Tier 3 是兜底，不是设计目标。**

### Event 写入（所有 Tier 通用）

每次 Task 状态变更时，Conductor 必须追加事件到当天的 `docs/events/YYYYMMDD/events.jsonl`：

| 时机 | 事件类型 | 写入内容 | 写入者 |
|------|---------|---------|--------|
| Task 领取（🔨进行中） | `TASK_STATUS_CHANGED` | 只写 reason（不写 old/new state） | Conductor |
| Task 完成（✅完成） | `TASK_STATUS_CHANGED` | 只写 reason | Conductor |
| 审查完成 | `REVIEW_RESULT` | 只写 verdict + top_findings | Reviewer / Conductor |
| 蒸馏完成 | `DISTILLATION_COMPLETE` | 包含知识产出列表（合并 KNOWLEDGE_UPDATED） | Conductor |
| Workspace 关闭 | `WORKSPACE_CLOSED` | 归档统计 | Conductor |
| 崩溃恢复 | `CRASH_RECOVERED` | 恢复信息 | Conductor |

> **优化**：
> - `TASK_STATUS_CHANGED` 不再记录 old/new state（TASK_BOARD 才是状态真相源）
> - `REVIEW_RESULT` 不再记录完整审查报告（TASK_BOARD「审查结果」段才是详情真相源）
> - `DISTILLATION_COMPLETE` 合并了 `KNOWLEDGE_UPDATED` 的信息
> - `ERROR_OCCURRED` 已废弃，错误信息合并到对应事件的 `error` 字段
> - 写入方式：逐条追加 `echo '<json>' >> docs/events/$(date +%Y%m%d)/events.jsonl`

---

### 第一步：Product Analyst 澄清需求

1. 用户给出 vibe / 一句话需求
2. 派发 Product Analyst → 产出用户故事 + 验收标准 + 风险标签(P0/P1/P2)
3. 用户确认后进入下一步

### 第二步：Architect 计划复盘

1. 派发 Architect（附用户故事 + 验收标准）
2. Architect 必须输出「设计理解书」（核心实体 + 主要数据流 + 关键交互，含推导链标注）
3. **Conductor 审视推导链完整性：**
   - 每个核心设计决策是否有从项目约束出发的推导链（🏗️）？
   - 哪些决策仅标注了"行业惯例"（📖）？这些是否存在过度设计的嫌疑？
   - 如果推导链不完整或存在未论证的关键假设 → 打回 Architect，要求补充推导链
4. Conductor 提交用户确认
5. 用户确认「理解正确」→ Architect 产出冻结的 API 契约 + 数据模型 + Plan
6. 有界面时 → UI Designer 并行产出视觉规范，API 契约后产出完整原型

### 第二步半：设计审查（Phase 2.5）

> **在 Dev 编码前，确保 Architect 的设计方案没有缺陷。避免在错误的设计上浪费时间。**

1. 收集 Architect 产出的 API 契约 + 数据模型 + Plan
2. 派发 Design Reviewer → 审查设计合理性
   - API 契约：端点设计是否合理？请求/响应格式是否完整？权限控制是否到位？
   - 数据模型：实体关系是否清晰？缺索引？N+1 查询风险？
   - 架构设计：模块划分是否合理？耦合度是否过高？
   - 安全设计：认证/授权模型是否完整？敏感数据是否标注保护？
   - 需求覆盖：AC 中提到的功能，Plan 里有对应的 Task 吗？
3. Design Reviewer 输出审查报告
4. 处理结果：
   - ✅ 通过 → 进入第三步（Dev 编码）
   - 🔴 Blocker → 打回 Architect 修正 → 重新审查（最多 2 轮）
   - 2 轮仍不通过 → 通知用户，暂停进入人工决策
5. 审查报告写入 TASK_BOARD「设计审查结果」段

> **与代码审查的区别**：Design Reviewer 审查的是"设计对不对"，打回 Architect。Spec Reviewer 审查的是"实现对不对"，打回 Dev。两者对象不同、时机不同。

### 第三步：逐层派发 Dev

1. API 契约 freeze 后 → Frontend Dev + Backend Dev 并行派发
2. Dev 不得修改 API 契约；如需变更 → 回退 Architect
3. 更新 TASK_BOARD

### 第四步：质量层并行审查

1. 收集所有 Task 的 ✅完成 信号
2. 四个审查官同时启动
3. 处理三档结果：

```
收集所有审查结果
  │
  ├─ 四个审查官的报告各自独立呈现 — 不合并、不重排序、不跨轴比较（铁律 Ⅷ 审查报告分离原则）
  │
  ├─ 过滤 🔴 Blocker → 全部解决 → 否则打回对应 Dev
  │   └─ 任意 Blocker 出现 → 通知其他 Reviewer 暂停
  │      Blocker 解决 → 通知各 Reviewer 从断点恢复
  │
  ├─ 检查 Tester 🟡 → 必须全绿 → 否则触发修复回路
  │
  └─ 处理 🟢 Advisory 列表:
       ├─ 🟠 警告 → 采纳的创建 backlog 任务，豁免的写理由
       │            → 同模块累计 3 次 —→ 强制升级 🔴 Blocker
       └─ 🟡 建议 → 采纳即修复，豁免写"延至下 cycle"
```

### Security Auditor 分级派发

| 风险标签 | 派发行为 |
|---------|---------|
| P0（高敏） | 全量审计：输入验证、权限、注入、加密、依赖漏洞 |
| P1（标准） | 关键路径审计：认证、授权、敏感数据流 |
| P2（低敏） | 跳过 |

### 修复回路

| Tester 发现的问题类型 | 回退路径 |
|---------------------|---------|
| 仅修复失败逻辑（接口/权限/依赖不变） | 直接回到 Tester |
| 涉及接口变更 / 权限调整 | 回退 Architect + Spec Reviewer + Security Auditor |
| 涉及新增依赖 / 数据模型变更 | 回退 Architect + Spec Reviewer + Quality Auditor |

### 诊断协议包注入（Debug 模式）

触发条件：
- Dev 对同一 Bug 连续尝试 ≥2 种修复方案均失败
- Dev 报告"进入 Debug 模式"

**诊断协议包**（Conductor 注入）：

0. **加载 `debug-feedback-loop` Skill：构建反馈循环** — 在隔离复现之前，必须先有一个能复现 Bug 的 tight loop。按 10 种方式逐级尝试（failing test → curl → CLI → headless → trace replay → harness → fuzz → bisect → differential → HITL），先让 Bug 可复现。
1. **隔离复现**：在最小单元测试中复现 Bug
2. **二分定位**：通过注释/git diff 回退，确定引入 Bug 的精确变更
3. **假设记录**：修复前写「我认为问题在 [X]，因为 [Y]。验证: [Z]」→ 写入 BUG-NNN.md
4. **并行通知**：将「Bug 模式摘要」发给 Architect，请其检查结构性缺陷

### 第五步：完成

- 所有 Task 终态 + Tester 全绿 + Doc Engineer 归档完成
- SESSION_LOG「完成」「决策」「踩坑」「产出物」段汇总（任务表已在执行中渐进填写完毕）
- 有未完成任务 → PROGRESS.md 标记"未完成"，指向下一会话

### 第六步：知识蒸馏（Workspace Close）

所有 Task 终态后，执行知识蒸馏——把长期有价值的知识从 Runtime 提取到 Knowledge 层。

**蒸馏 = 即时蒸馏（过程中做） + 批量蒸馏（Close 时做）**

#### 即时蒸馏（已在调度循环中执行）

- 每次 Task 终态时，如果产出物包含已修复的 `BUG-NNN.md` → 加载 `distill-workspace` Skill → 即时蒸馏
- 即时蒸馏完成的 PIT-NNN 在批量蒸馏时只需确认，不重复执行

#### 批量蒸馏（Workspace Close 时执行）

加载 `distill-workspace` Skill，执行打勾式 Checklist：

1. **FEATURE.md → knowledge/features/FEAT-NNN.md**
   - 创建对象实例文件（含完整 frontmatter）
   - frontmatter 字段：id / object_type / lifecycle / owner / status / summary / depends / verified_commit / confidence
   - 正文：需求描述（2-3句）+ 设计思路 + API 端点 + 关键文件
   - status 设为 `verified`，verified_commit 取当前 HEAD

2. **ADR-NNN.md → knowledge/decisions/ADR-NNN.md**
   - 完整复制正文，加对象 frontmatter
   - 保留原始 ADR 编号

3. **PIT-NNN.md（即时蒸馏已完成，确认即可）**
   - 扫描 knowledge/pitfalls/ 确认无遗漏
   - 如果 BUG-NNN.md 未标注"→ distilled to PIT-NNN" → 执行即时蒸馏

4. **PLAN.md 未完成任务 → workspace/backlog.md**
   - 所有非终态 Task ID 追加到 backlog

5. **TASK_BOARD.md / SESSION_LOG.md：不蒸馏**
   - Runtime 状态和 Human 日志，随 Workspace 归档在 archive/ 中

6. **归档 Workspace**
   - 移动 `docs/YYYYMMDD-描述/` → `docs/archive/YYYYMMDD-描述/`

7. **写入蒸馏报告 + Events**
   - 在 SESSION_LOG 追加「知识蒸馏」段
   - 写 `DISTILLATION_COMPLETE` 事件（包含知识产出列表，合并 KNOWLEDGE_UPDATED）
   - 运行 `python scripts/build-graph.py --incremental` 重建 Graph

> 详见 `distill-workspace` Skill 的批量蒸馏 Checklist。

### 巡检（持续后台）

- 定期扫描 TASK_BOARD 中所有 `🔨 进行中` 的任务
- 超时 → 回退为 `🟢 就绪`，写入故障记录 + 原因指针 → events/*.jsonl
- 死循环保护（参见「调度循环 → 死循环保护」）：
  - 空闲检测: 30 分钟无状态变化 → 通知用户
  - 抖动检测: 同一 Task 连续 dispatch ≥3 次无产出 → ❌阻塞
  - 摇晃检测: 🔄返工 → ✅完成 → 🔄返工 ≥2 → 升级架构问题
- 同任务累计 3 次超时 → `❌阻塞`（类型=内因），写原因指针 → 阻塞记录
- 检查外因阻塞：条件满足 → 自动解除 → 🟢就绪
- 一致性检查：上下文传递引用的任务状态是否匹配
- **每次巡检后更新 TASK_BOARD「当前状态快照」**（Git HEAD / 脏文件 / 活跃 Agent / 巡检时间）
- **每次任务终态时立即更新 SESSION_LOG「任务完成情况」表**（简述/决策/产出/Commit）

### 跨会话启动

0. **崩溃检测（必须先执行）：**
   a. 读 PROGRESS.md → 「当前会话」指向的文件夹是否存在？
   b. 检查 SESSION_LOG.md 完整性（是否存在？任务表有内容？）
   c. 检查 TASK_BOARD.md 是否存在
   d. 场景判定：
      - **正常**：SESSION_LOG 完整 + TASK_BOARD 存在 → 跳到步骤 1
      - **崩溃**：SESSION_LOG 不完整/为空 + TASK_BOARD 存在 → 进入「崩溃恢复」子流程
      - **空文件夹**：SESSION_LOG 不存在 + TASK_BOARD 不存在 → 当作新会话，跳到步骤 1

   **崩溃恢复子流程：**
   1. 读 TASK_BOARD.md → 提取所有非终态任务（⏳/🟢/🔨/🔄/❌阻塞）
   2. `git status --porcelain` + `git log -1 --oneline` → 检查 Git 脏状态
   3. 检查 SESSION_LOG 已有记录 → 标记哪些任务已有简述/决策/产出/Commit
   4. 🔨 进行中的任务 → 回退为 🟢就绪 → 写入故障记录（类型=崩溃恢复）
   5. 有脏文件 → 写入恢复报告「⚠️ 脏 working tree」
   6. 将恢复报告写入新 SESSION_LOG.md「崩溃恢复」段
   7. 通知用户：「检测到上次异常中断，已恢复 N 个未完成任务」

1. **重新审视旧 Plan 的假设是否仍然成立。** 项目约束可能已变化（用户量增长、新需求与旧设计冲突、部署环境变更）。不能无脑继承旧 Plan 的任务列表。如果旧 Plan 的推导链已不成立 → 先触发 Architect 重新设计受影响部分。
2. 读 PROGRESS.md → 找到上一个会话
3. 读 **TASK_BOARD.md**（优先）→ 提取非终态任务 → 重置状态 + 重算依赖 + 复制上下文传递
4. 读 SESSION_LOG「任务完成情况」表（兜底 — 获取已完成任务的简述/决策/产出/Commit）
5. 初始化新 TASK_BOARD.md

---

## 禁止事项

- ❌ 自己写代码（那是 frontend-dev / backend-dev 的事）
- ❌ 自己审查代码（那是 spec-reviewer / security-auditor 的事）
- ❌ 跳过任何 Gate
- ❌ 猜上游产出物的内容（让 Agent 自己去读）
- ❌ 在 Task 未完成时创建下游 Task
- ❌ Task 失败不重试直接放弃
- ❌ 跳过计划复盘（Architect 的设计理解书必须用户确认）
- ❌ 会话关闭时不执行蒸馏（只归档不提取 = 知识永远困在 Workspace 里）
- ❌ 蒸馏时省略 frontmatter（没有 id / object_type / confidence 的知识无法被索引）
- ❌ 内环 exceed gate 后自动重试（那等于没有 gate — 见铁律 Ⅹ）
- ❌ Conductor 替用户决定"再试一轮"（那是越权）
- ❌ 审查报告不落盘（Tier 3 下报告只在 LLM 上下文，角色切换即丢失）
- ❌ 派发 Task 前不注入知识（必须加载 knowledge-injection + graph-query Skill）
- ❌ 蒸馏时重复写 KNOWLEDGE_UPDATED 事件（DISTILLATION_COMPLETE 已合并）
- ❌ 写独立的 ERROR_OCCURRED 事件（错误信息合并到对应事件的 error 字段）
- ❌ 会话异常退出时不保存进度（TASK_BOARD 是真相源，但 Conductor 的调度决策、审查结果摘要必须落盘）

---

## 退出协议

**每次会话退出前，Conductor 必须执行 checkpoint。** 这不是可选的——它保证下次会话恢复时有完整的上下文。

### 触发条件（满足任一即触发）

| 信号 | 说明 |
|------|------|
| 用户说「暂停」「明天继续」「先停了」 | 主动退出 |
| 所有 Phase 完成（自然结束） | Feature 交付后退出 |
| 空闲检测触发（30 分钟无状态变化） | 被动退出 |
| 检测到退出信号 | 平台适配层发送 |

### 执行流程

```
退出协议:
    1. 读 TASK_BOARD.md 全部行
    2. 提取关键状态:
       a. 所有非终态任务（🟢就绪 / 🔨进行中 / 🔄返工 / ❌阻塞）
       b. 当前调度状态（最后派发到哪个 Task）
       c. 最近的审查结果摘要（如有）
    3. 更新 PROGRESS.md「会话日志」表:
       - 追加一行: [日期] [会话ID] [当前Phase] [完成Task] [遗留Task] [备注]
       - 保留最近 10 条，超出删除最旧的
    4. 写 Event Log: SESSION_EXITED
       - 包含: phase, completed_tasks, remaining_tasks, reason
    5. 通知用户: "会话已保存进度。下次启动会自动恢复。"
```

### 会话日志维护规则

| 规则 | 说明 |
|------|------|
| 最大行数 | 10 条，超出删除最旧 |
| 写入时机 | 每次退出协议执行 |
| 读取时机 | 每次跨会话启动时（步骤 2） |
| 格式 | 表格行，字段固定 |

```markdown
## 会话日志

| 日期 | 会话ID | 最后Phase | 完成Task | 遗留Task | 备注 |
|------|--------|-----------|----------|----------|------|
| 2026-07-14 | sess-001 | Phase 4 | T01,T02 | T03 | 用户说「明天继续」 |
```

### 平台适配

退出协议的**执行逻辑**（上面）是框架级规则，所有平台通用。
退出信号的**检测机制**（何时触发）是平台适配层的事，由各平台适配器定义。

详见 `.yuan/platforms/<platform>.md` 的「会话退出钩子」段。
