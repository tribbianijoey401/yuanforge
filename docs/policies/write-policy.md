# Write Policy — Knowledge 写入规则

> **适用范围**：`docs/knowledge/` 下的所有对象文件。
> **平台无关**：本规则适用于任何 Agent 平台，不绑定特定工具。

---

## 一、写入条件

### 可以写

| 场景 | 路径 | 执行者 |
|------|------|--------|
| Workspace Close 蒸馏 | 直接写入 knowledge/ | Conductor |
| 纠正过期知识（confidence=stale） | 直接写入，更新 verified_commit | 任何 Agent（需先读代码验证） |
| 废弃对象（status→deprecated） | 更新 frontmatter，不改正文 | 任何 Agent |

### 不可以写（未来通过 Proposal）

| 场景 | 原因 |
|------|------|
| 两个 Agent 同时修改同一对象 | 需要 Proposal 事务保证原子性 |
| 大规模重写 Knowledge | 需要审查后 Merge |

> **当前阶段**：Proposal 层尚未实现。Conductor 在蒸馏时直接写入，不做并发控制。两个 Agent 同时修改同一 knowledge 文件的概率在当前架构下极低（蒸馏是 Conductor 独占操作）。

---

## 二、写入要求

### Frontmatter 必填字段

每次写入 knowledge/ 文件时，以下字段必须填写：

| 字段 | 说明 |
|------|------|
| `id` | 全局唯一。格式 `{TYPE}-{NNN}` |
| `object_type` | feature / decision / pitfall / module |
| `lifecycle` | 固定 `knowledge` |
| `owner` | 负责角色 |
| `status` | 由各类型状态机决定 |
| `summary` | 一句话摘要（< 200 字符） |
| `confidence` | verified / stale / draft / deprecated |

### verified_commit 规则

- 蒸馏时：取当前 `git log -1 --format=%H`
- 纠正过期知识时：取修正后的 HEAD
- 如果无法确定 → 留空（但不推荐）

### 正文规则

- 蒸馏后正文应精简（原 FEATURE.md 可能 5KB → 蒸馏后 1-2KB）
- 必须保留到 source session 的链接（如 `[PLAN](../archive/YYYYMMDD-描述/PLAN.md)`）
- 正文是 Markdown，不是原始 Workspace 文件的拷贝

---

## 三、禁止事项

- ❌ 蒸馏时省略 frontmatter（没有 id / object_type / confidence 的知识无法被索引）
- ❌ 蒸馏时修改原始 Workspace 文件（Workspace 文件归档后不可变）
- ❌ 手工维护 knowledge/ 文件（正常流程只有蒸馏和 Proposal 两种入口）
- ❌ confidence=stale 的文件直接使用而不验证（必须先检查代码）
