# Archive Policy — Workspace 归档规则

> **适用范围**：Workspace 关闭后的归档操作。
> **执行者**：Conductor（Workspace Close 时）。

---

## 一、归档时机

| 触发条件 | 行为 |
|---------|------|
| 所有 Task 终态 + 蒸馏完成 | 立即归档 Workspace → `archive/` |
| Workspace 超过 7 天无活动（TTL） | 强制归档（即使有未完成任务） |
| 用户指令中断 Workspace | 蒸馏已完成任务，归档剩余 |

---

## 二、归档流程

```
1. 确认蒸馏已完成:
   ├─ knowledge/ 中已有本次 Workspace 产出的 Feature/ADR/Pitfall
   └─ SESSION_LOG 已含蒸馏报告

2. 移动 Workspace:
   docs/YYYYMMDD-描述/ → docs/archive/YYYYMMDD-描述/

3. 清理:
   ├─ 无需清理 — archive/ 中的文件是完整快照，不可修改
   └─ 不删除原目录中的任何文件
```

---

## 三、TTL 规则

| 条件 | 处理 |
|------|------|
| Workspace 有活跃 🔨 任务 | TTL 从最后一次巡检时间算起 |
| Workspace 所有任务 ⏳等待 | TTL 从创建时间算起 |
| Workspace 超过 7 天 | Conductor 通知用户 → 用户决策：继续 / 强制归档 |

---

## 四、归档后访问

归档的 Workspace 仍然可读：

- `docs/archive/YYYYMMDD-描述/PLAN.md` — 回顾设计
- `docs/archive/YYYYMMDD-描述/SESSION_LOG.md` — 回顾过程
- `docs/archive/YYYYMMDD-描述/BUG-NNN.md` — 追溯 Bug

Knowledge 文件中已包含指向 archive 的链接（如 `[PLAN](../archive/YYYYMMDD-描述/PLAN.md)`）。

---

## 五、禁止事项

- ❌ 归档时修改 Workspace 中的任何文件
- ❌ 归档后删除 Workspace（archive 是永久保留）
- ❌ 蒸馏未完成就归档（必须先蒸馏，再归档）
- ❌ 单个 Workspace 保留超过 14 天不归档
