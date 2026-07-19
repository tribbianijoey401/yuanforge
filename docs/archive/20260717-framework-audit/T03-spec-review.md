## Spec Review: T01-T02

| 验收标准 | 结果 | 备注 |
|---------|------|------|
| 已结束会话不会被恢复流程误判为活动会话 | ❌ | `AGENTS.md` 仍要求扫描 `docs/YYYYMMDD-*`；未定义“活跃”的可判定条件，历史目录仍可能触发恢复提示。 |
| DocsOS 路径唯一且存在 | ✅ | 关键规则、合约、协议与 Memory Skill 已指向存在的 DocsOS 目录。 |
| Windows 默认控制台可运行 Graph 校验 | ✅ | 实测 `python scripts/build-graph.py --check` 通过。 |

| 对抗路径 | 结果 | 备注 |
|---------|------|------|
| `docs/` 同时包含历史 Workspace 与当前 Workspace | ❌ | 仅按目录名扫描无法判断活动状态，必须以 `PROGRESS.md` 的会话指针和 `TASK_BOARD.md` 存在性作为唯一判据。 |

## 判定

🔴 Blocker（1 项未通过）：恢复模式必须以 `PROGRESS.md` 的当前会话指针为唯一入口，不能通过扫描历史目录推断活跃 Workspace。
