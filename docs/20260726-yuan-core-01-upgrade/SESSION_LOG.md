# 会话日志

> 会话: 20260726-yuan-core-01-upgrade
> 开始: 2026-07-26 18:29 +08:00
> 结束: —
> 模式: 严格模式 / verifier-first migration
> 接续自: 无

## 任务完成情况

| 任务 | 状态 | 简述 | 决策 | 产出 | Commit |
|------|------|------|------|------|--------|
| task-001 | ✅ 完成 | 在任何仓库写入前保护原始 dirty 与 untracked 内容 | 使用仓库外唯一 snapshot，后镜像为 Evidence | `evidence/m0a/` | 本提交 |
| task-002 | ✅ 完成 | 冻结 clean-room Yuan Core 0.1 Genesis baseline | 五原语、六结果、八项 mandatory semantics | `FEATURE.md`, `DESIGN.md`, `PLAN.md`, 状态文档 | 本提交 |
| task-003 | ✅ 完成 | 独立、失败关闭的 bootstrap verifier | CLI + 冻结 manifest SHA-256 + 结构化 receipt；visible fixtures 不替代 Tester held-out | `scripts/bootstrap-core-verifier.py`, `scripts/bootstrap_verifier*.py`, `tests/bootstrap_verifier/` | 本提交 |
| task-004 | ✅ 完成 | M1 独立 held-out、组合攻击与反作弊验证 | 两轮返工关闭 M1-B01–B04；31/31 tests 和冻结 receipt PASS | `tests/bootstrap_verifier/test_bootstrap_core_verifier_held_out.py`, `evidence/m1/` | 本提交 |
| task-005 | ✅ 完成 | M2 inert Core candidate 经两轮独立返工后通过 M3 | M3-B01–B06 全部关闭；未弱化 held-out 或旧 trust root | `.yuan/core/0.1/`, `evidence/m3/independent-review.md` | `3df9250` |
| task-006 | ✅ 完成 | M3 旧信任根接受 r2 candidate | 30/30 held-out、27/27 author、31/31 M1、75-check bootstrap 全部 PASS | `tests/core_01/`, `evidence/m3/` | 本提交 |
| task-007 | ✅ 完成 | M4 Shadow conversion 与回退演练 | 单向只读 legacy→shadow；Core 重建、writer guard 与无损 rollback 全绿 | `scripts/yuan-shadow-migrate.py`, `evidence/m4/` | 本提交 |
| task-008 | ✅ 完成 | M5 Canary Work 经 r3 修复后通过独立复测 | 原 10 项 + 3 项普通数据变体全绿；旧 Genesis root 接受新 candidate | `evidence/m5/` | 本提交 |
| task-009 | ✅ 完成 | M6 Adapter conformance | manual executable mapping + Hermes honest unsupported；旧根与独立变体通过 | `evidence/m6/` | 本提交 |
| task-010 | ✅ 完成 | M7 Extensions 与条款 provenance | 六 Extensions 只消费 Core 公共契约、只产 authoring advice/Evidence；旧源全保留 | `.yuan/extensions/`, `evidence/m7/` | 本提交 |
| task-011–task-013 | ⏳ 等待 | M8 authority switch 至 M9 清场 | M8 依赖已满足；继续 verifier-first 推进 | 见 `PLAN.md` | — |

## 现场保护

- 保护时 HEAD: `b8fc38901f928be2fe52d1d9fc9f15679904fe47`
- 仓库外原始 snapshot: `C:\tmp\yuanforge-m0a-20260726-182928-172`
- 原始 tracked dirty: 8 个。
- 原始 untracked: 2 个。
- `git-diff.binary.patch` 已由 `git apply --numstat --summary` 成功解析。
- 两个 untracked 原文副本与源文件 SHA-256 一致。
- snapshot 创建和验证完成后才创建本 Workspace，因此本 Workspace 不在原始 dirty 清单中。

## 冻结决策

1. Yuan Core 仅包含 Protocol、Work Contract、Run Memory、Attempt、Evidence。
2. Tick 仅有 CONTINUE、CORRECT、COMPLETE、BLOCKED、WAIT_AUTH、BUDGET_EXIT。
3. Harness 确定性执行、取证与归约；LLM 只提出候选。
4. 先证明 bootstrap verifier 能拒绝坏候选，再实现和验证 Core candidate。
5. 迁移期间单写 authority，禁止旧、新运行态双写。
6. 清场前必须完成条款 provenance、dogfood、完整汇报和用户二次确认。

## 完成

- M0a 原始现场保护。
- Clean-room 需求与架构冻结文档初版。
- M0a–M9 verifier-first 实施计划和 Dispatch Table。
- M0b Genesis baseline 冻结，M1 bootstrap verifier 已可派发。
- task-003 TDD Red：实现文件不存在时 5 项 CLI 测试全部失败。
- task-003 Green：9 项 CLI/异常测试全绿，`py_compile` 通过；author-visible manifest SHA-256 为 `66f20b3a04050135468209e6ead66f3df258f2faff8dbeb8f76a50c635ad8e55`。
- Bootstrap verifier 对 empty、known-bad、零断言、validator crash、不可解析输出均形成显式 REJECT，并对 manifest/candidate/validator 文件做哈希绑定。
- task-004 首轮 held-out 发现未绑定 validator command、receipt 覆盖输入和重复 check ID 三项 Blocker；r1 修复。
- task-004 未预告组合攻击发现 manifest 未可信时 FAIL receipt 仍可覆盖 candidate；r2 将 receipt 隔离前移到 manifest 信任之前。
- r2 最终独立验证：31/31 PASS、0 skip、0 xfail；额外覆盖 junction 逃逸、suite-root 边界、原子写失败、Windows UTF-8 和 reason pollution。
- 冻结 author-visible manifest 产生 14-check PASS receipt；用户原始 10 个 dirty/untracked 文件哈希仍与 M0a 一致。
- task-006 M3 使用未告知 held-out 攻击 Evidence、Attempt、Run Memory、reducer、授权/预算、Reference Port 与自修改：28 checks 中 16 PASS、12 FAIL。
- 冻结 M1 verifier regression 仍为 31/31 PASS；外层 M3 suite 内容寻址绑定 candidate 与独立 validator，64 checks 后仅 Core case 因 `CHECK_FAILED` 被拒绝。
- 建立 M3-B01–B05 并将 task-005 返回 Backend Dev；task-006 保持 Hard Gate 阻塞，修复后原样复测。
- task-005 r1 未触碰独立 held-out/M1 verifier；原 28 项 held-out、25 项 author 与 31 项 M1 全部 PASS，证明 B01–B05 已关闭。
- Tester 将外层 manifest 重绑定到 `659e2da5...bdbd942`，并新增不访问网络/外部系统、不产生真实副作用的 rebuild+self-mod revision+artifact scope 组合一致性检查。
- 新检查发现 M3-B06：replay 未强制 self-mod trust proof，且 BLOCKED Run Memory 把 artifact scope 退化为 `.`；旧根 72 checks 仅拒绝 Core case。
- task-005 r2 未触碰独立 held-out、M1 verifier 或旧 bootstrap trust root；候选 manifest 更新为 `c3d41ac1...12d72e3`。
- Tester 新增固定种子、纯数据的 16 组受保护 scope 与 previous-root proof 变体；所有不一致组合均 fail-closed。
- task-006 最终 M3：30/30 独立 held-out、27/27 author、31/31 M1 与旧根 75 checks / 7 cases 全部 PASS；M3-B01–B06 全部关闭，task-007 可派发。
- task-007 M4：扫描 3 个 Workspace、9 个 legacy source，重放 28 个
  task/event observation；Core schema/rebuild 3/3 PASS。19 个缺失或无
  verifier binding 的语义均保留为 structured unresolved，并将投影置为
  `BLOCKED`，未把旧状态文本猜成 `COMPLETE`。
- `.yuan-shadow-m4-drill` 回退前后 legacy snapshot SHA-256 均为
  `0f4098281c0338df3cd5297cc69fa57810491020f69b8ff336e1a5bde20abc4c`；
  shadow 已丢弃，结构化回执见 `evidence/m4/rollback-receipt.json`。
- task-008 M5 真实 Canary：reference Port 以 CAS 写入固定 artifact，并
  通过 Python audit sandbox command 执行预绑定独立 validator；3/3
  assertions PASS，Core reducer 仅依据 Work/Attempt/Evidence 产生
  `COMPLETE`。authority pointer 与 4 个 legacy runtime state 文件在
  Canary 执行前后 SHA-256 相等，派生 Run Memory 删除后可字节等价重建。
- M5 独立对抗检查 10 项中 9 PASS / 1 FAIL：stale Evidence 与 UNKNOWN
  均不能 COMPLETE，但合法 UNKNOWN Attempt 在 `BLOCKED` rebuild 中从
  `pending_side_effects` 消失，违反 Core Protocol §9 并使 reconciliation
  无法定位。建立 M5-B01，task-008 Hard Gate 阻塞并返回 task-005-r3。
- task-008-r1 对 `b8e518e` 做完整性 diff，确认 task-005-r3 未修改
  `tests/core_canary/` 或首轮 M5 Evidence；原样复跑 10/10 PASS。
- 新增三组普通数据变体：COMMITTED 与纯 read 均不进入 pending；缺失
  Attempt 的 Evidence 必须 BLOCKED 且不伪造 pointer。最终 M5 13/13
  PASS、0 skip、0 xfail，M5-B01 关闭。
- 新 candidate manifest `d3e0f536...ea4fc` 经旧 Genesis root
  77 checks / 7 cases 接受；M1 31/31、Core 30/30、M3 1/1、M4 10/10
  与 M0a 原 dirty 10/10 hash 全部通过。task-009 可派发。
- task-009 M6 首轮以同一套 filesystem/command/LLM/unsupported trace
  检查 Reference Port 与 manual/Hermes 映射，5 项中 1 PASS / 4 FAIL；
  建立 M6-B01–B04 并返回 task-005-r4，未用旧平台文档替代可执行证据。
- task-005-r4 未修改首轮 held-out，补齐 bounded enumeration、proposal
  receipt、manual executable descriptor，并将无 executable Core Port 的
  Hermes 明确标为 unsupported。
- task-009-r1 原样复测 5/5，加三组 enumeration budget/link、provider
  failure、descriptor hash drift/escape 普通变体，共 8/8 PASS。
  旧 Genesis root 重绑定新 candidate manifest
  `20ac1cbb...d9768` 后 80 checks / 7 cases PASS；M1 31/31、Core 35/35、
  M3 30/30、M4 10/10、M5 1/1（内部 13-check）及 M0a dirty 10/10
  全绿。M6-B01–B04 关闭，task-009 完成。
- task-010 M7：建立 software-delivery、testing、DocsOS、Knowledge、UI、
  platform-adapters 六个可选 Extension；每个只消费 Core 公共契约，只能
  形成 Work authoring advice 或 Evidence，不重定义五原语、六结果、
  `COMPLETE` 或 runtime authority。
- provenance scope 覆盖 177 个规范源、1,435,630 bytes，并按 Markdown
  heading/无 heading 全文件 hash 机械切分为 1,701 条 clause；1,701 条
  全部唯一映射到 Core / Extension / Knowledge / Fixture /
  Obsolete-with-proof，unmapped=0、coverage=100.00%。
- 抽取状态外置、Protocol over Platform、bounded convergence、
  actor/checker、held-out、integrity diff、真实环境契约验证、PIT-003/004、
  merged/deployed/live claim 分离与 VERSION 单源；10 项 legacy failure
  以 source hash 绑定为负向 fixtures，未用概括替代或删除旧源。
- M7 Gate：provenance links/hash/obsolete proof PASS；M1 31/31、Core
  35/35、M3 30/30、M4 10/10、M5 1/1（内部 13 checks）、M6 8/8、
  旧 Genesis 80 checks / 7 cases、M0a dirty 10/10 全绿。task-011 的
  M6/M7 依赖全部满足。

## 决策

- 现有 `run-ptg-cal-check.py` 和缺失的 `framework-self-test` 不属于 Genesis trust root。
- 原有角色、Phase、Gate、DocsOS、Knowledge 与测试方法降为 Extensions/recipes，不进入 Core。
- M0 snapshot 同时保留仓库外原件和 Workspace Evidence 镜像。

## 踩坑

- 遵循 `PIT-003`：框架模板规格与项目运行状态分离；本次状态只写入当前 Workspace。
- 遵循 `PIT-004`：迁移前先保留全部原始内容，不用概括替代唯一信息；删除动作推迟到 provenance 和用户清场确认之后。

## 产出物

- `FEATURE.md`
- `DESIGN.md`
- `PLAN.md`
- `TASK_BOARD.md`
- `SESSION_LOG.md`
- `evidence/m0a/`
- `scripts/bootstrap-core-verifier.py`
- `scripts/bootstrap_verifier.py`
- `scripts/bootstrap_verifier_support.py`
- `tests/bootstrap_verifier/`
- `tests/bootstrap_verifier/test_bootstrap_core_verifier_held_out.py`
- `evidence/m1/`
- `tests/core_01/`
- `evidence/m3/`
- `evidence/m5/`
- `tests/core_canary/`
- `tests/adapter_conformance/`
- `.yuan/adapters/`
- `evidence/m6/`
- `.yuan/extensions/`
- `scripts/yuan-provenance.py`
- `evidence/m7/`
- `docs/events/20260726/events.jsonl`
