# task-008 M5 Canary Work — Independent Tester Report

> 角色：Tester（未参与 Yuan Core candidate 实现）
> 首轮时间：2026-07-27 00:17 +08:00
> 独立复测：2026-07-27 00:34 +08:00
> 最终判定：`PASS — M5 Hard Gate`
> 修复闭环：`M5-B01 → task-005-r3 → task-008-r1 PASS`

## 真实 Canary Work

Canary 使用一份 schema-valid、content-addressed 的 Core Work Contract，在
仓库内低影响且可逆的
`docs/20260726-yuan-core-01-upgrade/evidence/m5/canary-run/` 范围执行：

- typed AC：`AC-CANARY-ARTIFACT`，类型 `contract`；
- 预绑定 validator：`tests/core_canary/canary_validator.py`，SHA-256
  `9c509650b0f2a6e746849fc64978f8f630f01091eab1a2874ee4df4d98522a4c`；
- deny-by-default scope/grant，有限 Tick、tool、strategy、command budget；
- reference Port 以 CAS file-write 创建固定 UTF-8 artifact；
- reference Port 以无 shell、Python audit sandbox command 执行 validator；
- Attempt journal 完整经过
  `PREPARED → EXECUTING → OBSERVED → COMMITTED`；
- file-write 与 command 均保存结构化 Port receipt；
- 独立 Evidence 为 3 assertions / 3 PASS；
- Core replay reducer 仅依据 Work、Attempt、Evidence 归约为 `COMPLETE`。

成功路径回执：

| 项 | 结果 |
|----|------|
| artifact SHA-256 | `c30e40fbf27d6ca297746483e1cad0dd04d7ef726c3565ff7f8fef98b5e3dc9c` |
| validator assertions | `3/3 PASS` |
| reducer | `COMPLETE` |
| authority pointer before/after | `f600f6aa...fd9332`，字节相等 |
| legacy runtime state before/after | 4/4 文件 SHA-256 相等 |
| derived Run Memory discard/rebuild | byte-equivalent PASS |

完整机器回执见
[`canary-run/receipt.json`](./canary-run/receipt.json)。

## 对抗与失败关闭验证

独立 verifier 共执行 10 项检查：

- 9 PASS；
- 1 FAIL；
- 0 skip / 0 xfail。

已通过：

1. persisted success history 可确定性重建为同一 `COMPLETE`；
2. typed AC、预绑定 validator、independence 与正断言数有效；
3. scope、authorization、budget 被机械执行；
4. file-write 与 command 均来自 reference Port 且有 receipt；
5. M4 authority pointer 与 legacy runtime state 未被 Canary 执行修改；
6. stale Evidence 归约为 `BLOCKED/INVALID_EVIDENCE`，不能 `COMPLETE`；
7. `UNKNOWN` side effect 归约为 `BLOCKED/UNKNOWN_SIDE_EFFECT`；
8. 删除派生 Run Memory 后可从不可变历史字节等价重建；
9. M4 writer guard 拒绝 shadow writer 越界写 legacy evidence lane。

## 首轮 Blocker M5-B01

合法的 `UNKNOWN` Attempt 输入：

```text
PREPARED → EXECUTING → UNKNOWN
```

Core 正确返回：

```text
last_result = BLOCKED
rebuild.errors = ["UNKNOWN_SIDE_EFFECT"]
```

但错误返回：

```text
pending_side_effects = []
```

这违反 `protocol.md §9` 的“Run Memory 保存 non-terminal/UNKNOWN side
effects”要求，也让下一 Tick 无法定位必须由独立 reconciliation 处理的
Attempt。Blocker 的直接原因是 `runtime_replay._blocked()` 对所有早期
阻塞投影硬编码空 `pending_side_effects`。

复现证据：

- 输入：
  [`canary-run/negative/unknown-attempt.json`](./canary-run/negative/unknown-attempt.json)
- 错误投影：
  [`canary-run/negative/unknown-run-memory.json`](./canary-run/negative/unknown-run-memory.json)
- 完整结果：
  [`independent-verification.json`](./independent-verification.json)

## 修复验收条件

`task-005-r3` 必须：

1. 让所有 `BLOCKED` 投影保留可验证历史中的 non-terminal/UNKNOWN Attempt；
2. 不因无效/歧义 Attempt 伪造 pending side effect；
3. 保持错误列表确定性排序；
4. 不改变 frozen 六结果优先级；
5. 不弱化 `tests/core_canary/`、M3 held-out 或 M1 trust-root tests；
6. 原样重跑 M5，要求 10/10 PASS 且 reducer 成功路径仍为 `COMPLETE`。

Tester 未修改 Core 实现。首轮 M5 Hard Gate 因此保持阻塞，并将修复路由
给 `task-005-r3`。

## 回归与反作弊

```text
M5 Canary held-out 首轮:  1 test / 1 expected FAIL (M5-B01)
M1 bootstrap regression: 31/31 PASS
Core author regression:  30/30 PASS
M3 independent held-out:  1/1 PASS
M4 shadow migration:     10/10 PASS
```

- 未修改 `.yuan/core/0.1/`、M1/M3 verifier、既有测试或阈值；
- 没有 skip、xfail、断言弱化或 baseline 回写；
- 成功路径与失败路径由同一冻结 Work/validator/replay 输入验证；
- `independent-verification.json` 为机器可读 Hard Gate 结果，当前明确
  记录最终 13/13 PASS；首轮 FAIL 仍保留在 Git 历史 `c93bd83`，没有
  通过改写历史隐藏。

## task-008-r1 独立复测

完整性 diff：

- `task-005-r3` 只修改 Core protocol、replay 实现、candidate manifest、
  作者测试和 TASK_BOARD；
- `tests/core_canary/` 与首轮 `evidence/m5/` 零 diff；
- 没有删除/弱化 M5 断言，没有新增 skip/xfail，没有降低阈值；
- candidate manifest SHA-256 独立复核为
  `d3e0f536428c7315f96b6546b4f728055c162cff16e80d00d3b5d5db378ea4fc`。

原样复跑的首轮 10 项现为 `10/10 PASS`。另新增三项普通数据 held-out
变体，防止针对 UNKNOWN 的过拟合修复：

1. 正常 `COMMITTED` side effect 不进入 `pending_side_effects`；
2. 合法纯 `file-read` Attempt 不进入 `pending_side_effects`；
3. Evidence 引用缺失 Attempt 时必须 `BLOCKED/MISSING_ATTEMPT_HISTORY`，
   且不得伪造 pending pointer。

三项全部通过，最终独立 Gate 为 `13/13 PASS`、0 skip、0 xfail，
`blockers=[]`。此外：

```text
M1 bootstrap regression: 31/31 PASS
Core author regression:  30/30 PASS
M3 independent held-out:  1/1 PASS
old Genesis trust root:  77 checks / 7 cases PASS
M4 shadow migration:     10/10 PASS
M0a original dirty:      10/10 SHA-256 PASS
```

新 Core revision 下重新执行真实 Canary，reference Port、预绑定 validator、
Work/Attempt/Evidence 和 reducer 再次产生 `COMPLETE`；authority pointer
与四个 legacy runtime state 文件执行前后仍字节相等。M5-B01 已关闭，
M5 Hard Gate 最终通过，`task-009` 可晋升。
