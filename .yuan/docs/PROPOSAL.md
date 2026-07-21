---
name: PROPOSAL
description: >
  文档格式规格书：提案事务格式
spec_type: document-format
version: "3.0.0"
---

# PROPOSAL — 提案事务规格书

> 管辖 `docs/proposals/`。Proposal 是 Knowledge 层的写事务——保证原子性和并发安全。

---

## 一、设计铁律

| # | 铁律 | 推导 |
|---|------|------|
| Ⅰ | **Proposal 是 Transaction，不只是审批。** 核心价值是原子性，审批是副产品 | 两个 Agent 改同一对象 = 写冲突，Transaction 解决 |
| Ⅱ | **只保护 Knowledge 层。** Runtime 层（TASK_BOARD）直接写 | Runtime 有 TTL，不需要事务保护 |
| Ⅲ | **Proposal 是临时的。** 合并后移动到 closed/，不永久保留 | 否则 proposals/ 会像 SESSION_LOG 一样膨胀 |
| Ⅳ | **一个 Proposal = 一个 Target Object。** 不能跨对象 | 跨对象的事务复杂度远超收益 |

---

## 二、目录结构

```
docs/proposals/
├── architect/
│   └── prop-NNN.md          ← 活跃 Proposal
├── backend-dev/
├── frontend-dev/
├── quality-auditor/
│   └── ...
└── closed/                  ← 已处理的 Proposal（合并/拒绝/过期）
    └── prop-NNN.md
```

每个 Agent 角色有自己的子目录，Proposal 按角色隔离。

---

## 三、Proposal 生命周期

```
Agent 创建 Proposal
  │
  ▼
Draft ─── Agent 可以修改
  │
  ▼
Submitted ─── 等待 Conductor 处理
  │
  ├──→ Merged ──→ 移动到 closed/
  ├──→ Rejected ─→ 移动到 closed/（附原因）
  └──→ Expired ──→ 超过 7 天未处理，自动关闭
```

---

## 四、Proposal 格式

```markdown
---
id: prop-042
status: submitted
target_object: FEAT-AUTH
target_file: knowledge/features/FEAT-AUTH.md
author: architect
created: "2026-07-09T18:00:00Z"
change_type: update_status
summary: "Update FEAT-AUTH status to deprecated after OAuth migration"
depends_on: []
---

# Proposal: [标题]

## 动机
[为什么要改？关联哪个 ADR / 哪个决策？]

## 变更内容

### Frontmatter 变更
| 字段 | 原值 | 新值 |
|------|------|------|
| status | verified | deprecated |
| confidence | verified | deprecated |
| updated_by | architect | architect |

### 正文变更
[新增/修改/删除的章节和内容]

## 验证
- [x] 已读目标对象当前正文，确认变更合理
- [x] 已检查 depends 列表，无断裂引用
- [x] 已验证 affected files（如有）与 proposal 一致

## 影响分析
- 依赖此对象的其他对象：[FEAT-LOGIN 的 depends 包含 FEAT-AUTH]
- 是否需要同时更新其他文件：[是/否，列出]
```

---

## 五、Conductor 处理规则

### 5.1 收到 Proposal 后

```
1. 检查 target_object 是否存在 → 不存在 → Rejected
2. 检查是否有其他 Proposal 也在改同一 target_object：
   ├─ 没有 → 处理当前 Proposal
   └─ 有且状态为 submitted → 排队（先到先处理）
3. 验证 Proposal：
   ├─ depends_on 列表中的 Proposal 是否已处理？→ 未处理 → 等待
   ├─ frontmatter 变更是否合法（状态机允许此转换？）
   └─ 正文变更是否在目标文件的有效章节内？
4. 合并：
   ├─ 更新 frontmatter（version +1）
   ├─ 应用正文变更（替换目标章节，非全文替换）
   └─ 写入 KNOWLEDGE_UPDATED 事件
5. 移动到 closed/
```

### 5.2 冲突处理

```
两个 Proposal 修改同一 target_object:
  ├─ 修改不同章节 → 不冲突，按提交顺序依次合并
  ├─ 修改同一章节 → 先到先合并，后到的打回（附冲突说明）
  └─ 来自同一 Agent → 自动串联合并（prop-042 → prop-043）
```

---

## 六、当前阶段

> **Proposal 层是远期架构。** 当前阶段：
> - 目录骨架已创建（`docs/proposals/`）
> - Conductor 蒸馏时直接写入 Knowledge（无并发风险—蒸馏是独占操作）
> - Agent 纠正过期知识时直接写入（单 Agent 操作）
>
> **触发 Proposal 层的条件**：
> 1. 超过 3 个 Agent 同时活跃
> 2. 出现第一次并发写冲突
> 3. 用户明确要求 Knowledge 变更需要审批

在此之前，Proposal 目录和格式存在但 Conductor 不强制走 Proposal 流程。

---

## 七、与 Events 的关系

| | Proposal | Event |
|----|:---:|:---:|
| 时机 | 修改前 | 修改后 |
| 内容 | 计划（我想改什么） | 事实（改了什么） |
| 可拒绝 | 是 | 否（已经发生） |
| 存储 | proposals/ → closed/ | events/YYYYMMDD/events.jsonl |

> Proposal = 意图，Event = 事实。两者互补。

---

## 八、生命周期

| 阶段 | 操作 | 执行者 |
|------|------|--------|
| Agent 需要修改 Knowledge | 创建 Proposal（draft） | Agent |
| 确认变更 | draft → submitted | Agent |
| Conductor 审查 | 验证 + 合并 → merged | Conductor |
| 不通过 | 打回 → rejected（附原因） | Conductor |
| 超过 7 天 | submitted → expired | Conductor（自动） |
