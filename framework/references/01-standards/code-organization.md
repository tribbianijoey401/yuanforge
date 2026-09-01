---
id: code-organization
title: 代码组织启发式（Project-native First · 边界与复杂度）
domain: agentic-delivery
category: 01-standards
difficulty: advanced
tags: [code-organization, project-native, module-boundary, cognitive-complexity, 单一职责, 文件拆分]
quality_score: 95
last_updated: 2026-09-01
---

# 代码组织启发式

## Project-native First

生成代码的结构问题通常是职责、依赖和变化原因混在一起，导致难读、难测、难改。本 Reference 提供识别和改善这些问题的启发式；它不要求所有项目采用同一目录、controller → service → repository、文件长度或拆分方式。

先从目标模块、相邻实现、测试和 `ARCHITECTURE` 提取已有 boundary、依赖方向、错误模型、生命周期与命名方式。只有现有结构无法承载本次变化，且候选调整能以更低认知复杂度解释时，才提出改变。已有 adapter → application → domain、feature slice、CQRS 或其他已验证结构必须保留，除非 Task 明确改变它。

## Boundary Signals

| Signal | 调查问题 | 候选改善 |
|---|---|---|
| 职责混合 | 同一单元是否承担互不相关的变化原因？ | 按稳定职责或 feature seam 拆分，并保留 / 改善测试入口 |
| 依赖漂移 | 依赖是否绕过了项目既有公开 boundary？ | 回到项目已有的公开接口，不新建模板层 |
| 浅接口 | 调用者是否必须理解实现细节或不停透传参数？ | 仅在能隐藏真实复杂度时引入更深模块 |
| 巨型或碎片化文件 | 长度、分支、依赖或跳转是否破坏理解？ | 先定位复杂度来源；只有拆分实际降低负担时拆分 |
| transport / domain / persistence 泄漏 | 当前项目的错误、事务、状态或生命周期是否难以推理？ | 沿用现有边界把泄漏收回到合适模块 |
| 无边界 helper | `utils` 是否吸收业务能力且无法定位 owner？ | 将业务能力放回项目现有 module；纯 helper 才留在 utils |

文件行数、目录名称和三层示意只能作为调查 Signal，不能单独构成“不合格”或退回理由。

## New-project Starting Points

当 Repository 没有可复用设计时，可从分离 transport、业务规则、数据访问和基础设施开始；前端也可分开页面组装、复用组件、数据访问和 UI state。它们是可调整的起点，不是强制目录模板。每次选择都写出：约束 → 所需能力 → 方案 → 验证。

## Review Evidence

审查或重构建议应提供相邻实现、依赖图、测试 seam 或实际 Diff，说明候选结构如何减少复杂度、保持哪些不变量、为何没有采用明显替代方案。没有这种 Evidence 时，固定层级、文件行数或入口形态只能触发继续调查。

## Self-check

- [ ] 已确认 Project-native module、依赖、错误、事务 / 生命周期 boundary。
- [ ] 每个调整都有可解释的职责或复杂度收益。
- [ ] 新接口沿用当前项目的公开 boundary，未为了形式引入新 abstraction。
- [ ] 测试 seam 在调整后保持或更清楚。
- [ ] 没有把文件长度、目录名字或三层形状当作唯一质量结论。
