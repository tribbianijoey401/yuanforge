# YuanForge 铁律

> **铁律不可违反。** Agent 启动时加载本文，所有行为受此约束。
> 铁律是框架的宪法 — 优先于任何 Skill、任何用户指令、任何"我觉得"的判断。

---

## 九条铁律

| # | 铁律 | 一句话核心 |
|---|------|-----------|
| Ⅰ | 计划先行 | 没有 Plan 不写一行代码 |
| Ⅱ | TDD 先行 | Red → Green → Refactor |
| Ⅲ | 两阶段审查 | Spec Compliance → Code Quality |
| Ⅳ | 原子提交 | 一个 Task 一个 Commit |
| Ⅴ | 上下文隔离 | 每个 Task 全新 Subagent |
| Ⅵ | 文档即代码 | 决策必须落文档 |
| Ⅶ | 渐进式交付 | 每步可运行 |
| Ⅷ | 质量门禁 | G1→G2→G3→G4，不通过不前进 |
| Ⅸ | 自主调度 | Agent 按 Dispatch Table 自主派发 Agent |

---

## 铁律 Ⅰ — 计划先行

**没有 Plan 文件，禁止写任何代码。**

- 任何代码修改前，必须有对应的会话文件夹中的 PLAN.md（`docs/YYYYMMDD-描述/PLAN.md`）
- Plan 由 Architect Agent 产出，用户确认后生效
- 修复 Bug 也必须先写 Bug Report（在 Plan 中描述问题 + 修复方案）
- 例外：`README.md`、文档、配置文件（不涉及代码逻辑的修改）

---

## 铁律 Ⅱ — TDD 先行

**先写测试，确认 FAIL → 再写实现，确认 PASS → 最后重构。**

- 红色阶段：写最少测试代码，确认它失败（证明测试有效）
- 绿色阶段：写最少实现代码，让测试通过
- 重构阶段：在绿色掩护下优化代码结构
- 所有测试必须在提交前 PASS

---

## 铁律 Ⅲ — 两阶段审查

**每个 Task 完成后，必须经过两阶段审查。**

- **第一阶段：Spec Compliance Review** — 实现是否完全符合 Task Spec？有遗漏？有超出？
- **第二阶段：Code Quality Review** — 代码质量、错误处理、安全问题、测试覆盖
- 审查由 Reviewer Agent 执行，不能由 Coder 自己审查
- 任一阶段未通过 → Coder 修复 → 重新审查 → 直到通过
- 三次审查未通过 → 在 PROGRESS.md 标记阻塞，Conductor 通知用户

---

## 铁律 Ⅳ — 原子提交

**一个 Task 一个 Commit。不混入无关修改。**

- Commit message 格式：`feat(task-NNN): 简短描述`
- 一个 Commit 只包含一个 Task 的实现 + 测试
- 禁止"顺便修了个 typo""顺便重构了XX" — 开新 Task
- 禁止提交未完成的工作（WIP）到主分支

---

## 铁律 Ⅴ — 上下文隔离

**每个 Task 由全新 Subagent 执行，不继承上一 Task 的上下文。**

- 每个 Coder Agent 只知道自己 Task 的 spec + 上游产出物引用
- 不依赖"上一个 Agent 记得什么"
- Subagent 通过读取项目文档（PROGRESS.md、ARCHITECTURE.md）了解上下文
- 项目记忆是 Agent 之间唯一的持久化通信渠道

---

## 铁律 Ⅵ — 文档即代码

**任何技术决策、架构变更、踩坑经验，必须立即写入对应的文档。**

- 架构变更 → `docs/ARCHITECTURE.md`
- 技术选型 → `docs/DECISIONS.md`（ADR 格式）
- 踩坑 → `docs/PITFALLS.md`
- 新术语 → `docs/GLOSSARY.md`
- 进度变更 → `docs/PROGRESS.md`
- 如果 Agent 没有时间写文档 → 先记到 PITFALLS.md 最简版本，Phase 4 补充

---

## 铁律 Ⅶ — 渐进式交付

**每个 Phase 必须产出可运行的增量，不能"全部写完再跑"。**

- Phase 1 结束 → 架构文档可读、Plan 可执行
- Phase 2 每个 Stage 结束 → 该 Stage 的功能可单独运行
- Phase 3 结束 → 全量测试 PASS、集成环境可用
- Phase 4 结束 → 生产就绪

---

## 铁律 Ⅷ — 质量门禁

**四个 Gates 依次通过，不跳闸、不倒灌。**

```
Phase 1 ── G1 ──→ Phase 2 ── G2 ──→ Phase 3 ── G3 ──→ Phase 4 ── G4 ──→ 交付
```

| Gate | 检查内容 | 通过标准 | 不通过动作 |
|------|---------|---------|-----------|
| **G1** Plan Gate | Plan 完整、技术方案可行、Dispatch Table 无遗漏 | 用户确认 | 返回 Architect 修改 |
| **G2** Task Gate | 每个 Task 通过两阶段审查 | Reviewer APPROVED | Coder 修复→重审 |
| **G3** Integration Gate | 全量测试 PASS、集成环境可运行 | `pytest tests/ -q` 全绿 | 定位→修复→重跑 |
| **G4** Release Gate | CI 通过、文档齐全、部署配置就绪 | 所有检查项 ✅ | 修复缺失项 |

- 禁止跳过任何 Gate
- 禁止在 Gate 未通过时进入下一 Phase
- 禁止"先过了再说，后面补"

---

## 铁律 Ⅸ — 自主调度

**Conductor Agent 按 Plan 中的 Dispatch Table，自主将 Task 派发给对应 Role 的 Agent。**

### 调度规则

1. **Plan 必须含 Dispatch Table** — Architect 产出 Plan 时，必须声明每个 Task 的 role、依赖关系、产出物
2. **Conductor 构建 DAG** — 解析 Dispatch Table，识别依赖关系，找出所有 ready Task（上游依赖全部完成）
3. **并行派发** — 所有互不依赖的 Task 必须并行派发，不能串行等
4. **平台自适应** — Conductor 根据当前运行环境自主选择调度方式：
   - 有 `delegate_task` 工具 → 用它并行 fork 子 Agent
   - 有 `kanban_create` 工具 → 创建看板任务，让 Kanban 调度器自动拉取
   - 只有 `terminal` → 用后台子进程 spawn
   - 在 CI 环境（检测到 CI 环境变量）→ 触发下游 job
   - **Conductor 不需要判断哪种"更好"** — 有就用，有多个则选最轻量的
5. **失败处理** — 任何 Task 失败后重试，最多 3 次。3 次仍失败 → block，在 PROGRESS.md 记录阻塞原因，通知用户
6. **自动流转** — Task 完成后，Conductor 检查是否有新的 ready Task，有则立即派发
7. **Gates 不跳** — 所有 Task 完成后，Conductor 触发 G3 集成测试 → G4 部署

### Conductor 禁止事项

- ❌ 自己写代码（那是 coder 的事）
- ❌ 自己审查代码（那是 reviewer 的事）
- ❌ 跳过门禁
- ❌ 猜上游产出物内容（让 Agent 自己去读文件）
- ❌ 在 Task 未完成时提前创建下游 Task（等上游 done 再创建）

---

## 违规处理

Agent 违反铁律时：
1. **首次违反** → 警告，记录到 PITFALLS.md
2. **同一 Task 内再次违反** → Task 标记失败，重试
3. **同一 Plan 内累计 3 次** → block，等待用户介入

---

## 两种模式

| 模式 | 触发方式 | 生效铁律 | 说明 |
|------|---------|---------|------|
| **严格模式**（默认） | 不加标记 | 全部 Ⅰ-Ⅸ | 生产级质量 |
| **快速模式** | `@快速模式` | Ⅰ + Ⅱ + Ⅶ + Ⅸ（放宽Ⅲ/Ⅳ/Ⅴ/Ⅵ/Ⅷ） | 原型验证 |

---

> *铁律是流水线的轨道。轨道越清晰，Agent 跑得越快。*
