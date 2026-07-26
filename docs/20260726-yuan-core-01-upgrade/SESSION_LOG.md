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
| task-003–task-013 | ⏳ 等待 | M1–M9 实施与验证 | 严格按 verifier-first 依赖推进 | 见 `PLAN.md` | — |

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
- `docs/events/20260726/events.jsonl`
