# Yuan Decisions

本文件只记录已确认、会长期影响 Product 或 Architecture 的 Decision。历史方案可以用于解释原因，但不再与当前 Decision 竞争 Truth Source。

## D-001：Yuan 使用 Agent-platform-native Architecture

- **Status**：Confirmed
- **Decision**：Yuan vNext 是 Markdown Framework，不建设独立 Agent Runtime 或安全控制平面。
- **Reason**：首要价值是代码质量、长期连续性和专业协作；重型 Runtime 增加 Token、时间、确认与维护成本，却无法在现有 Platform 上完整拦截 Tool。
- **Supersedes**：v3 Runtime Protocol、Reducer、Ledger、Gateway、Authority Chain 方向。

## D-002：保留完整专业资产，改为 Dynamic Loading

- **Status**：Confirmed
- **Decision**：现有 13 个 Agent Contract、18 个 Skill 和 31 个 Reference 全部保留为专业资产；不默认全部加载。
- **Reason**：旧仓库的专业内容有价值，问题在固定触发和依赖混乱，不在内容本身。

## D-003：唯一依赖方向为 Agent → Skill → References

- **Status**：Confirmed
- **Decision**：Conductor Routing 与 Workflow 只选择 Agent，不声明或指定 Skill；Agent 根据 Contract 与当前 Signal 选择 Skill；Skill 根据 Retrieval Signal 选择 Reference Section。Agent 和 Conductor 不直接加载 References。
- **Reason**：让职责、方法和知识分层，避免误用能力、全量注入和 Token 膨胀。

## D-004：采用七类 Project Document

- **Status**：Confirmed
- **Decision**：默认只维护 `PRODUCT.md`、`ARCHITECTURE.md`、`DECISIONS.md`、`BACKLOG.md`、`WORK.md`、`STATUS.md` 和 `MEMORY.md`。
- **Reason**：每类信息只有一个稳定落点，既能跨 Session 恢复，也避免 DocsOS 的对象、Graph、Event、Proposal 和 Session 多源漂移。

## D-005：Verification First 与 Risk-driven Review

- **Status**：Confirmed
- **Decision**：实现前先定义可执行验证；Bug 优先建立 Reproduction/Regression；Reviewer 由 Risk 决定，不固定启动所有 Reviewer。
- **Reason**：保留 TDD、Verifier、Test Integrity 和多角色独立检查的质量价值，同时避免小任务被完整 Gate 流水线拖慢。

## D-006：Update 强制采用最新官方快照

- **Status**：Confirmed
- **Decision**：`update` 不保留旧官方 Framework，不因旧版本或旧 Runtime 状态失败；只保留 Project Memory、Override 和业务内容。
- **Reason**：安装或更新本身常用于修复损坏 Framework，不能要求旧 Framework 先健康。

## D-007：Project Override 与官方资产分离

- **Status**：Confirmed
- **Decision**：官方资产安装到 `.yuan/framework/`；Project 自定义写入 `.yuan/overrides/`，采用相同相对路径并具有更高优先级。
- **Reason**：Update 可以整体替换官方快照，同时不覆盖本地经验和项目特化。

## D-008：Requirement Discovery 与 Spec Clarification 由同一 Product Analyst 串联

- **Status**：Confirmed
- **Decision**：模糊、高影响、高不确定或 Solution 先于 Outcome 的需求，先完整执行 `deep-requirement-discovery`，再由同一 Product Analyst 使用 `grilling` 形成具体 Spec。前者不拆分 References，不删减规则；后者继承 Discovery Result，不重复访谈。
- **Reason**：Discovery 负责确认是否在解决正确的问题，Grilling 负责把正确问题定义成可开发、可验证的 Product Contract；保持同一 Agent Ownership 可以避免语义丢失、重复提问和双 Truth Source。

## D-009：Update 只检查 Work 状态，不迁移 Project 内容

- **Status**：Confirmed
- **Decision**：Update 继续只替换全部官方受管资产并原样保留 Project-owned 文件；写入前只阻止明确的 `STATUS.work_state: active`。旧格式、缺失或无法判定的状态直接放行，不需要迁移 Document 或传递额外参数。未完成 Work 可保存 Checkpoint 后标记为 `paused`，下次 Session 原地恢复。每次 Update 必须逐项输出实际保留的 Yuan-known 路径及原因。
- **Reason**：Update 不应猜测或重写项目事实，但也不能在 Active Work 尚未形成可恢复点时改变 Framework Contract。

## D-010：Yuan 路径使用三种逻辑定位符

- **Status**：Confirmed
- **Decision**：运行时契约使用 `project://`、`framework://`、`skill://` 分别表示 Project Root、带 Override 优先级的 Framework Root、当前 Skill Root。定位符不是文件夹名、环境变量或 URL，必须在文件操作前解析；禁止使用 `PROJECT_ROOT/...` 这类容易被误认为真实目录的占位表达。
- **Reason**：根信息必须存在于每个路径本身，单 LLM、多 Agent 与不同 Platform 才能在没有隐含当前目录假设时得到同一解析结果。

## D-011：规范状态采用单一可执行 State Guard

- **Status**：Confirmed
- **Decision**：状态词汇由 `framework://policies/state-contract.md` 定义，合法 Workflow Stage 与 Agent ID 分别动态来自 Workflow frontmatter 和 Agent Contract 文件名，且 Agent 必须被当前 Workflow 声明；`framework://tools/state_guard.py` 在每次 Conductor State Commit 后只读校验。Installer Check 与 Insight 加载同一 Guard，不复制校验逻辑、不自动改写 Project State。具体动作以 WORK 的 Current Task 为唯一真相源，Insight 只做派生展示；执行实例标签可进入 `agent.instance`。
- **Reason**：自然语言提示无法可靠阻止 LLM 创造 `specialist_execution`、`frontend-fixer` 等非规范值；多套事后校验又会漂移。一个轻量、无后台进程、无状态写权限的可执行提交门能在保留 Markdown 与单 LLM 架构的同时阻止错误状态继续驱动 Dispatch。

## D-012：界面设计采用内容驱动的展示架构链

- **Status**：Confirmed
- **Decision**：Yuan 的高影响界面设计沿 `Outcome / Task → Product Contract → Repository Capability Audit → Content / Data Model → View Model / IA → Visual Language → Prototype Convergence → Presentation Contract → Independent Review → Frontend Implementation` 推导。全过程分开 Product Truth、System Capability Evidence 与 Presentation Decision；每个数据型 UI 区域声明 source、fields、freshness、failure/empty semantics 与 ownership。UI Designer 冻结同一 Presentation Contract，UX Reviewer 审查，Frontend Dev 只消费。View Model 由内容量、关系、任务、变化频率、设备与上下文连续性决定，不默认 Dashboard、单屏或长滚动；query-ux-pro-max 仅在 View Model 之后作为条件性建议。
- **Reason**：视觉风格或页面模板先行会让不同产品收敛到同一布局；跳过 Repository Evidence 又会让前端用固定文案伪造后端没有的判断。统一因果链让页面结构、数据语义、视觉、反馈和验证都可追溯，同时允许用户偏好覆盖行业默认配方。用户认可“舒服/高级”只收敛视觉方向，不证明数据契约和实施条件完整。

## D-013：UI 设计是前端实现的前置硬门

- **Status**：Confirmed
- **Decision**：涉及 UI 的 New Feature / Large Project 中，`frontend-dev` 进入实现阶段（`implement` / `build` 及之后）前，`presentation_contract` 必须为 `frozen`，且 WORK 必须提供 `Status: frozen`、Product Truth、Contract Locator 与 Prototype / Verification evidence。未冻结时报 `STATE_UI_DESIGN_MISSING`；只有状态、没有内容时报 `STATE_UI_PRESENTATION_CONTRACT_INCOMPLETE`。Complex Bug 与 Small Change 不触发此门。
- **Reason**：UI Designer 与 UX Reviewer 原本只是 optional，导致前端在无原型时裸写界面、风格趋同于 AI 模板。把"frontend-dev 被启用"本身当作"有 UI"的铁证，让审美环节从依赖 LLM 自觉变成机器可校验的前置条件。

## D-014：Framework 分发使用 Version + 内容指纹双重身份

- **Status**：Confirmed
- **Decision**：任何 managed Framework capability 变化都升级 `framework/VERSION`；Installer 同时将 Framework tree 的 SHA-256 content fingerprint 写入 `.yuan/install.json`。`check` 比较安装记录、项目 Snapshot 与当前 Source，内容不一致即报告 fingerprint mismatch / source drift，即使版本字符串相同也不能判定能力已安装。
- **Reason**：`content-driven-interface-design` 已进入 Source，但 Codex 安装副本和 BTC-data snapshot 仍缺失该能力，三者却同标 `4.0.0-alpha.10`。只有版本字符串无法识别漏发、陈旧副本或受管内容被直接修改。

## Historical Decision

旧 `ADR-001` 曾把 Human Gate 与 Quality Gate 统一到 v3 Workflow Protocol。该 Decision 在 v3 内部解决了命名冲突，但其固定 Gate/Protocol 前提已被 D-001 与 D-005 Supersede；其中“减少重复定义、缩小变更爆炸半径”的工程经验仍保留在 `MEMORY.md`。
