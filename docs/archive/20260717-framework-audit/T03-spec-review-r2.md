## Spec Review: T01-T02（复审）

| 验收标准 | 结果 | 备注 |
|---------|------|------|
| 已结束会话不会被恢复流程误判为活动会话 | ✅ | 恢复仅接受 `PROGRESS.md` 指向、未归档且包含 `TASK_BOARD.md` 的 Workspace；明确禁止目录扫描推断。 |
| DocsOS 路径唯一且存在 | ✅ | 旧全局文档路径已清除；陷阱知识已迁移为带 frontmatter 的对象文件。 |
| Windows 默认控制台可运行 Graph 校验 | ✅ | 实测 `python scripts/build-graph.py --check` 通过。 |

| 对抗路径 | 结果 | 备注 |
|---------|------|------|
| `docs/` 同时包含历史 Workspace 与当前 Workspace | ✅ | 历史目录不参与活跃判定；只有全局会话指针和任务板共同成立才触发恢复。 |

## 判定

✅ 通过
