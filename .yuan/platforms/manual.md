# 通用 / 人工模式适配

> 本文件是 YuanForge 的**平台无关兜底方案**。
> 任何不支持自动化调度的 Agent 平台，甚至纯人类，都能按此文件操作。

---

## 平台能力描述符

```yaml
platform: manual
version: "1.0"

capabilities:
  subagent:
    supported: false
    fallback: "人工模拟：一个人扮演一个 Agent 角色，串行执行"
  parallel:
    supported: false
    fallback: "所有 Task 串行执行"
  filesystem:
    supported: true
    fallback: "人工创建/编辑文件"
  shell:
    supported: true
    fallback: "人工执行命令"
  approval:
    supported: true
  patch:
    supported: false
    fallback: "人工编辑文件"
  persistent_session:
    supported: false
    fallback: "PROGRESS.md + SESSION_LOG 作为跨会话桥梁"
  knowledge_graph:
    supported: false
    fallback: "人工浏览 knowledge/ 目录"
  event_store:
    supported: true
    fallback: "人工追加 JSONL 行"
  git:
    supported: true
    fallback: "人工执行 git 命令"

execution:
  strategies: [sequential, manual]
  defaults:
    max_retry: 1
    timeout_buffer_minutes: 0
    checkpoint_interval_minutes: 0
```

---

## 核心概念速览

YuanForge 定义了一套**角色分工 + 规则约束**的协作模式：

### 6 个角色

| 角色 | 一句话职责 |
|------|-----------|
| Architect | 分析需求，设计架构，产出 Plan |
| Conductor | 读 Plan 的 Dispatch Table，协调各角色 |
| Coder | 按 Task spec 写代码 + 测试 |
| Reviewer | 审查 Coder 的产出（Spec + Quality） |
| Tester | 集成测试，确保全线通过 |
| DevOps | CI/CD 配置，部署就绪 |

### 九条铁律

必读 `.yuan/rules/iron-rules.md`。核心要点：

1. **计划先行** — 没有 Plan 不写一行代码
2. **TDD** — Red → Green → Refactor
3. **两阶段审查** — Spec Review → Quality Review
4. **原子提交** — 一个 Task 一个 Commit
5. **上下文隔离** — 每个 Task 全新上下文
6. **文档即代码** — 决策必须落 docs/
7. **渐进式交付** — 每步可运行
8. **质量门禁** — G1→G2→G3→G4
9. **自主调度** — 按 Dispatch Table 派发

### Dispatch Table（调度表）

在 Plan 的 `## Dispatch Plan` 段中，用 Markdown 表格描述任务依赖关系。
详见 `protocols/dispatch-table.md`。

---

## 如何派发子 Agent（人工模式）

如果你所在平台**不支持**自动 fork 子 Agent：

### 方法 A：多终端并行

```bash
# 终端 1 — Coder 执行 Task A
# 告诉 Agent: "你是 Frontend Dev 角色（见 contracts/frontend-dev.md），执行 Task task-004"

# 终端 2 — Backend Dev 执行 Task B（与 A 无依赖，可并行）
# 告诉 Agent: "你是 Backend Dev 角色（见 contracts/backend-dev.md），执行 Task task-003"

# 终端 3 — 等 A 和 B 都完成后再启动
# 告诉 Agent: "你是 Spec Reviewer 角色（见 contracts/spec-reviewer.md），审查 task-002 + task-003"
```

### 方法 B：顺序执行

```bash
# 同一个终端，按 DAG 拓扑顺序逐 Task 执行
# 每个 Task 开始前，告诉 Agent 切换角色
# 例："现在你是 Architect 角色，读 contracts/architect.md，执行 task-001"
```

### 方法 C：用 AGENTS.md 引导

大多数现代 Agent 平台（Cursor、Claude Code、Codex CLI）会**自动读取**根目录的 `AGENTS.md`。
你只需告诉 Agent："按照 YuanForge 框架开发这个项目"，它自会找到规则。

---

## 如何加载 Skill

Skill 是纯 Markdown 文件，位于 `.yuan/skills/` 下。
**直接读取即可。** 不需要任何特殊的"加载"机制。

```
# 例如：需要写 Plan
Agent 读取: .yuan/skills/writing-plans.md

# 例如：需要引导式 TDD
Agent 读取: .yuan/skills/test-driven-development.md
```

---

## 如何追踪进度

1. 读写 `docs/PROGRESS.md` — 这是项目的**进度中枢**
2. 每个 Task 完成后更新 PROGRESS.md
3. 遇到阻塞记录在「阻塞项」栏

---

## 平台能力矩阵

| 平台 | 自动读取规则 | 自动派发子Agent | 推荐模式 |
|------|------------|----------------|---------|
| **Cursor** | ✅ AGENTS.md | ❌ | 方法 C（AGENTS.md 引导） |
| **Claude Code** | ✅ CLAUDE.md | ✅ 子进程 | 方法 A 或 C |
| **Codex CLI** | ✅ AGENTS.md | ✅ sandbox | 方法 A 或 C |
| **GitHub Copilot Chat** | ✅ AGENTS.md | ❌ | 方法 B（顺序执行） |
| **任何终端 + LLM** | ❌ | ❌ | 方法 A 或 B |
| **Human（人工）** | ❌ | ❌ | 方法 A — 每人一个终端 |

---

> **关键原则：YuanForge 是规则，不是代码。只要你理解了角色分工和铁律，用什么工具执行并不重要。**
