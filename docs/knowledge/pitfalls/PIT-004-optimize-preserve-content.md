---
id: PIT-004
object_type: pitfall
lifecycle: knowledge
owner: doc-engineer
status: active
confidence: verified
summary: 优化/升级 Skill 或合约时，不得为给新内容让篇幅而删除原有有效内容（示例、表格、具体确认点等）；必须叠加保留。
severity: advisory
type: process
modules:
  - grilling
  - product-analyst
cause: 在重写 grilling Skill 合并 5 维度时，为给新内容让篇幅，把原有的事实/决策对照表、推荐答案格式示例、PA/Architect 具体确认点压缩删除，导致实用性下降。
fix: 优化=叠加，不删旧。原版每条规则/示例/表格完整保留，新增内容（第一性原理、维度覆盖门禁、单文档约束）作为独立段追加；被误删的示例与确认点需补回。
related: FEATURE.md 规格书、product-analyst 合约 5 维度升级
---

# PIT-004: 优化 Skill/合约不得删除原有有效内容

优化或升级框架文件（Skill、角色合约、规格书）时，常见错误是为腾出篇幅给新内容，把原有有效内容（对照表、格式示例、具体确认点）压缩或删除。

**正确做法：** 优化是叠加，不是重写覆盖。
- 原版每条规则、示例、表格完整保留
- 新增内容作为独立段追加（如 grilling 的"第一性原理"+"维度覆盖门禁"+"单文档真相源"三块）
- 若发现原版有示例/表格被误删，必须补回，而非用一句概括替代

**本次实例：** grilling Skill 合并 5 维度时，一度丢失：事实/决策对照表、推荐答案代码块示例、PA/Architect 确认点。已通过 patch 补回，现版 70 行 = 原 46 行 + 新增 24 行，无旧内容丢失。
