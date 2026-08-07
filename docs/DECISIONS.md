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
- **Decision**：Conductor Routing 选择 Agent；Agent 选择 Contract 声明的 Skill；Skill 根据 Retrieval Signal 选择 Reference Section。Agent 和 Conductor 不直接加载 References。
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

## Historical Decision

旧 `ADR-001` 曾把 Human Gate 与 Quality Gate 统一到 v3 Workflow Protocol。该 Decision 在 v3 内部解决了命名冲突，但其固定 Gate/Protocol 前提已被 D-001 与 D-005 Supersede；其中“减少重复定义、缩小变更爆炸半径”的工程经验仍保留在 `MEMORY.md`。
