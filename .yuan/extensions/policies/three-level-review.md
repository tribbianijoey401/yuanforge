# Policy: Three-Level Review

> **扩展分类**：policy（可选）
> **禁用影响**：审查档位降低为单一级别，不再有 🔴Blocker / 🟡Hard Gate / 🟢Advisory 区分
> **依赖**：INVARIANTS（铁律 Ⅲ 三档审查原则）

---

## 概述

Three-Level Review 定义四种审查官的阻塞级别，确保不同质量问题的严重程度得到差异化处理。

## 审查档位

| 档位 | 符号 | 含义 | 影响 | 必须执行 |
|------|------|------|------|---------|
| 🔴 Blocker | 阻塞 | 设计/安全/逻辑缺陷，不解决不合入 | 阻止 COMPLETE | 是 |
| 🟡 Hard Gate | 硬闸门 | 测试失败、全量覆盖不通过 | 阻止 COMPLETE | 是 |
| 🟢 Advisory | 建议 | 性能/可读性/风格建议 | 不阻止，可豁免 | 否 |

## 角色档位分配

| 角色 | 档位 | 原因 |
|------|------|------|
| Spec Reviewer | 🔴 Blocker | 验收标准+API契约缺陷 |
| Security Auditor | 🔴 Blocker | 安全漏洞 |
| Quality Auditor | 🟢 Advisory↗ | 同类≥3 自动升级为 🔴 |
| UX Reviewer | 🟢 Advisory↗ | 无障碍/交互问题 |

## 与 Core 的关系

- Three-Level Review 是 INVARIANTS 铁律 Ⅲ 的执行细化
- Core Reducer 只检查 Evidence result（pass/fail），不检查审查档位
- 禁用后：所有审查结果同等对待，不影响 Core 完成判定

## 禁用时的降级行为

- 所有审查统一为 Advisory 级别
- 审查发现仅记录，不阻断流程
- 仍可手动标记 Blocker，但非强制

---

## 版本

| 字段 | 值 |
|------|-----|
| schema | yuan.policy.three-level-review/v1 |
| category | policy |
| depends_on | INVARIANTS.III |
| required_in_core | false |
