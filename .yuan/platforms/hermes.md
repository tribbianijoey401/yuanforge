# Hermes Agent 平台适配

> 本文件告诉 Hermes Agent 如何执行 YuanForge 的定义。

---

## 加载规则

Hermes 的系统提示会注入 `.yuan/rules/` 下的规则文件：

| 规则 | 加载方式 |
|------|---------|
| iron-rules.md | 系统提示中注入 |
| plan-format.md | 写入 Plan 时参考 |
| .yuan/docs/ | project-bootstrap 读规格书创建 docs/ |

---

## 派发子 Agent（Conductor）

使用 Hermes 的 `delegate_task` 工具，按 12 人专家团合约派发：

```markdown
# Conductor 的标准操作：
1. 读取 Plan 中的 Dispatch Table
2. 解析依赖关系 → 构建 DAG
3. 按调度决策表依次派发：
   product-analyst → architect → frontend-dev/backend-dev
   → spec-reviewer/security-auditor/quality-auditor/ux-reviewer (并行)
   → tester → doc-engineer
4. 为每个 ready Task 调用 delegate_task，context 含：
   - Task 详细 spec
   - 对应角色合约（contracts/）
   - 铁律引用
   - 上游产出物路径
```

可选：如配置了 Kanban 系统，用 `kanban_create` 创建持久化任务板。

---

## 加载 Skill

使用 `skill_view(name)` 工具，skill 名称对应 `.yuan/skills/` 下的文件名（不含扩展名）。

示例：
```
skill_view("vibecoding-workflow")
skill_view("test-driven-development")
```

---

## 追踪进度

- `docs/PROGRESS.md` — 项目进度中枢
- `docs/YYYYMMDD-描述/SESSION_LOG.md` — 会话日志
- `docs/YYYYMMDD-描述/TASK_BOARD.md` — 运行时任务板

---

## 工具映射

| YuanForge 概念 | Hermes 工具 |
|---------------|------------|
| 派发子 Agent | `delegate_task` |
| 加载 Skill | `skill_view` |
| 项目管理 | `kanban_*` 系列 |
| 终端执行 | `terminal` |
| 文件操作 | `read_file` / `write_file` / `patch` |
| Git 操作 | `terminal` (git 命令) |

---

## 注意事项

- Hermes 的 `delegate_task` 是 **同步**的 — 父 Agent 等待子 Agent 完成
- 最多 3 个并行子 Agent（可配置 `delegation.max_concurrent_children`）
- 子 Agent 没有父会话的记忆 — 必须通过 context 传递全部信息
