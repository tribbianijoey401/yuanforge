# 任务板

> 会话: 20260726-yuan-core-01-upgrade
> 创建: 2026-07-26 18:30 +08:00
> 最后更新: 2026-07-27 01:03 +08:00

## 当前状态快照

| 项 | 值 |
|----|-----|
| **已验证实现 HEAD** | `9370d7fc992a0d8bf51ee7f898e556abec0b277a` |
| **原始 Git 脏文件** | 8 tracked modified + 2 untracked；已由 `evidence/m0a/` 保护 |
| **活跃 Agent** | task-009 已完成；task-010 可继续；task-011 仍等待 task-010 |
| **当前 authority** | 旧 YuanForge 文档运行态；新 Core 尚未接管 |
| **最后 Conductor 巡检** | 2026-07-26 18:34 +08:00 |

## 任务状态

| ID | 优先级 | 风险 | 任务 | 角色 | 依赖 | 状态 | 产出 | 原因指针 |
|----|--------|------|------|------|------|------|------|----------|
| task-001 | P0 | R0 | M0a 保护原始工作现场 | doc-engineer | - | ✅ 完成 | `evidence/m0a/` | `SESSION_LOG.md#现场保护` |
| task-002 | P0 | R0 | M0b 冻结 Genesis baseline | doc-engineer | task-001 | ✅ 完成 | `FEATURE.md`, `DESIGN.md`, `PLAN.md` | `DESIGN.md#8-trust-root-与验证层` |
| task-003 | P0 | R0 | M1 实现 bootstrap verifier | backend-dev | task-002 | ✅ 完成 | `scripts/bootstrap-core-verifier.py`, `scripts/bootstrap_verifier*.py`, `tests/bootstrap_verifier/` | `evidence/m1/held-out-final.json` |
| task-004 | P0 | R0 | M1 负向 fixtures 与反作弊验证 | tester | task-003 | ✅ 完成 | held-out tests, `evidence/m1/receipt.json` | `evidence/m1/held-out-final.json` |
| task-005 | P0 | R0 | M2 实现 inert Core candidate | backend-dev | task-004 | ✅ 完成 | `.yuan/core/0.1/`, `evidence/m2/` | `evidence/m3/independent-review.md` |
| task-006 | P0 | R0 | M3 旧信任根验证新候选 | tester | task-005 | ✅ 完成 | `tests/core_01/`, `evidence/m3/` | `evidence/m3/final.json` |
| task-007 | P0 | R0 | M4 Shadow conversion 与回退演练 | backend-dev | task-006 | ✅ 完成 | converter, rollback receipt | `evidence/m4/author-evidence.md` |
| task-008 | P1 | R1 | M5 Canary Work | tester | task-007 | ✅ 完成 | canary Evidence + 13-check held-out Gate | `evidence/m5/final-verification.json` |
| task-009 | P1 | R1 | M6 Adapter conformance | tester | task-008 | ✅ 完成 | 8-check adapter Gate + old-root receipt | `evidence/m6/final-verification.json` |
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
| 23:14 | task-005-r1 | task-006 | M3-B01–B05 已按 author TDD 封闭；25/25 author、48-check candidate self-check、28/28 原样 held-out、31/31 M1 回归均 PASS | 新 manifest SHA-256 `659e2da5cc3732d96fb15c6a470a0ca974cc8161c6e31e165c8032cdbbdbd942`；冻结 M3 runner 须由 Tester 独立重绑定后出具新证据 |
| 23:23 | task-006-r1 | task-005-r2 | 完整性 diff 通过、原 28 项 held-out 全绿；新增纯数据组合一致性检查发现 replay 未强制 self-mod proof 且 BLOCKED 投影丢失 artifact/Port scope | M3-B06；新 hash 已重绑定，旧根 72-check suite 仅拒绝 Core case |
| 23:35 | task-005-r2 | task-006-r2 | replay 已在 COMPLETE 前强制验证受保护变更 trust proof；BLOCKED 投影按 Evidence→Attempt→Work 保留真实 scope | 27/27 author、50/50 self-check、29/29 原样 held-out、31/31 M1 PASS；新 manifest SHA-256 `c3d41ac1a056523ad5af4a430e09185f7ab1e732507097ba7546be7f512d72e3` |
| 23:39 | task-006-r2 | task-007 | 旧 Genesis trust root 已接受修正候选；独立 held-out 与固定种子变体全部通过 | 30/30 held-out、27/27 author、31/31 M1、75-check bootstrap（7/7 cases）PASS；M3_APPROVED |
| 23:58 | task-007 | task-008,task-010 | 单向 shadow converter、writer guard、确定性 replay 与无损 rollback 已完成 | 3 Workspace / 9 sources / 28 records；Core rebuild 3/3 PASS；19 项歧义全部 structured unresolved/BLOCKED；legacy rollback hash 相等 |
| 00:17 | task-008 | task-005-r3 | 真实 Canary 成功路径 reducer=`COMPLETE`，但 UNKNOWN 失败分支丢失 reconciliation target | 10 项独立检查 9 PASS / 1 FAIL；M5-B01 见 `evidence/m5/M5-TEST-REPORT.md` |
| 00:28 | task-005-r3 | task-008-r1 | BLOCKED replay 现从合法 immutable Attempt 重建 `{attempt_id,state}` pending 指针；digest 不可信时 phase 降级 UNKNOWN | 30/30 author、52/52 self-check、M3 1/1、M5 canary 10/10、M1 31/31 PASS；新 manifest SHA-256 `d3e0f536428c7315f96b6546b4f728055c162cff16e80d00d3b5d5db378ea4fc` |
| 00:34 | task-008-r1 | task-009 | r3 未修改 Canary Gate；原 10 项与 3 项普通数据变体全绿，旧 Genesis root 接受新 candidate | 13/13 M5、31/31 M1、30/30 Core、1/1 M3、77-check old-root、10/10 M4 PASS |
| 00:42 | task-009 | task-005-r4 | M6 held-out 首轮 1/5 PASS；Reference Port 缺枚举/LLM receipt，manual/Hermes 缺 Core descriptor | `evidence/m6/held-out-initial.json`；M6-B01–B04 路由 backend-dev；Hermes 可诚实 unsupported |
| 00:54 | task-005-r4 | task-009-r1 | M6-B01–B04 已封闭：有界稳定枚举与文件哈希、纯提案结构化回执、manual 可执行 descriptor、Hermes 诚实 unsupported | 35/35 author、55-check self-check、M6 5/5、M1 31/31、M3 held-out 30/30、M4 10/10、M5 1/1 PASS；manifest `20ac1cbb7f2377d5cecadf3347a40d81e14e8469c6c914701f585a49903d9768`，旧根冻结哈希待 Tester 独立重绑定 |
| 01:03 | task-009-r1 | task-011 | M6 独立 Gate PASS；manual 为可执行 Reference Port，Hermes 诚实 unsupported 且 Core 不依赖 | 原样 5/5 + 独立变体 3/3；旧 Genesis 80 checks / 7 cases；M1/M3/M4/M5 与 M0a dirty 全绿；task-011 仍等待 task-010 |

## 故障记录

| 时间 | 任务 | 类型 | 详情 |
|------|------|------|------|
| 21:58 | task-003 | held-out Blocker | M1-B01 command 可执行未绑定 root 外脚本；M1-B02 receipt 可覆盖已验证输入；M1-B03 重复 check id 可虚增断言 |
| 22:07 | task-003-r1 | held-out Blocker | M1-B04：manifest hash 校验失败时未收集 candidate 拓扑，FAIL receipt 仍可覆盖 suite input |
| 22:53 | task-006 | held-out Blocker | M3-B01–B05：Evidence 绑定/新鲜度、Attempt journal、Run Memory rebuild、自修改旧根、授权过期与 command scope 未闭合 |
| 23:23 | task-006-r1 | held-out Blocker | M3-B06：self_modification_authorized 未接入 replay；`_blocked` 将 artifact scope 硬编码为 `.` |
| 00:17 | task-008 | held-out Blocker | M5-B01：`BLOCKED` rebuild 将合法 UNKNOWN Attempt 从 `pending_side_effects` 丢失，后续 reconciliation 无法定位 |
| 00:42 | task-009 | held-out Blocker | M6-B01–B04：Reference Port 缺 enumerate/LLM receipt；manual/Hermes 缺 Core descriptor |

## 返工记录

| 任务 | 次数 | 原因 | 审查人 |
|------|------|------|--------|
| task-003 | 2 | r1 修复三项初始 Blocker；r2 将 receipt 隔离前移到 manifest 信任之前，封闭 hash-tamper + receipt-collision 组合攻击 | Tester |
| task-005 | 4 | r1 封闭 B01–B05；r2 强制 replay trust proof/修复 BLOCKED scope；r3 修复 UNKNOWN pending 原子指针；r4 封闭 M6 Adapter B01–B04 | Tester |
| task-009 | 1 | M6 首轮发现 B01–B04，路由 task-005-r4；held-out 需原样复测 | Tester |

## 阻塞

| 时间 | 任务 | 类型 | 原因 |
|------|------|------|------|
| — | — | — | 暂无 |

## 审查结果

| 时间 | 任务 | 审查官 | 判决 | 要点 |
|------|------|--------|------|------|
| 2026-07-26 | design-freeze | clean-room Design Reviewer | passed | verifier-first、单写 authority、无损回退、dirty 保护与条款级 provenance 已通过对抗审查 |
| 2026-07-26 21:58 | task-003 / task-004 | Tester held-out | blocked → r1 待复测 | 11 项中 3 项 Blocker；证据见 `evidence/m1/held-out-blocker-review.md` |
| 2026-07-26 22:07 | task-003-r1 / task-004 | Tester held-out | blocked → r2 待复测 | 未预告组合攻击 M1-B04；manifest 未可信时 receipt 仍覆盖 candidate |
| 2026-07-26 22:15 | task-003-r2 / task-004 | Tester held-out | PASS | 31/31、0 skip；junction、receipt 边界、原子失败、UTF-8 与反作弊全通过；M1-B01–B04 关闭 |
| 2026-07-26 22:53 | task-005 / task-006 | Tester held-out | FAIL → task-005 r1 | 旧 bootstrap 64 checks 明确拒绝 candidate；held-out 16 PASS / 12 FAIL；M3-B01–B05 |
| 2026-07-26 23:23 | task-005-r1 / task-006-r1 | Tester held-out | FAIL → task-005 r2 | 原 28 项全 PASS；新增组合检查 FAIL；旧 bootstrap 72 checks 仅 Core case REJECT；M3-B06 |
| 2026-07-26 23:39 | task-005-r2 / task-006-r2 | Tester held-out | PASS | 30/30 held-out、27/27 author、31/31 M1；旧 bootstrap 75 checks、7/7 cases 接受 Core；M3-B01–B06 全部关闭 |
| 2026-07-27 00:17 | task-008 | Tester Canary held-out | FAIL → task-005-r3 | 成功路径 COMPLETE；10 项独立检查 9 PASS / 1 FAIL；M5-B01 丢失 UNKNOWN reconciliation target |
| 2026-07-27 00:34 | task-005-r3 / task-008-r1 | Tester Canary held-out | PASS | 原 10 项 10/10 + 普通数据变体 3/3；COMMITTED/read 不伪造 pending，missing Attempt fail-closed；M5-B01 关闭 |
| 2026-07-27 00:42 | task-009 | Tester Adapter held-out | FAIL → task-005-r4 | 5 项 trace 1 PASS / 4 FAIL；M6-B01–B04，Hermes 允许诚实 unsupported |
| 2026-07-27 01:03 | task-005-r4 / task-009-r1 | Tester Adapter held-out | PASS | M6 8/8；旧 Genesis 80 checks / 7 cases；M6-B01–B04 关闭 |

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
| 23:14 | task-005-r1 完成 → task-006 复测 | tester | author 回归全绿；冻结 M3 runner 的候选 manifest 哈希须由 Tester 独立重绑定 |
| 23:23 | task-006-r1 阻塞 → return task-005-r2 | backend-dev | 将 self-mod proof 强制接入 replay，并保留 BLOCKED artifact/Port scope；不得弱化 held-out |
| 23:35 | task-005-r2 完成 → task-006-r2 复测 | tester | M3-B06 author 与原样 held-out 均绿；冻结 M3 runner 须独立重绑定新 manifest |
| 23:39 | task-006-r2 完成 → promote task-007 | backend-dev | M3 Gate PASS；M4 Shadow conversion 与无损回退演练可派发 |
| 23:58 | task-007 完成 → promote task-008 | tester | M4 author gate PASS；M5 Canary 可派发，M7 仍可并行 |
| 00:17 | task-008 阻塞 → return task-005-r3 | backend-dev | 保留合法 UNKNOWN pending side effect，且不得弱化 M5/M3/M1 Gate |
| 00:28 | task-005-r3 完成 → task-008-r1 复测 | tester | M5-B01 author 与原样 canary 均绿；由 Tester 更新独立证据与 Gate 判决 |
| 00:34 | task-008-r1 完成 → promote task-009 | tester | M5 Hard Gate PASS；M6 Adapter conformance 可派发 |
| 00:42 | task-009 阻塞 → return task-005-r4 | backend-dev | 保持 held-out 原样；补齐 Reference Port enumerate/LLM receipt 与 manual/Hermes Core descriptor |
| 00:54 | task-005-r4 完成 → task-009-r1 复测 | tester | 作者与原样 M6/M1/M3/M4/M5 回归均绿；冻结 M3 runner 的 candidate-manifest 哈希须由 Tester 独立重绑定 |
| 01:03 | task-009-r1 完成 → task-011 依赖部分满足 | backend-dev | M6 Hard Gate PASS；task-011 仍须等待 task-010 M7 |

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
| 23:14 | task-005-r1 | Tier 1 | backend-dev | ✅ B01–B05 修复完成；author 25/25、自检 48/48、原样 held-out 28/28、M1 31/31 |
| 23:23 | task-006-r1 | Tier 1 | tester | ❌ M3 Hard Gate：新组合一致性检查发现 M3-B06，旧根继续 REJECT |
| 23:35 | task-005-r2 | Tier 1 | backend-dev | ✅ B06 修复完成；author 27/27、自检 50/50、原样 held-out 29/29、M1 31/31 |
| 23:39 | task-006-r2 | Tier 1 | tester | ✅ M3_APPROVED：30/30 独立 held-out、旧根 75 checks / 7 cases 全部通过 |
| 23:58 | task-007 | Tier 1 | backend-dev | ✅ 9/9 TDD、3/3 Core rebuild、单写 guard 与 rollback drill PASS；旧语义歧义未猜测完成 |
| 00:17 | task-008 | Tier 1 | tester | ❌ 真实 Canary 成功路径 COMPLETE；UNKNOWN 恢复分支暴露 M5-B01，Hard Gate 阻塞 |
| 00:28 | task-005-r3 | Tier 1 | backend-dev | ✅ M5-B01 修复完成；author 30/30、自检 52/52、M3/M5/M1 全绿 |
| 00:34 | task-008-r1 | Tier 1 | tester | ✅ M5 13/13、旧根 77 checks / 7 cases、全回归与原 dirty hash 全绿 |
| 00:42 | task-009 | Tier 1 | tester | ❌ M6 Hard Gate：5 项同轨 trace 1 PASS / 4 FAIL；M6-B01–B04 路由 backend-dev |
| 00:54 | task-005-r4 | Tier 1 | backend-dev | ✅ M6-B01–B04 修复完成；author 35/35、自检 55/55、M6 5/5、M1/M3/M4/M5 回归全绿；待独立 Tester 复测与旧根重绑定 |
| 01:03 | task-009-r1 | Tier 1 | tester | ✅ M6_PASS：8/8 独立 trace，旧 Genesis 80 checks / 7 cases，全回归与 dirty hash 通过 |
