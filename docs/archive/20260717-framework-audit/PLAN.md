# Plan: YuanForge 框架逻辑审计与修复

## 输入：Product Analyst 产出

| 项 | 内容 |
|----|------|
| 用户故事 | 作为 YuanForge 维护者，我想修复框架本体的逻辑断链，以便 Agent 能按 DocsOS 与 Loop Engineering 规则稳定执行。 |
| 验收标准 | Given 已完成 DocsOS v1, When Agent 启动, Then 不会将已关闭会话判为活跃；Given DocsOS 文档, When Agent 查阅知识, Then 使用存在且唯一的规范路径；Given Windows 默认控制台, When 运行 Graph 校验, Then 命令不因输出编码失败。 |
| 风险标签 | P1 |
| 功能优先级 | P1 |

## 概况

- **目标:** 统一 DocsOS 状态与关键路径引用，并使图谱校验脚本在 Windows 默认控制台可执行。
- **创建时间:** 2026-07-17
- **Architect:** Architect（Tier 3 role-switch）
- **关联需求:** 检查 YuanForge 框架逻辑问题并解决。

## 设计理解书

- **核心实体:** 全局状态入口（`PROGRESS.md`、`INDEX.md`）、长期知识目录（`knowledge/`）、会话级运行时状态（`TASK_BOARD.md`）、图谱校验脚本。
- **主要数据流:** Agent 从全局状态定位活动 Workspace；运行时任务由该 Workspace 的任务板承载；完成后知识进入 `knowledge/` 并由图谱脚本读取。
- **关键交互:** Agent 启动与崩溃恢复读取状态入口；维护者执行 `python scripts/build-graph.py --check` 验证知识图。

## 技术方案

### 架构决策

| 决策 | 推导链 |
|------|--------|
| `knowledge/` 为长期知识唯一真相源 | DocsOS 对象模型规定知识对象写入 `knowledge/` → 旧聚合文件与新目录同时承载同一语义会产生分叉 → 将旧文件改为导航入口，并迁移既有陷阱。 |
| 仅活动会话由 `PROGRESS.md` 指向 | 崩溃恢复以该指针判断活动 Workspace → 指向已结束会话会触发错误恢复 → 完成的里程碑必须清空会话指针。 |
| CLI 诊断信息使用 ASCII 标记 | 框架须在 Windows 默认编码下可运行 → Emoji 可能无法编码为 GBK → 使用 `[OK]`、`[WARN]`、`[ERROR]`。 |

### 接口与数据模型

本次不新增外部 API 或数据实体；仅修正文档路径契约与 CLI 输出契约。

## 模块划分

| 模块 | 职责 | 对应 Task | 关键文件 |
|------|------|----------|----------|
| DocsOS 状态与知识 | 修正状态入口、迁移陷阱并更新规范引用 | T01 | `docs/`, `.yuan/rules/`, `contracts/`, `protocols/` |
| 图谱校验 | 消除 Windows 编码失败并生成图谱 | T02 | `scripts/build-graph.py`, `scripts/pre-commit`, `docs/graph/` |

## Dispatch Plan

### 依赖关系

- T01（DocsOS 一致性）与 T02（脚本兼容性）互不依赖；Tier 3 受平台限制顺序执行。
- T03 至 T06 分别审查 T01 与 T02 的结果，依赖 T01、T02 完成。
- T07（验证）依赖所有审查任务完成且所有 Blocker 已解决。
- T08（会话归档）依赖 T07 通过。

### 任务派发表

| Task ID | 优 | 标题 | Role | 上游依赖 | ⏱超时 | 产出物 | 门禁 | 风险 |
|---------|----|------|------|---------|-------|--------|------|------|
| T01 | P1 | 统一 DocsOS 状态和规范路径 | doc-engineer | - | 30 | `docs/`, `.yuan/rules/`, `contracts/`, `protocols/` | G2 | P1 |
| T02 | P1 | 修复 Graph 校验的 Windows 输出兼容性 | backend-dev | - | 30 | `scripts/build-graph.py`, `scripts/pre-commit`, `docs/graph/index.json` | G2 | P1 |
| T03 | P1 | 规格对照审查 | spec-reviewer | T01,T02 | 15 | 审查结果 | G2 | P1 |
| T04 | P1 | 安全审查 | security-auditor | T01,T02 | 20 | 审查结果 | G2 | P1 |
| T05 | P2 | 质量审查 | quality-auditor | T01,T02 | 20 | 审查结果 | G2 | P1 |
| T06 | P2 | UX 适用性审查 | ux-reviewer | T01,T02 | 15 | 审查结果 | G2 | P1 |
| T07 | P1 | 执行验收验证 | tester | T03,T04,T05,T06 | 20 | 命令验证结果 | G3 | P1 |
| T08 | P2 | 归档审计结论 | doc-engineer | T07 | 10 | `SESSION_LOG.md` | G4 | P1 |

## 质量门禁

| Gate | 检查内容 | 通过标准 | 执行者 |
|------|----------|----------|--------|
| G2 | 四审查官并行 | 两个 Blocker 审查均通过；Advisory 已记录 | 四审查官 |
| G3 | 命令与引用验证 | Graph 校验、Python 编译与路径检索通过 | tester |
| G4 | 文档归档 | 会话日志记录结果与余留风险 | doc-engineer |
