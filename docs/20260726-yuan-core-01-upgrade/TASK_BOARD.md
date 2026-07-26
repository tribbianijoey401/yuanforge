# 任务板

> 会话: 20260726-yuan-core-01-upgrade
> 创建: 2026-07-26 18:30 +08:00
> 最后更新: 2026-07-26 22:53 +08:00

## 当前状态快照

| 项 | 值 |
|----|-----|
| **已验证实现 HEAD** | `f46c4e465ded813b1d21e6fa5b9d61196c7f0e54` |
| **原始 Git 脏文件** | 8 tracked modified + 2 untracked；已由 `evidence/m0a/` 保护 |
| **活跃 Agent** | task-006 独立 M3 已阻塞；task-005 等待 Backend Dev 返工 |
| **当前 authority** | 旧 YuanForge 文档运行态；新 Core 尚未接管 |
| **最后 Conductor 巡检** | 2026-07-26 18:34 +08:00 |

## 任务状态

| ID | 优先级 | 风险 | 任务 | 角色 | 依赖 | 状态 | 产出 | 原因指针 |
|----|--------|------|------|------|------|------|------|----------|
| task-001 | P0 | R0 | M0a 保护原始工作现场 | doc-engineer | - | ✅ 完成 | `evidence/m0a/` | `SESSION_LOG.md#现场保护` |
| task-002 | P0 | R0 | M0b 冻结 Genesis baseline | doc-engineer | task-001 | ✅ 完成 | `FEATURE.md`, `DESIGN.md`, `PLAN.md` | `DESIGN.md#8-trust-root-与验证层` |
| task-003 | P0 | R0 | M1 实现 bootstrap verifier | backend-dev | task-002 | ✅ 完成 | `scripts/bootstrap-core-verifier.py`, `scripts/bootstrap_verifier*.py`, `tests/bootstrap_verifier/` | `evidence/m1/held-out-final.json` |
| task-004 | P0 | R0 | M1 负向 fixtures 与反作弊验证 | tester | task-003 | ✅ 完成 | held-out tests, `evidence/m1/receipt.json` | `evidence/m1/held-out-final.json` |
| task-005 | P0 | R0 | M2 实现 inert Core candidate | backend-dev | task-004 | 🔄 返工 | `.yuan/core/0.1/`, `evidence/m2/` | `evidence/m3/independent-review.md` |
| task-006 | P0 | R0 | M3 旧信任根验证新候选 | tester | task-005 | ❌ 阻塞 | `tests/core_01/`, `evidence/m3/` | `evidence/m3/final.json` |
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
| 22:04 | task-003-r1 | task-004 | 已封闭 held-out 的三个信任边界：command 必须绑定 trusted file；receipt 与输入不相交；check id 唯一 | 全量 visible + held-out 25 项通过；Tester 文件与 `evidence/m1/` 保持独立、未纳入修复提交 |
| 22:10 | task-003-r2 | task-004 | Receipt 输出隔离已前移到 manifest 读取之前；suite root 内任何 receipt 路径只输出 stdout 失败回执 | frozen 旧 hash + 篡改 manifest + candidate receipt 组合攻击已回归；全量 visible + held-out 28 项通过 |
| 22:15 | task-004 | task-005 | M1 独立 Hard Gate 通过；31/31 tests、14-check frozen receipt、py_compile 和 dirty hash 复核均 PASS | `evidence/m1/held-out-final.json`, `evidence/m1/receipt.json` |
| 22:37 | task-005 | task-006 | inert Core candidate 已按 TDD 完成；17/17 author tests、41-check candidate conformance、31/31 M1 regression 与 10 个原 dirty hash 复核均 PASS；author 自检不构成 M3 证明 | `.yuan/core/0.1/candidate-manifest.json`, `evidence/m2/author-final.json` |
| 22:53 | task-006 | task-005-r1 | 冻结 M1 verifier 仍为 31/31 PASS，但 28-check 独立 held-out 有 12 FAIL，旧根 64-check suite 拒绝 Core candidate | M3-B01–B05；详见 `evidence/m3/independent-review.md` |

## 故障记录

| 时间 | 任务 | 类型 | 详情 |
|------|------|------|------|
| 21:58 | task-003 | held-out Blocker | M1-B01 command 可执行未绑定 root 外脚本；M1-B02 receipt 可覆盖已验证输入；M1-B03 重复 check id 可虚增断言 |
| 22:07 | task-003-r1 | held-out Blocker | M1-B04：manifest hash 校验失败时未收集 candidate 拓扑，FAIL receipt 仍可覆盖 suite input |
| 22:53 | task-006 | held-out Blocker | M3-B01–B05：Evidence 绑定/新鲜度、Attempt journal、Run Memory rebuild、自修改旧根、授权过期与 command scope 未闭合 |

## 返工记录

| 任务 | 次数 | 原因 | 审查人 |
|------|------|------|--------|
| task-003 | 2 | r1 修复三项初始 Blocker；r2 将 receipt 隔离前移到 manifest 信任之前，封闭 hash-tamper + receipt-collision 组合攻击 | Tester |
| task-005 | 1 | M3 28-check held-out 中 12 FAIL；冻结旧根明确 REJECT candidate | Tester |

## 阻塞

| 时间 | 任务 | 类型 | 原因 |
|------|------|------|------|
| 22:53 | task-006 | M3 Hard Gate | task-005 candidate 未满足 AC-03/04/05/06 与 Mandatory Semantics 2–4/7/8；等待 Backend Dev 修复 M3-B01–B05 |

## 审查结果

| 时间 | 任务 | 审查官 | 判决 | 要点 |
|------|------|--------|------|------|
| 2026-07-26 | design-freeze | clean-room Design Reviewer | passed | verifier-first、单写 authority、无损回退、dirty 保护与条款级 provenance 已通过对抗审查 |
| 2026-07-26 21:58 | task-003 / task-004 | Tester held-out | blocked → r1 待复测 | 11 项中 3 项 Blocker；证据见 `evidence/m1/held-out-blocker-review.md` |
| 2026-07-26 22:07 | task-003-r1 / task-004 | Tester held-out | blocked → r2 待复测 | 未预告组合攻击 M1-B04；manifest 未可信时 receipt 仍覆盖 candidate |
| 2026-07-26 22:15 | task-003-r2 / task-004 | Tester held-out | PASS | 31/31、0 skip；junction、receipt 边界、原子失败、UTF-8 与反作弊全通过；M1-B01–B04 关闭 |
| 2026-07-26 22:53 | task-005 / task-006 | Tester held-out | FAIL → task-005 r1 | 旧 bootstrap 64 checks 明确拒绝 candidate；held-out 16 PASS / 12 FAIL；M3-B01–B05 |

## Conductor 调度状态

| 时间 | 调度动作 | 目标 | 状态 |
|------|----------|------|------|
| 18:30 | 派发 task-001 / task-002 | doc-engineer | M0 文档与现场保护执行中 |
| 18:34 | task-002 完成 → promote task-003 | backend-dev | 等待 Conductor 派发 M1 |
| 18:51 | task-003 完成 → promote task-004 | tester | 等待 Conductor 派发独立负向验证 |
| 22:04 | task-003 r1 修复完成 → task-004 复测 | tester | 等待独立 held-out 复测和最终 M1 receipt |
| 22:10 | task-003 r2 修复完成 → task-004 复测 | tester | 等待独立组合攻击复测和最终 M1 receipt |
| 22:15 | task-004 完成 → promote task-005 | backend-dev | M1 Gate PASS，M2 inert Core candidate 可派发 |
| 22:37 | task-005 完成 → promote task-006 | tester | M2 author evidence PASS；须由旧 Genesis trust root + 新 held-out 独立验证 |
| 22:53 | task-006 阻塞 → return task-005-r1 | backend-dev | 修复 M3-B01–B05 后原样重跑独立 held-out，不得弱化测试 |

## 派发日志

| 时间 | 任务 | Tier | 目标角色 | 结果 |
|------|------|------|------|
| 18:29 | task-001 | Tier 1 | doc-engineer | ✅ 仓库外 snapshot 已创建并验证 |
| 18:30 | task-002 | Tier 1 | doc-engineer | ✅ Genesis baseline 已冻结 |
| 18:35 | task-003 | Tier 1 | backend-dev | ✅ verifier、author-visible fixtures 与 9 项开发测试完成 |
| 22:00 | task-003-r1 | Tier 1 | backend-dev | ✅ 三个 held-out Blocker 已修复；visible + held-out 25 项通过 |
| 22:08 | task-003-r2 | Tier 1 | backend-dev | ✅ receipt 先验隔离已实现；visible + held-out 28 项通过 |
| 22:10 | task-004 | Tier 1 | tester | ✅ 独立 31 项负向/反作弊/边界验证通过，M1 receipt 已冻结 |
| 22:37 | task-005 | Tier 1 | backend-dev | ✅ 五原语 Schema/Protocol、reference Port、author fixtures/tests/conformance 完成；M3 独立 Gate 待执行 |
| 22:53 | task-006 | Tier 1 | tester | ❌ M3 Hard Gate：冻结旧根 REJECT；held-out 12 项失败，task-005 返工 |
