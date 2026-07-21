# 通用 / 人工模式适配

> 本文件是 YuanForge 的**平台无关兜底方案**。
> 任何不支持自动化调度的 Agent 平台，甚至纯人类，都能按此文件操作。

---

## 平台能力描述符

```yaml
platform: manual
version: "2.0"

capabilities:
  subagent: false
  parallel: false
  filesystem: manual
  shell: manual
  persistent_session: false
  knowledge_graph: false
  event_store: manual
  git: manual

execution:
  strategies: [sequential, manual]
```

---

## 核心概念速览

YuanForge 定义了一套 **Protocol-First** 协作模式：5 份协议 + 12 人专家团 + 十条铁律。

### 12 人专家团

| 角色 | 档位 | 一句话职责 |
|------|:---:|-----------|
| Product Analyst | — | vibe → 用户故事 + 验收标准 + 风险标签(R0/R1/R2) |
| Architect | — | 计划复盘 → API 契约冻结 + Plan |
| UI Designer | — | 视觉规范 + 交互原型 |
| Frontend Dev | — | 前端 TDD 实现 |
| Backend Dev | — | 后端 TDD 实现 |
| Spec Reviewer | 🔴 Blocker | 对抗式审查：验收标准 + API 契约 |
| Security Auditor | 🔴 Blocker | 分级安全审计（P0/P1/P2） |
| Quality Auditor | 🟢 Advisory↗ | 代码质量 + 性能 + DB（同类 3 次升级） |
| UX Reviewer | 🟢 Advisory↗ | UI 还原度 + 无障碍（有界面时） |
| Tester | 🟡 Hard Gate | 全量测试 + 修复回路路由 |
| Doc Engineer | — | 增量归档 + 阶段整合 |
| Conductor | — | 工作流解释器：读 Protocol → 产生 Action → 调 Adapter |

### 十条铁律

必读 `.yuan/rules/iron-rules.md` + `.yuan/specs/`（5 份协议）。核心要点：

1. **计划先行** — 没有 Plan 不写一行代码
2. **TDD** — Red → Green → Refactor
3. **三档审查** — 4 审查官并行：🔴Blocker / 🟡Hard Gate / 🟢Advisory↗
4. **原子提交** — 一个 Task 一个 Commit
5. **上下文隔离** — 每个 Task 全新上下文
6. **文档即代码** — 决策必须落 docs/
7. **渐进式交付** — 每步可运行
8. **质量门禁** — G1→G2→G3→G4，含三档阻塞策略
9. **自主调度** — Conductor 按调度循环派发
10. **循环收敛** — 每个循环必须有闸门，不得"直到正确为止"

---

## Action 映射（Adapter Protocol §三）

本平台如何实现 8 个统一 Action：

```yaml
platform: manual
transport: human-operated

dispatch:
  implementation: prompt_user
  notes: |
    提示用户:
    1. 打开 contracts/<role>.md 了解角色合约
    2. 读 TASK_BOARD.md 找到 🟢就绪 任务
    3. 以对应角色身份执行 Task
    4. 完成后更新 TASK_BOARD.md 状态行

review:
  implementation: prompt_user
  notes: |
    提示用户:
    1. 选择审查角色（spec-reviewer / security-auditor / quality-auditor / ux-reviewer）
    2. 读对应合约 + 验收标准
    3. 执行审查（合规路径 + 对抗路径）
    4. 输出审查报告（独立呈现）

snapshot:
  implementation: manual_checkpoint
  notes: "提示用户记录当前进度到 agents/<role>.yaml"

checkpoint:
  implementation: manual_archive
  notes: "提示用户打包 Workspace"

recover:
  implementation: manual_check
  notes: "提示用户检查 TASK_BOARD 异常并手动恢复"

archive:
  implementation: manual_move
  notes: "提示用户移动 Workspace 目录到 archive/"

promote:
  implementation: manual_extract
  notes: |
    提示用户按 distillation-checklist 执行:
    1. FEATURE.md → knowledge/features/
    2. ADR → knowledge/decisions/
    3. BUG → 判断 → knowledge/pitfalls/ 或跳过
    4. 运行 scripts/build-graph.py
```

---

## 如何派发子 Agent（人工模式）

如果你所在平台**不支持**自动 fork 子 Agent：

### 方法 A：多终端并行

```bash
# 终端 1 — Frontend Dev 执行 Task A
# 告诉 Agent: "你是 Frontend Dev（见 contracts/frontend-dev.md），执行 Task T03"

# 终端 2 — Backend Dev 执行 Task B（与 A 无依赖，可并行）
# 告诉 Agent: "你是 Backend Dev（见 contracts/backend-dev.md），执行 Task T04"

# 终端 3 — 等 A 和 B 都完成后再启动 4 审查官并行
```

### 方法 B：顺序执行

```bash
# 同一个终端，按 DAG 拓扑顺序逐 Task 执行
# 每个 Task 开始前，告诉 Agent 切换角色
# 例："现在你是 Architect，读 contracts/architect.md，执行 Task T01"
```

### 方法 C：用 AGENTS.md 引导

大多数现代 Agent 平台（Cursor、Claude Code、Codex CLI）会**自动读取**根目录的 `AGENTS.md`。
你只需告诉 Agent："按照 YuanForge 框架开发这个项目"，它自会找到规则。

---

## 如何加载 Skill 和协议

所有 YuanForge 定义都是 Markdown 文件：
- **5 份协议**：`.yuan/specs/object-protocol.md` 等 — 纯规范，定义对象/状态/动作/流程/适配
- **9 条铁律**：`.yuan/rules/iron-rules.md`
- **Skill**：`.yuan/skills/` — **直接读取即可**，不需要特殊加载机制

```
# 例如：需要写 Plan
Agent 读取: .yuan/skills/writing-plans.md

# 例如：需要 TDD
Agent 读取: .yuan/skills/test-driven-development.md

# 例如：需要了解工作流
Agent 读取: .yuan/specs/workflow-protocol.md
```

---

## 如何追踪进度

1. 读写 `docs/PROGRESS.md` — 项目的**进度中枢**
2. 读写 `docs/YYYYMMDD-描述/TASK_BOARD.md` — 运行时任务板
3. 每个 Task 完成后更新状态
4. 遇到阻塞记录在「阻塞」表

---

## 平台能力矩阵

| 平台 | 自动读取规则 | 自动派发子Agent | 推荐模式 |
|------|------------|----------------|---------|
| **Hermes** | ✅ | ✅ (delegate_task) | 自动 |
| **Cursor** | ✅ AGENTS.md | ❌ | 方法 C（AGENTS.md 引导） |
| **Claude Code** | ✅ | ✅ 子进程 | 方法 A 或 C |
| **Codex CLI** | ✅ | ✅ sandbox | 方法 A 或 C |
| **GitHub Copilot Chat** | ✅ | ❌ | 方法 B（顺序执行） |
| **任何终端 + LLM** | ❌ | ❌ | 方法 A 或 B |
| **Human（人工）** | ❌ | ❌ | 方法 A — 每人一个终端 |

---

> **关键原则：YuanForge 是协议，不是代码。LLM 即 Runtime——你读协议、解释协议、执行协议。用什么工具执行并不重要。**
