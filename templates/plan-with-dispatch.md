# Plan: [功能名称]

> 此模板供 Architect Agent 使用。填写方括号内容后保存到 `.yuanforge/plans/{date}_{name}.md`。

---

## 概况

- **目标:** [一句话描述要交付什么]
- **创建时间:** YYYY-MM-DD
- **Architect:** [产出此 Plan 的 Agent]
- **关联需求:** [用户原始需求摘要]

---

## 技术方案

### 技术栈选择

| 层 | 选型 | 原因 |
|----|------|------|
| 语言 | [如 Python 3.11] | [原因] |
| 框架 | [如 FastAPI] | [原因] |
| 数据库 | [如 PostgreSQL] | [原因] |

### 架构决策

[关键决策简述，详细 ADR 见 docs/DECISIONS.md]

---

## 模块划分

| 模块 | 职责 | 对应 Task | 关键文件 |
|------|------|----------|---------|
| [模块 A] | [职责] | task-NNN | `src/path/` |
| [模块 B] | [职责] | task-NNN | `src/path/` |

---

## Dispatch Plan

Conductor 请按以下方案调度 Agent：

### 依赖关系

- [task-AAA]（[简述]）依赖 [task-BBB] 的 [产出物]，[可否与其他并行]
- [task-CCC]（[简述]）依赖 [task-DDD] 的 [产出物]，[可否与其他并行]

### 任务派发表

| Task ID | 标题 | Role | 上游依赖 | 产出物 | 门禁 |
|---------|------|------|---------|--------|------|
| task-001 | [如 架构设计] | architect | - | `docs/ARCHITECTURE.md` | G1 |
| task-002 | [如 数据模型] | coder | task-001 | `src/models/x.py, tests/` | G2 |
| task-003 | [如 API 实现] | coder | task-002 | `src/api/x.py, tests/` | G2 |
| task-00N | [如 集成测试] | tester | task-002,task-003 | `tests/integration/` | G3 |
| task-00N | [如 部署] | devops | task-00N | `k8s/x.yaml` | G4 |

---

## 质量门禁

| Gate | 检查内容 | 通过标准 | 执行者 |
|------|---------|---------|--------|
| G1 | Plan 完整性 | Dispatch Table 无遗漏、依赖正确、用户确认 | 用户 |
| G2 | Task 级审查 | Spec 合规 + 代码质量 APPROVED | reviewer |
| G3 | 集成测试 | `pytest tests/ -q` 全 PASS | tester |
| G4 | 交付就绪 | CI 通过 + 文档齐全 + 部署配置 | devops |
