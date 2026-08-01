---
name: migration
title: YuanForge Core 迁移日志
description: Phases 1-9 迁移完整记录，含新增/删除文件清单和验收状态
category: documentation
stage: published
created_at: 2026-08-01
author: framework-team
---

# Migration Log — YuanForge Core Architecture

> **迁移日期**：2026-08-01
> **基线 Tag**：`yuanforge-core-v1.0`
> **迁移路线**：9 阶段渐进式迁移（shishi.plan）

---

## 迁移总结

| Phase | 描述 | 状态 | Commit |
|-------|------|------|--------|
| Phase 1 | 建立 Core 骨架（PROTOCOL, INVARIANTS, REDUCER, schemas） | ✅ | `624dc2d` |
| Phase 2 | Proposal 组合规范（4 试点角色） | ✅ | `624dc2d` |
| Phase 3 | 最小校验投影（core_validator.py + 15 测试） | ✅ | `624dc2d` |
| Phase 4 | 迁移全部 13 个 Agent 合约到 extensions/ | ✅ | `624dc2d` |
| Phase 5 | 建立 Shadow Runtime（runner + evaluator） | ✅ | `624dc2d` |
| Phase 6 | 切换唯一状态源（STATE.md 派生视图） | ✅ | `624dc2d` |
| Phase 7 | 迁移 Workflow/Policy/Skill 到 extensions/ | ✅ | `12e00ac` |
| Phase 8 | Adapter 与平台 Goal（capability_adapter.py） | ✅ | `1fc4d3f` |
| Phase 9 | Legacy 收缩（本次） | ✅ | 本次 |

---

## 新增文件

```
.yuan/core/
├── PROTOCOL.md          # Core 权威定义
├── INVARIANTS.md        # 安全不变量
├── REDUCER.md           # 确定性 reducer 决策表
├── schemas/             # 7 个核心 Schema（WORK, STATE, PROPOSAL, ATTEMPT, EVIDENCE, JOURNAL, CHANGE）
├── validators/
│   ├── MANIFEST.md      # Validator 注册表
│   └── trust-boundary.md # 信任边界
└── CONFLICT_RULES.md    # 冲突解决规则

.yuan/extensions/
├── MANIFEST.md          # 扩展注册表
├── agents/roles/        # 13 个角色合约（architect, backend-dev, frontend-dev, tester, conductor,
│   ├── architect.md
│   ├── backend-dev.md
│   ├── conductor.md
│   ├── design-reviewer.md
│   ├── doc-engineer.md
│   ├── frontend-dev.md
│   ├── product-analyst.md
│   ├── quality-auditor.md
│   ├── security-auditor.md
│   ├── spec-reviewer.md
│   ├── tester.md
│   ├── ui-designer.md
│   └── ux-reviewer.md
├── workflows/           # 5 个可选 Workflow
│   ├── tdd-loop.md
│   ├── phase-gates.md
│   ├── atomic-commit.md
│   ├── role-isolation.md
│   └── promotion.md
├── policies/            # 3 个可选 Policy
│   ├── three-level-review.md
│   ├── per-task-commit.md
│   └── evidence-binding.md
└── skills/              # 6 个可选 Skill
    ├── test-driven-development.md
    ├── subagent-driven-development.md
    ├── knowledge-distillation.md
    ├── debug-feedback-loop.md
    ├── grilling.md
    └── promotion.md

.yuan/platforms/
├── hermes.md            # Hermes 平台适配
├── manual.md            # 人工模式适配
└── capabilities.md      # 统一 Capability 声明格式

.yuan/runtime/
├── runner.py            # Shadow Runtime 主循环
├── shadow_evaluator.py  # Shadow 评估器
├── generate_views.py    # 视图生成器
└── capability_adapter.py # 平台 Capability 映射

scripts/validation/
├── core_validator.py    # 完整验证器（33KB）
├── phase3-tests.py      # Phase 3 测试（15 项）
├── phase7-tests.py      # Phase 7 测试（12 项）
└── phase8-tests.py      # Phase 8 测试（8 项）

work/
├── STATE.md             # 唯一状态源
└── views/               # 派生视图（TASK_BOARD, PROGRESS, SESSION）
```

---

## 删除文件

| 文件/目录 | 删除原因 | 替代机制 |
|----------|---------|---------|
| `scripts/setup-phase2.sh` | 旧安装脚本，无调用者 | Phase 3-8 直接运行 Python 脚本 |
| `scripts/validate-final.sh` | 旧验证脚本 | `core_validator.py` + `phase3-tests.py` |
| `lib/` | 旧审计库 | Core Validator 内置校验 |
| `migration/` | 迁移过程文件 | 本迁移文档 |
| `docs/IMPLEMENTATION_PHASE2.md` | 过程文档 | 归档到 git log |
| `docs/knowledge_analysis_report.md` | 过程文档 | 归档到 git log |
| `docs/validation-hook-spec.md` | 过程文档 | 归档到 git log |
| `trust-boundary.md` 旧引用 | 指向已删除文件 | 更新为当前路径 |

---

## 保留文件（未迁移但必要）

| 文件 | 原因 |
|------|------|
| `contracts/` | 仍被平台文档引用（hermes.md, manual.md），作为 Agent 启动指引 |
| `.yuan/skills/` | 仍被平台文档和 runtime metadata 引用，作为 skill_view 加载源 |
| `.yuan/specs/` | 5 份核心协议（未迁移），仍为框架权威定义 |
| `.yuan/rules/` | 铁律和约定（未迁移），仍为框架权威定义 |
| `.yuan/docs/` | 文档格式规格书（未迁移），仍为框架权威定义 |

> **注意**：`contracts/` 和 `.yuan/skills/` 是 Legacy 引用，未来 Phase 9 收尾时可逐步清除。

---

## 关键 Bug 修复

| 问题 | 修复 | Commit |
|------|------|--------|
| `read_state()` 无法解析带 markdown 代码围栏的 STATE.md | 添加 YAML 提取逻辑 | `624dc2d` |
| T7 测试因浅拷贝导致 BASE_PROPOSAL 被污染 | 使用 `copy.deepcopy` | `624dc2d` |
| Reducer 空 Evidence 时返回 COMPLETE（vacuous truth） | 要求 `len(evidence_list) > 0` | `1fc4d3f` |
| `extensions` 字段在 Core Schema 中为必填 | 改为可选（由 RoleExtensionValidator 校验） | `1fc4d3f` |

---

## 验收状态

| 验收项 | 状态 |
|--------|------|
| Core 完整性（7 Schema + 6 结果 Reducer + 7 不变量） | ✅ |
| 13 角色合约迁移 | ✅ |
| Shadow Runtime 验证 | ✅ |
| STATE.md 唯一状态源 | ✅ |
| Extension 架构（可选/禁用不影响 Core） | ✅ |
| Platform Capability 映射 | ✅ |
| 所有测试套件通过（15+12+8=35 项） | ✅ |
