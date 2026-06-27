# 元锻造铁律 (Iron Rules)

> **YuanForge 的根本法则** — 所有 Agent 在任何项目、任何阶段都必须遵守。
> 铁律不是建议，是不可违反的底线。违反铁律的产出视为无效。

---

## 🔨 七条铁律

### Ⅰ. 计划先行 (Plan First)

> 没有 Plan，不写一行代码。

- 任何功能开发 **必须** 先产出 Implementation Plan
- Plan 必须包含：目标、架构、文件清单、分步任务、测试策略
- Plan **必须** 通过审查后才能进入实现阶段
- 禁止「边写边想」

**反例：** "我先写起来，写到哪算哪" ❌  
**正例：** "先写好 Plan，确认后再实现" ✅

---

### Ⅱ. TDD 先行 (Test First)

> 先写失败的测试，再写通过的代码。

- 每个 Task 的流程必须是：Red → Green → Refactor
  1. 写测试（红灯 — 测试失败）
  2. 写最小实现（绿灯 — 测试通过）
  3. 重构（保持绿灯）
- 测试必须在提交前全部通过
- 不允许「先写代码，后补测试」

**反例：** "功能写完了，现在补几个测试" ❌  
**正例：** "先写测试用例，再写实现代码" ✅

---

### Ⅲ. 两阶段审查 (Two-Stage Review)

> 每段代码经过两道门：Spec 审查 → Quality 审查。

- **Stage 1 — Spec Compliance Review：** 实现是否符合 Plan 中定义的需求？
  - 检查：功能完整性、文件路径、接口签名、行为预期
  - 输出：`PASS` 或具体差距列表
  
- **Stage 2 — Code Quality Review：** 代码质量是否过关？
  - 检查：代码规范、错误处理、命名、测试覆盖、安全性
  - 输出：`APPROVED` 或具体问题列表

- 两阶段 **必须按序执行**，Stage 1 未 PASS 不得进入 Stage 2
- 审查不通过 → 修复 → 重新审查 → 直到通过

---

### Ⅳ. 原子提交 (Atomic Commits)

> 一个 Task = 一个 Commit。不混合无关改动。

- 每个 Task 完成后立即提交
- Commit message 遵循 Conventional Commits 规范：
  - `feat:` — 新功能
  - `fix:` — 修复 bug
  - `refactor:` — 重构（不改行为）
  - `test:` — 添加测试
  - `docs:` — 文档变更
  - `chore:` — 工具/配置变更
- 一个 Commit 只做一件事

**反例：** 一个 commit 包含「新增登录 + 改 CSS + 修 bug」❌  
**正例：** 三个独立 commit：`feat: add login endpoint` / `fix: button alignment` ✅

---

### Ⅴ. 上下文隔离 (Context Isolation)

> 每个实现 Task 用全新的 Agent，不受前面任务污染。

- 每个 Task 派一个全新的 Subagent
- 通过 Plan 传递上下文，**不依赖 Agent 记忆**
- 不同 Task 之间的状态隔离，互不干扰

**原理：** 新鲜大脑做新鲜事。累计的上下文会导致 Agent 产生偏差和幻觉。

---

### Ⅵ. 文档即代码 (Docs as Code)

> 架构决策、技术选型、术语定义必须落文档。不依赖口头传递。

- 架构变更 → 更新 `ARCHITECTURE.md`
- 技术决策 → 记录在 `DECISIONS.md`（ADR 格式）
- 新术语/概念 → 加入 `GLOSSARY.md`
- 文档和代码同步更新，同一个 Commit

**反例：** "我们上次讨论过用 Redis 做缓存，你知道的吧" ❌  
**正例：** `DECISIONS.md` 中有记录：「2026-06-27: 选择 Redis 作为缓存层，因为...」✅

---

### Ⅶ. 渐进式交付 (Incremental Delivery)

> 每个 Task 完成后，项目仍可运行。不允许积累大量未集成的代码。

- 每个 Task 的产出必须能独立运行/测试
- 不允许「先把所有模块写完，最后一起联调」
- 持续可演示、可验证

**反例：** "先写 10 个模块，最后一起集成" ❌  
**正例：** 写完一个模块 → 集成 → 测试 → 提交 → 下一个 ✅

---

### Ⅷ. 质量门禁 (Quality Gates)

> 每个 Phase 之间有明确的 Gate。Gate 不通过，禁止进入下一 Phase。

YuanForge 的 Pipeline 包含 **4 个硬性门禁**：

```
Phase 1: 架构           Phase 2: 执行           Phase 3: 收尾
─────────────────── G1 ─────────────────── G2 ─────────────────── G3 ──→ 交付
                                                        │
                                                        G4（全量回归）
```

| Gate | 位置 | 通过条件 | 不通过行为 |
|------|------|---------|-----------|
| **G1: Plan Gate** | Phase 1 → 2 | Plan 完整、task 粒度 ≤ 5 分钟、用户已确认 | 回 Phase 1 修改 Plan |
| **G2: Task Gate** | 每个 Task 之后 | Spec Review PASS + Quality Review APPROVED | Coder 修复 → 重新审查（最多 3 轮，超过则触发架构复盘） |
| **G3: Integration Gate** | Phase 2 → 3 | 所有 Task 完成、全量测试 PASS、无未处理 Issue | 回 Phase 2 修复 |
| **G4: Release Gate** | Phase 3 → 交付 | 集成测试 PASS、CI 通过、文档已更新 | 回 Phase 3 补充 |

**门禁铁律：**

- Gate 不通过，绝对不允许跨越
- G2 同一 Task 连续 3 次审查不通过 → **必须** 触发架构复盘（找 Architect 重新评估 Plan），而非无限循环
- Gate 状态必须可见 — 每个 Gate 通过后在 Plan 中标注 `[G1 ✓]`
- 快速模式下 G2 只执行 Quality Review，G3/G4 可选

---

## 📋 每个开发周期的检查清单

Agent 在开始任何开发任务前，必须逐条确认：

- [ ] Ⅰ. 是否有 Implementation Plan？
- [ ] Ⅱ. 是否写了先失败的测试？
- [ ] Ⅲ. Spec Review 是否 PASS？
- [ ] Ⅲ. Quality Review 是否 APPROVED？
- [ ] Ⅳ. 每个 Task 是否对应独立 Commit？
- [ ] Ⅴ. 是否用了全新 Subagent 执行 Task？
- [ ] Ⅵ. 如有架构决策，是否已更新文档？
- [ ] Ⅶ. Task 完成后项目是否仍可运行？
- [ ] Ⅷ. 当前 Gate 是否已通过？（G1→G2→G3→G4）

**所有项打勾，才能进入下一个 Task。**

---

## ⚡ 快速模式 vs 严格模式

| 场景 | 模式 | 规则 |
|------|------|------|
| 原型验证 / 探索 | **快速模式** | 放宽 Ⅲ（审查）、Ⅳ（提交）、Ⅷ（只保留 G1+G2-Quality） |
| 正式开发 | **严格模式** | 八条铁律全开，G1→G2→G3→G4 全部硬性门禁 |

**切换方式：** 在需求描述中声明 `@快速模式` 或 `@严格模式`（默认严格模式）。

---

> *铁律不是束缚，是自由。它让每个 Agent 在任何项目中都能产出可靠、可维护的代码。*
