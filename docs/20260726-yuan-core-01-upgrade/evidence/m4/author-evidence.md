# task-007 M4 Shadow Conversion Author Evidence

> 角色：Backend Dev（实现者自检，不替代 task-008 独立 Tester）
> 时间：2026-07-26 23:58 +08:00
> 判定：`PASS — M4 author gate`

## 实现边界

- converter 只读 `docs/` 中可识别的 legacy Workspace 与 session-bound
  `events.jsonl`，只写显式隔离的 shadow root。
- authority pointer 初始且保持 `legacy`；未修改 `AGENTS.md`、
  `docs/PROGRESS.md`、initializer、pre-commit 或任何原始 dirty 文件。
- 不双写：legacy 与 shadow writer lane 互斥，写入使用路径边界与
  compare-and-swap 哈希检查。
- 不推断成功：旧状态文本只作为 observation 重放；缺文档、缺事件、
  缺原始 typed verifier binding 全部成为 structured unresolved，
  对应 Run Memory 强制 `BLOCKED`。
- rollback 只删除通过 ownership marker、文件清单和 SHA-256 校验的
  shadow root；出现未知文件或 legacy source 哈希变化时失败关闭。

## 真实历史重放

| 项 | 结果 |
|----|------|
| 识别 Workspace | 3 |
| 覆盖 legacy source | 9 |
| 重放 task/event observation | 28 |
| schema / Core validation errors | 0 |
| structured unresolved | 19 |
| 所有 Workspace 投影结果 | `BLOCKED` |

Unresolved 分布：

- `20260707-框架v2`：5 项；缺 FEATURE、PLAN、TASK_BOARD、events 和可逐字提取的 Goal。
- `20260717-framework-audit`：2 项；缺 FEATURE 和 events；Plan Goal 已逐字提取。
- `20260726-yuan-core-01-upgrade`：12 项；原 12 条 AC 缺少 legacy
  typed verifier binding，AC 原文与必需证据已完整保留在 replay report，
  未伪造绑定。

## 回退演练

```text
shadow root: .yuan-shadow-m4-drill
projection digest: 24996128011c43454c7d5600ab12c86eb56e6e6d8c6053acca3a13e96f277826
legacy before: 0f4098281c0338df3cd5297cc69fa57810491020f69b8ff336e1a5bde20abc4c
legacy after:  0f4098281c0338df3cd5297cc69fa57810491020f69b8ff336e1a5bde20abc4c
Core rebuild checks: 3/3 PASS
rollback: ROLLED_BACK
shadow remains: false
```

结构化回执见 [rollback-receipt.json](./rollback-receipt.json)。

## 最终 Shadow Candidate

状态文档与 task-007 Event 写入 legacy authority 后重新生成最终 candidate：

```text
shadow root: .yuan-shadow
authority: legacy
workspaces: 3
covered sources: 9
replayed observations: 29
structured unresolved: 19
projection digest: c16924df49b608dd98d9d6d246d4006ac4577f5062113f816e703e9aa9513a4b
legacy snapshot: 49ab23b8bece0f0ba1543dad6362dbdd41b2eda662a129ec973757ca42206111
Core deterministic rebuild: 3/3 PASS
```

最终验证回执见 [final-verification.json](./final-verification.json)。
`.yuan-shadow/authority.json` 仍明确声明 legacy 是唯一 writable authority；
M4 未执行 authority switch。

## TDD 与对抗验证

```text
python -B -m unittest discover -s tests/shadow_migration -p "test_*.py" -v
Ran 10 tests — OK

python -B -m py_compile scripts/yuan-shadow-migrate.py \
  scripts/yuan_shadow_migrate.py scripts/yuan_shadow_support.py
PASS
```

覆盖：active pointer、历史发现、dry-run 零写入、Core schema/rebuild、
确定性重复输出、writer lane 隔离、stale CAS、路径逃逸、未知 shadow
文件拒绝、无损 rollback、Windows UTF-8 CLI。

全量回归：

```text
M1 bootstrap tests:       31/31 PASS
Core 0.1 author tests:    27/27 PASS
M3 independent held-out:  30/30 PASS
old-root bootstrap:       75 checks / 7 cases PASS
final shadow rebuild:      3/3 PASS
M0a original dirty hashes: 10/10 PASS
```
