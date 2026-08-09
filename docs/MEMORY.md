---
name: memory
title: Yuan Long-term Memory
description: 可复用的 Verified Finding、Pitfall、Preference 和 Convention
---

# Yuan Long-term Memory

本文件保存可复用的 Verified Finding、Pitfall、Preference 和 Convention，不保存完整聊天、角色推理或逐步事件。

## User Preferences

- Markdown 描述使用中文，Agent、Skill、References、Routing、Work 等 Technical Term 保持英文。
- Project Continuity 是最高优先级；必须保留长期 Project Memory、可读 Handoff、历史 Pitfall 和经验。
- `update` 的目的就是强制采用最新 Framework；不需要保留旧官方版本，只需保护 Project Memory、Override 与业务内容。
- 用户自然描述需求即可；Framework 应自动 Routing 到 Agent/Skill，不要求用户通过 Prompt 点名内部阶段、Agent 或 Skill。

## Pitfalls

### M-001：Framework Update 不得依赖旧 Runtime 健康

- **Symptom**：安装 Framework 本来用于修复问题，却先被 Version、Integrity 或旧 Runtime 检查阻断。
- **Cause**：让被替换对象参与新版本安装的准入判断。
- **Rule**：Source 外部 Installer 直接替换官方快照；更新后再做非回滚式 Check。

### M-002：优化不得删除已有有效专业内容

- **Symptom**：目录更干净，但 Agent Contract、Skill 方法和 Reference 知识变成空壳。
- **Cause**：把结构重构误当成从零重写。
- **Rule**：先建立 Content Inventory 和 Migration Matrix；通过 Content Preservation Test 保护代表性章节和资产数量。

### M-003：Template 与 Project Document 必须分层

- **Symptom**：Framework Template 被当作当前 Project Fact，或 Project 的修改被 Update 覆盖。
- **Cause**：Template、Vendored Asset 和 Project-owned State 混在同一路径。
- **Rule**：Template 位于 `framework/templates/project/`；Project Truth 位于 `docs/`；Override 位于 `.yuan/overrides/`。

### M-004：Agent 不能直接选择 References

- **Symptom**：同一 Agent 批量读取知识库，不同 Skill 的边界消失，Context 膨胀且知识被误用。
- **Cause**：职责、方法和知识三层之间存在越级依赖。
- **Rule**：强制 `Routing → Agent → Skill → References`；Skill 必须声明 Retrieval Signal 和 Section。

### M-005：子进程 Timeout 必须终止完整 Process Tree

- **Symptom**：父调用已经 Timeout，首次 `accept` 的子进程仍持有 Lock，后续操作持续失败。
- **Cause**：只结束等待或父进程，没有终止子进程树并回收 Lock。
- **Rule**：任何执行外部进程的可选 Script 都必须设置 Timeout、在 Timeout 后终止 Process Tree、等待回收并报告 Unknown Outcome；Native Core 不依赖常驻 Runtime Process。

### M-006：路径或目录迁移必须同步 Installer 与 Contract Test

- **Symptom**：Source 已移动，Installer 仍复制旧目录，或文档存在 Dangling Reference。
- **Cause**：目录结构在多个常量和说明中重复定义。
- **Rule**：以 `framework/` 和 `framework/VERSION` 为唯一官方源；结构变化必须同时通过 Installer Test 与 Reference Check。

### M-007：中国网络环境的 GitHub Transport 需要可替代路径

- **Symptom**：HTTPS 443 Timeout，或 `gh` 下载极慢。
- **Rule**：先区分 Repository 问题与 Network Transport；可使用已配置 SSH Remote 或可信 Mirror，但不得把网络失败误诊为 Framework Logic Failure。

### M-008：Insight 字段必须通过 "Yuan First" 测试

- **Symptom**：为 Dashboard 增加字段，Core 变重，删除 Insight 后字段无工程价值。
- **Rule**：任何新字段先回答"删除 Yuan Insight 后，这个字段是否仍明显改善 Yuan 自己？"——YES 进 Core，NO 只进 Insight，UNKNOWN 不加入并显示 Unknown。

### M-009：Observability 不得反向重塑 Core

- **Symptom**：为可视化设计 Memory 生命周期、Skill 状态或 Event Ledger，导致 Core 语义被 UI 需求污染。
- **Rule**：Projection follows Core semantics；UI never invents Core semantics。STATUS 是 Session Recovery Index（覆盖不追加），WORK 是 Active Work Authority（State 不是 History）；Insight 只读观察，不引入第二状态系统。

### M-010：YAML Frontmatter 列表解析须兼容两种形式

- **Symptom**：解析器只支持内联 `[a, b]`，遇到展开 `- item` 列表静默丢字段（如 workflow_id 恒为 unknown），校验形同虚设。
- **Rule**：任何解析 Frontmatter 列表的代码必须同时支持内联与展开两种形式，并用"注入不存在的 id 应报错"的负向测试验证校验真实生效。

### M-011：Observability 必须验证 Production Path，而非只验证函数

- **Symptom**：Unit Test 全绿，但 CLI、Dashboard、Observer、Coverage、Trace、Summary 和 Retention 没有接成一条真实链路。
- **Cause**：测试只覆盖局部计算，没有覆盖启动、状态变化、停止、恢复、完成归档和安装后执行。
- **Rule**：Observability 变更必须至少验证一次生产入口的端到端生命周期；Completion Transition 的 `from` 与 `to` 都是证据，清空 Active State 不得丢失最后 Agent 或 `skills_applied`。

### M-013：Framework Update 前必须先稳定 Work Checkpoint

- **Symptom**：Active Work 中途更新 Framework，下一 Session 无法判断旧 Work 做到哪里，或 Update 为了兼容而开始改写 Project Memory。
- **Rule**：Update 不迁移 Project 内容，只在写入前检查 `STATUS.work_state`；仅 `idle` / `paused` 放行。Pause 保留 `WORK.md` 全文并写清唯一 Next Action，既不归档也不清空。

### M-012：Requirement Discovery 与 Spec Clarification 不得混为一个 Gate

- **Symptom**：用户提出一个 Solution 后，Agent 立即追问字段、异常和实现细节，最终得到完整但解决错问题的 Spec；或两个 Agent 重复询问同一 Product 语义。
- **Cause**：没有区分“是否在解决正确的问题”和“正确问题是否定义完整”。
- **Rule**：同一 Product Analyst 在 Signal 命中时先完整执行 `deep-requirement-discovery`，再让 `grilling` 继承 Discovery Result 补齐 Spec；不得拆分前者规则、不得重复已有 Evidence。

### M-014：Routing 与 Workflow 不得越级选择 Skill

- **Symptom**：Workflow Frontmatter 或 Routing Policy 声明 `required_skills`，造成 Conductor 绕过 Agent Contract 直接决定专业方法。
- **Cause**：把 Workflow 编排与 Agent 内部能力选择混成同一层，破坏单向依赖并形成重复 Truth Source。
- **Rule**：Routing 与 Workflow 只选择 Agent；Agent 根据自己的 Contract 和当前 Signal 选择 Skill；Skill 再选择 References。Insight 的 Expected Skill 也只能从已观察 Agent 的 Contract 推导。

## Engineering Conventions

- 任何新机制先回答是否直接改善非技术用户的软件交付质量，是否减少 Token、确认和维护成本。
- 重大 Product/Architecture Decision 写入前需要用户确认；已验证技术事实和 Status 可由 Yuan 自动维护。
- Completion 需要 Acceptance 逐项验证、测试或明确的 Manual Verification、必要 Reviewer、已知风险披露和 Memory/Status 更新。
- 重构优先保持现有 Test 通过；Bug 优先建立可复现失败；新 Behavior 先定义 Acceptance；无法自动化时明确 Manual Verification 和剩余风险。
- 历史协议中的“统一定义、减少重复、缩小 Change Blast Radius”仍是有效工程原则，但不再要求固定 Gate State Machine。
