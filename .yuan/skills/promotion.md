---
name: promotion
description: "知识晋升管线 — Workspace Close 时将长期知识从 Runtime 提取到 Knowledge。FEATURE→features/, ADR→decisions/, BUG→pitfalls(if repeatable)。确定性规则：EXTRACT→VALIDATE→PROPOSE→MERGE。Conductor 在 Phase 6 执行。"
version: 1.0.0
---

# promotion — 知识晋升管线

> **定位**：Skill（可复用方法），不是协议。被 workflow-protocol Phase 6 调用。
> 定义从 Workspace 到 Knowledge 的确定性晋升流程。
> 所有长期知识必须经过同一管线。禁止 Runtime 直接修改 Knowledge。

---

## 一、设计原则

```
当前（LLM 驱动）:
  Conductor 读完 Workspace → 自己判断"哪些值得蒸馏" → 手动创建 knowledge/ 文件

目标（管线驱动）:
  Workspace Close → Candidate 提取 → 规则验证 → Proposal 生成 → Merge → Knowledge
```

| 步骤 | 谁执行 | 依赖 LLM？ |
|------|--------|:---:|
| Candidate 提取 | Rule Engine | ❌ 确定性规则 |
| Candidate 验证 | Rule Engine | ❌ 确定性规则 |
| Proposal 生成 | Promotion Pipeline | ❌ 模板填充 |
| Merge | Rule Engine | ❌ 确定性规则 |

---

## 二、管线总览

```
Workspace Close
    │
    ▼
┌─────────────────┐
│ 1. EXTRACT      │  从 Workspace 提取 Candidate
│    Candidates   │  - FEATURE.md → feature candidate
│                 │  - ADR-NNN.md → decision candidate
│                 │  - BUG-NNN.md → pitfall candidate (if repeatable)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ 2. VALIDATE     │  规则验证（确定性）
│    Candidates   │  - frontmatter 完整性检查
│                 │  - depends 引用检查
│                 │  - status 转换合法性
│                 │  - verified_commit 存在性
└────────┬────────┘
         │
    ┌────┴────┐
    ▼         ▼
  PASS       FAIL
    │         │
    │         └──→ reject.log（记录原因）
    ▼
┌─────────────────┐
│ 3. PROPOSE      │  自动生成 Proposal
│    Auto-gen     │  - 从 Candidate 填充 Proposal 模板
│                 │  - frontmatter 自动映射
│                 │  - 正文从 Workspace 源文件精简
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ 4. MERGE        │  确定性合并规则
│    to Knowledge  │  - 无冲突 → 直接写入 knowledge/
│                 │  - 有冲突（同 ID 已存在）→ 按规则处理
│                 │  - 写 KNOWLEDGE_UPDATED 事件
└────────┬────────┘
         │
         ▼
    Knowledge/
    ├── features/FEAT-NNN.md
    ├── decisions/ADR-NNN.md
    └── pitfalls/PIT-NNN.md
```

---

## 三、Step 1: Candidate 提取（确定性规则）

### 提取规则

| Workspace 源文件 | 提取为 | 提取条件 |
|-----------------|--------|---------|
| `FEATURE.md` | feature candidate | 总是提取 |
| `ADR-NNN.md` | decision candidate | 总是提取 |
| `BUG-NNN.md` | pitfall candidate | 见判断规则 |
| `PLAN.md` | 不提取 | 未完成任务 → workspace/backlog |
| `TASK_BOARD.md` | 不提取 | Runtime 状态 |
| `SESSION_LOG.md` | 不提取 | Human 日志 |

### BUG → Pitfall 判断规则（确定性）

```
if BUG.severity == "🔴阻断":
    → 提取为 pitfall candidate（阻断级 bug 值得 Agent 提前知道）

elif BUG.root_cause 匹配已知模式:
    - "N+1 query" → 提取
    - "race condition" → 提取
    - "memory leak" → 提取
    - "hardcoded secret" → 提取
    - "missing validation" → 提取

elif BUG 在同一 Workspace 中出现 ≥2 次:
    → 提取（重复出现 = 值得记录）

else:
    → 不提取 → 留在 archive
```

### Candidate 结构

```yaml
candidate:
  source: "FEATURE.md"
  source_workspace: "20260709-用户认证"
  target_type: "feature"
  proposed_id: "FEAT-AUTH"         # 从 FEATURE.md 标题推断，或自动分配
  frontmatter:
    id: "FEAT-AUTH"
    object_type: "feature"
    lifecycle: "knowledge"
    owner: "architect"             # 从 FEATURE.md 的「负责角色」提取
    status: "verified"             # Workspace Close = 审查已通过
    summary: ""                    # 从 FEATURE.md「需求描述」提取
    depends: []                    # 从 FEATURE.md「关联」段提取
    verified_commit: ""            # 取当前 HEAD
    confidence: "verified"
  body: ""                         # 从 FEATURE.md 精简
```

---

## 四、Step 2: Candidate 验证（确定性规则）

### 验证 Checklist

| # | 检查项 | 规则 | 不通过处理 |
|---|--------|------|-----------|
| 1 | frontmatter 完整性 | id / object_type / lifecycle / owner / status / summary / confidence 都存在 | reject: "缺少必填字段: [field]" |
| 2 | depends 引用 | depends 中每个 ID 都存在于现有 knowledge/ 或本次 Promotion 的产出中 | reject: "未知依赖: [id]" |
| 3 | ID 唯一性 | proposed_id 不与现有 knowledge/ 中的 ID 冲突 | conflict → 走冲突规则 |
| 4 | verified_commit | 必须填充 | warn: "未填 verified_commit"，仍通过 |
| 5 | summary 长度 | ≤ 200 字符 | truncate |
| 6 | status 合法性 | 由 object_type 的状态机允许 | reject: "非法状态转换" |

### ID 冲突规则

```
if knowledge/ 中已存在同 ID 对象:
    if 现有对象.status == "deprecated":
        → 允许覆盖（deprecated 对象被新版本取代）
    elif 现有对象.verified_commit == HEAD:
        → 跳过（同一 commit 产出的重复蒸馏）
    else:
        → 生成新 ID（后缀递增: FEAT-AUTH → FEAT-AUTH-2）
        → warn: "ID 冲突，自动分配新 ID"
```

---

## 五、Step 3: Proposal 自动生成

### 模板填充（确定性）

```
Candidate.frontmatter → Proposal 变更内容（frontmatter 字段一一映射）

Candidate.body:
  从 Workspace 源文件按规则精简:
    FEATURE.md:
      保留: 需求描述（2-3句） / 设计思路 / API 端点 / 关键文件
      丢弃: 会话元信息 / 完整代码 / Debug 过程
    ADR-NNN.md:
      保留: 背景 / 决策 / 备选方案 / 后果（完整）
      丢弃: 无（ADR 格式已经很精简）
    BUG-NNN.md (→ pitfall):
      保留: 现象 / 根因 / 修复 / 教训
      丢弃: 完整堆栈 / 调试日志
```

### Proposal 元数据

```yaml
id: "prop-auto-042"
status: "submitted"
target_object: "FEAT-AUTH"
author: "promotion-pipeline"       # 自动生成的 Proposal 标记此 author
change_type: "distill"
summary: "蒸馏自 Workspace: 20260709-用户认证"
depends_on: []
```

---

## 六、Step 4: Merge 到 Knowledge

### 合并规则（确定性）

```
1. 识别目标文件:
   knowledge/{target_type}s/{proposed_id}.md

2. 目标文件不存在:
   → 直接创建（从 Proposal 填充）

3. 目标文件存在:
   ├─ Proposal.change_type == "distill":
   │   └─ 目标文件由同一 Workspace 生成 → 跳过（幂等）
   │   └─ 目标文件由不同 Workspace 生成 → ID 冲突规则（见 Step 2）
   │
   ├─ Proposal.change_type == "update":
   │   └─ 更新 frontmatter + 替换正文对应章节
   │
   └─ Proposal.change_type == "deprecate":
       └─ 只改 frontmatter.status = "deprecated"，不动正文

4. 写入 KNOWLEDGE_UPDATED 事件

5. 运行 build-graph.py
```

---

## 七、与 Conductor 的关系

Promotion Pipeline 不替代 Conductor——它替代 Conductor 中**不需要 LLM 判断**的部分。

| 操作 | 谁做 | 为什么 |
|------|------|--------|
| 判断 BUG 是否值得蒸馏 | Pipeline（规则匹配） | 有确定性标准 |
| 提取 FEATURE/ADR | Pipeline（规则提取） | 有固定格式 |
| 验证 frontmatter | Pipeline（规则检查） | 有 Checklist |
| 合并到 knowledge/ | Pipeline（规则合并） | 有合并规则 |
| **判断"这个 Feature 的 summary 怎么写"** | Conductor（LLM） | 需要语义理解 |
| **判断"这个决策的后果是什么"** | Conductor（LLM） | 需要分析能力 |
| **处理 Pipeline 无法自动处理的异常** | Conductor（LLM） | 需要判断 |

---

## 八、拒绝日志

Pipeline 验证失败的 Candidate 写入 `docs/reject.log`：

```jsonl
{"timestamp":"...","candidate":"FEAT-AUTH","reason":"缺少必填字段: summary","workspace":"20260709-用户认证"}
{"timestamp":"...","candidate":"ADR-005","reason":"未知依赖: FEAT-NOTFOUND","workspace":"20260709-用户认证"}
```

Conductor 定期检查 reject.log，处理需要人工判断的拒绝项。

---

## 九、NF-09 变更路由（← 吸收）

Promotion Pipeline 合并知识时，必须考虑变更对知识面的影响：

| 变更类型 | 影响知识面 | 处理 |
|---------|-----------|------|
| 新增 feature | features/ + ARCHITECTURE.md | 直接 distill |
| API 变更 | features/ + API docs + INDEX.md | 同步更新所有引用 |
| 数据模型变更 | features/ + ARCHITECTURE.md + migration docs | 标记旧 schema deprecated |
| 依赖变更 | setup docs + knowledge/features/ | 更新 depends 链 |
| 规则/合约变更 | rules/ + contracts/ | 同步验证引用 |
| 配置变更 | SETUP.md + knowledge/features/ | 记录变更前后对比 |
| 测试策略变更 | knowledge/pitfalls/ + testing docs | 更新测试覆盖率 |
| 文档格式变更 | 所有 docs 的格式一致性 | 全量扫描 |
| 生命周期变更 | knowledge/ 状态机 | 检查状态合法性 |

## 十、与现有规格书的关系

| 规格书 | 关联 |
|--------|------|
| RUNTIME_MODEL.md | Candidate/Proposal/Checkpoint 对象定义 |
| OBJECT_MODEL.md | Knowledge 对象 Schema（验证依据） |
| PROPOSAL.md | Proposal 生命周期和格式 |
| SESSION.md | Workspace Close 触发 Promotion Pipeline |
| EVENTS.md | Pipeline 产出 KNOWLEDGE_UPDATED 事件 |
| verification-policy.md | 晋升前必须完成六维验证（NF-02）+ 证据层级（NF-10） |
