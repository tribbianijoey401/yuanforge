# Merge Policy — Proposal 合并规则

> **适用范围**：Proposal 层（`docs/proposals/`）→ Knowledge 层的合并。
> **当前状态**：Proposal 层尚未实现。本文档定义未来合并规则，当前仅供 Conductor 蒸馏时参考。

---

## 一、合并时机

| 触发条件 | 合并者 |
|---------|--------|
| Agent 提交 Proposal，Conductor 审查通过 | Conductor |
| Proposal 超过 7 天未处理 | Conductor 自动关闭（不合并） |

---

## 二、合并流程

```
1. Conductor 检查:
   ├─ Proposal 的 target object 是否存在？
   ├─ target object 的 verified_commit 是否过期？→ 如果过期，先更新再合并
   └─ 是否有其他 Proposal 也在改同一个 target object？→ 冲突，按优先级处理

2. 合并操作:
   ├─ 更新 frontmatter（version +1, updated_by, updated_at）
   ├─ 替换正文中的目标章节（不是全文替换）
   └─ 如果 Proposal 增加了新依赖 → 更新 depends 字段

3. 关闭 Proposal:
   └─ 移动 proposals/<role>/prop-NNN.md → proposals/closed/
```

---

## 三、冲突处理

当两个 Proposal 修改同一个 target object：

| 优先级 | 规则 |
|--------|------|
| 1 | 先检查是否真的冲突（修改不同章节 → 不冲突，顺序合并） |
| 2 | 修改同一章节 → 按提交时间，先到的合并，后到的打回重做 |
| 3 | 两个 Proposal 来自同一 Agent → 自动串联（先合 prop-NNN，再合 prop-NNN+1） |

---

## 四、验证规则

合并前 Conductor 必须验证：

| 检查项 | 不通过的处理 |
|--------|-------------|
| Proposal 的 frontmatter 是否完整？ | 打回 Agent |
| Proposal 是否更新了 verified_commit？ | 打回 Agent（必须验代码） |
| 目标正文是否仍然有效（未被其他人改动）？ | 先更新目标，再合并 |
| 是否引用了不存在的 depends？ | 打回 Agent（错误引用） |

---

## 五、禁止事项

- ❌ 两个冲突的 Proposal 同时合并（不做 merge conflict resolution，直接排队）
- ❌ 合并时不更新 version 字段
- ❌ Proposal 关闭不通知原 Agent
