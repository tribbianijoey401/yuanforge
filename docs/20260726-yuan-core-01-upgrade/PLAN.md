# Plan: Yuan Core 0.1 升级

## 概况

- **目标**: 以 verifier-first、可回退方式把现有 YuanForge 升级为五原语轻内核，并完成权威切换、自举验证与经用户确认的旧规范清场。
- **创建时间**: 2026-07-26
- **Architect**: Architect + Clean-room Design Reviewer
- **关联需求**: 用户确认 clean-room Yuan Core 0.1，并要求持续实施直到框架完全升级。
- **基线 HEAD**: `b8fc38901f928be2fe52d1d9fc9f15679904fe47`
- **执行原则**: verifier-first；旧信任根验证新候选；单写权威；失败关闭；原现场零覆盖。

## 技术方案

### 目标载体

```text
AGENTS.md
.yuan/
  VERSION
  core/0.1/
    protocol.md
    work-contract.schema.yaml
    run-memory.schema.yaml
    attempt.schema.yaml
    evidence.schema.yaml
    conformance.py
    fixtures/
  adapters/
    manual.yaml
  extensions/
.yuan-run/
  contracts/
  run-memory.yaml
  attempts/
  evidence/
```

目录只是默认文件系统投影；五原语语义不依赖 Markdown、YAML 或特定平台。

### 迁移不变量

- 在 M1 负向验证通过前，不允许新 Core candidate 获得可信状态。
- 在 M8 原子切换前，现有运行入口保持唯一 writable authority。
- Shadow conversion 只读旧状态并生成新候选，禁止双写。
- 原有 dirty 与 untracked 内容先做内容哈希保护；后续写入使用 compare-and-swap。
- 任一里程碑失败都保留独立 EvidenceReceipt 和明确回退点。
- M9 清场必须发生在完整汇报和用户二次确认之后。

## 模块划分

| 模块 | 职责 | 对应里程碑 | 关键产出 |
|------|------|------------|----------|
| 现场保护与信任根 | 保护 dirty、冻结设计与负例 | M0a–M0b | `evidence/m0a/`, `FEATURE.md`, `DESIGN.md` |
| Bootstrap verifier | 先证明验证器能拒绝坏候选 | M1 | verifier、negative fixtures、receipt |
| Inert Core | 五原语 Schema、Protocol、reference Port | M2 | `.yuan/core/0.1/` |
| 候选验证 | 旧根独立验证新 Core | M3 | conformance Evidence |
| Shadow migration | 单向转换、历史重放、回退演练 | M4 | converter、shadow report |
| Canary | 小范围真实 Work 验证 | M5 | canary Evidence |
| Adapter conformance | 逐平台验证语义一致性 | M6 | adapter reports |
| Extensions/provenance | 迁移唯一知识，隔离非 Core 机制 | M7 | extensions、clause manifest |
| Authority switch | 原子切换，拒绝旧 writer | M8 | authority receipt |
| Self-host/清场 | 自修改 dogfood 与用户确认后 tombstone | M9 | dogfood Evidence、清场报告 |

## Dispatch Plan

### 依赖关系

- task-001（M0a）无依赖，必须在任何仓库写入前完成。
- task-002（M0b）依赖 task-001；冻结后 task-003 才能开始。
- task-003 与 task-004 共同构成 M1：先实现 bootstrap verifier，再用负向 fixtures 对抗验证。
- task-005（M2）依赖 M1 证明 verifier 能拒绝坏候选。
- task-006（M3）依赖 inert candidate 和冻结 verifier。
- task-007（M4）依赖 M3；只做单向 shadow conversion，不接管 authority。
- task-008（M5）依赖 shadow 回退演练通过。
- task-009（M6）可在 canary 稳定后逐 Adapter 执行；不通过的 Adapter 标记 unsupported。
- task-010（M7）依赖 Core 语义稳定，可与 M6 后半段并行，但不能在 provenance 100% 前删除旧内容。
- task-011（M8）依赖 M6、M7 全部通过。
- task-012（M9 dogfood）依赖 authority switch。
- task-013（M9 tombstone）依赖 dogfood、完整报告和用户新的明确确认。

### 任务派发表

| Task ID | 优 | 标题 | Role | 上游依赖 | ⏱超时 | 产出物 | 门禁 | 风险 |
|---------|----|------|------|---------|-------|--------|------|------|
| task-001 | P0 | M0a 保护原始工作现场 | doc-engineer | - | 30 | `evidence/m0a/` | G1 | R0 |
| task-002 | P0 | M0b 冻结 Genesis baseline | doc-engineer | task-001 | 30 | `FEATURE.md`, `DESIGN.md`, `PLAN.md`, 状态文档 | G1 | R0 |
| task-003 | P0 | M1 实现 bootstrap verifier | backend-dev | task-002 | 90 | bootstrap verifier | G2 | R0 |
| task-004 | P0 | M1 负向 fixtures 与反作弊验证 | tester | task-003 | 60 | empty/zero/known-bad fixtures, receipt | G3 | R0 |
| task-005 | P0 | M2 实现 inert Core candidate | backend-dev | task-004 | 120 | 五原语 Schema、Protocol、reference Port | G2 | R0 |
| task-006 | P0 | M3 旧信任根验证新候选 | tester | task-005 | 60 | conformance Evidence | G3 | R0 |
| task-007 | P0 | M4 Shadow conversion 与回退演练 | backend-dev | task-006 | 120 | converter、replay/rollback receipt | G3 | R0 |
| task-008 | P1 | M5 Canary Work | tester | task-007 | 90 | canary Evidence | G3 | R1 |
| task-009 | P1 | M6 Adapter conformance | tester | task-008 | 120 | per-adapter reports | G3 | R1 |
| task-010 | P0 | M7 Extensions 与条款 provenance | doc-engineer | task-006 | 180 | extensions、100% provenance manifest | G4 | R0 |
| task-011 | P0 | M8 原子 authority switch | backend-dev | task-009,task-010 | 90 | writer guard、authority receipt | G3 | R0 |
| task-012 | P0 | M9 自修改 dogfood | tester | task-011 | 120 | self-host Work 与 Evidence | G3 | R0 |
| task-013 | P0 | M9 汇报、二次授权与 tombstone | doc-engineer | task-012 | 120 | 清场报告、授权回执、恢复窗口 | G4 | R0 |

## 里程碑 Gate

| 里程碑 | 通过标准 | 回退点 |
|--------|----------|--------|
| M0a | base、status、binary patch、tracked mode/hash、全部 untracked 原文/hash 可读且一致 | `C:\tmp` 唯一 snapshot |
| M0b | 用户确认、五原语、六结果、八项 mandatory semantics 和负例期望被冻结 | M0a snapshot |
| M1 | verifier 确实拒绝 empty、零断言、known-bad、崩溃、不可解析结果 | 删除 inert verifier candidate |
| M2 | 五 Schema 和最小 Port 完整，但未接管入口 | 保持旧 authority |
| M3 | 冻结 verifier 对 candidate 全绿；不得由 candidate 自证 | 回到 M2 修正 |
| M4 | 历史重放一致、单写、writer guard、无损 rollback drill 通过 | 丢弃 shadow 投影 |
| M5 | Canary AC 全部有当前证据，无 UNKNOWN 副作用 | 回到旧 authority |
| M6 | 每个 Adapter 独立通过；失败者明确 unsupported | 禁用单个 Adapter |
| M7 | 旧条款归宿覆盖率 100%，唯一知识零丢失 | 保留旧规范只读 |
| M8 | 原子指针切换成功，旧 writer 被机械拒绝，回退再次验证 | 切回旧 authority |
| M9 | Core 完成自修改 dogfood；用户二次确认后才 tombstone；恢复窗口有效 | 内容寻址归档 |

## 提交策略

- 一个 task 一个原子 commit。
- 每次提交前只 stage 当前 task 产出；现有用户 dirty 文件不得被 stage。
- M0 使用 `docs(task-M0): protect workspace and freeze core baseline`。
- 后续实现提交分别关联 M1–M9，不把迁移清场混入 Core 实现。
