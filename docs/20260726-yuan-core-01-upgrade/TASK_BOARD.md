# 任务板

> 会话: 20260726-yuan-core-01-upgrade
> 创建: 2026-07-26 18:30 +08:00
> 最后更新: 2026-07-26 18:51 +08:00

## 当前状态快照

| 项 | 值 |
|----|-----|
| **Git HEAD** | `b8fc38901f928be2fe52d1d9fc9f15679904fe47` |
| **原始 Git 脏文件** | 8 tracked modified + 2 untracked；已由 `evidence/m0a/` 保护 |
| **活跃 Agent** | 无；下一任务 task-004 |
| **当前 authority** | 旧 YuanForge 文档运行态；新 Core 尚未接管 |
| **最后 Conductor 巡检** | 2026-07-26 18:34 +08:00 |

## 任务状态

| ID | 优先级 | 风险 | 任务 | 角色 | 依赖 | 状态 | 产出 | 原因指针 |
|----|--------|------|------|------|------|------|------|----------|
| task-001 | P0 | R0 | M0a 保护原始工作现场 | doc-engineer | - | ✅ 完成 | `evidence/m0a/` | `SESSION_LOG.md#现场保护` |
| task-002 | P0 | R0 | M0b 冻结 Genesis baseline | doc-engineer | task-001 | ✅ 完成 | `FEATURE.md`, `DESIGN.md`, `PLAN.md` | `DESIGN.md#8-trust-root-与验证层` |
| task-003 | P0 | R0 | M1 实现 bootstrap verifier | backend-dev | task-002 | ✅ 完成 | `scripts/bootstrap-core-verifier.py`, `scripts/bootstrap_verifier*.py`, `tests/bootstrap_verifier/` | `PLAN.md#里程碑-gate` |
| task-004 | P0 | R0 | M1 负向 fixtures 与反作弊验证 | tester | task-003 | 🟢 就绪 | negative fixtures, receipt | `FEATURE.md#clean-room-验收标准` |
| task-005 | P0 | R0 | M2 实现 inert Core candidate | backend-dev | task-004 | ⏳ 等待 | `.yuan/core/0.1/` | `DESIGN.md#2-五个-core-原语` |
| task-006 | P0 | R0 | M3 旧信任根验证新候选 | tester | task-005 | ⏳ 等待 | conformance Evidence | `DESIGN.md#8-trust-root-与验证层` |
| task-007 | P0 | R0 | M4 Shadow conversion 与回退演练 | backend-dev | task-006 | ⏳ 等待 | converter, rollback receipt | `DESIGN.md#9-authority-与迁移不变量` |
| task-008 | P1 | R1 | M5 Canary Work | tester | task-007 | ⏳ 等待 | canary Evidence | `PLAN.md#里程碑-gate` |
| task-009 | P1 | R1 | M6 Adapter conformance | tester | task-008 | ⏳ 等待 | adapter reports | `DESIGN.md#7-最小平台-port` |
| task-010 | P0 | R0 | M7 Extensions 与条款 provenance | doc-engineer | task-006 | ⏳ 等待 | extensions, provenance manifest | `DESIGN.md#9-authority-与迁移不变量` |
| task-011 | P0 | R0 | M8 原子 authority switch | backend-dev | task-009,task-010 | ⏳ 等待 | writer guard, authority receipt | `PLAN.md#里程碑-gate` |
| task-012 | P0 | R0 | M9 自修改 dogfood | tester | task-011 | ⏳ 等待 | self-host Evidence | `FEATURE.md#clean-room-验收标准` |
| task-013 | P0 | R0 | M9 汇报、二次授权与 tombstone | doc-engineer | task-012 | ⏳ 等待 | 清场报告、授权回执、恢复窗口 | `PLAN.md#里程碑-gate` |

## 上下文传递

| 时间戳 | 从 | 到 | 摘要 | 传递内容 |
|--------|-----|----|------|----------|
| 18:30 | task-001 | task-002,task-003 | 原始 dirty 已在仓库外先行保护；证据将镜像到 Workspace | `evidence/m0a/` 含 base commit、binary patch、status、tracked mode/hash 与 untracked 原文/hash |
| 18:30 | clean-room-design | task-002,task-003,task-004 | 用户已确认五原语、六结果、最小人工介入和可回退简化 | `FEATURE.md`, `DESIGN.md` 为冻结 Genesis 输入 |
| 18:51 | task-003 | task-004 | 独立 bootstrap verifier 已按 CLI seam 完成；author-visible suite 仅供开发，Tester 须新增独立 held-out fixtures | CLI `python scripts/bootstrap-core-verifier.py --manifest <path> --manifest-sha256 <sha256> --receipt <path>`；visible manifest SHA-256 `66f20b3a04050135468209e6ead66f3df258f2faff8dbeb8f76a50c635ad8e55` |

## 故障记录

| 时间 | 任务 | 类型 | 详情 |
|------|------|------|------|
| — | — | — | 暂无 |

## 返工记录

| 任务 | 次数 | 原因 | 审查人 |
|------|------|------|--------|
| — | 0 | — | — |

## 阻塞

| 时间 | 任务 | 类型 | 原因 |
|------|------|------|------|
| — | — | — | 暂无 |

## 审查结果

| 时间 | 任务 | 审查官 | 判决 | 要点 |
|------|------|--------|------|------|
| 2026-07-26 | design-freeze | clean-room Design Reviewer | passed | verifier-first、单写 authority、无损回退、dirty 保护与条款级 provenance 已通过对抗审查 |

## Conductor 调度状态

| 时间 | 调度动作 | 目标 | 状态 |
|------|----------|------|------|
| 18:30 | 派发 task-001 / task-002 | doc-engineer | M0 文档与现场保护执行中 |
| 18:34 | task-002 完成 → promote task-003 | backend-dev | 等待 Conductor 派发 M1 |
| 18:51 | task-003 完成 → promote task-004 | tester | 等待 Conductor 派发独立负向验证 |

## 派发日志

| 时间 | 任务 | Tier | 目标角色 | 结果 |
|------|------|------|------|
| 18:29 | task-001 | Tier 1 | doc-engineer | ✅ 仓库外 snapshot 已创建并验证 |
| 18:30 | task-002 | Tier 1 | doc-engineer | ✅ Genesis baseline 已冻结 |
| 18:35 | task-003 | Tier 1 | backend-dev | ✅ verifier、author-visible fixtures 与 9 项开发测试完成 |
