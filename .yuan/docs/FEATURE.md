# FEATURE — 需求规格书

> 管辖每个会话文件夹中的 `FEATURE.md`。Product Analyst 产出，Architect 读取。

<SECTION-END:feat-purpose>
## 目的

FEATURE.md 是需求的**单一真相源**（铁律Ⅵ）。承载 Product Analyst 的 5 维度澄清产出，供 Architect 作为设计输入。

- 消除「认知差」：把人类需求中的隐含假设显式化
- 单文档真相源：不另产独立澄清文档，5 维度吸收进用户故事 + 验收标准
- Architect 顺 TASK_BOARD 原因指针读取本文件

<SECTION-END:feat-pos>
## 在会话文件夹中的位置

```
docs/YYYYMMDD-描述/
├── PLAN.md      ← Architect 产出（冻结）
├── FEATURE.md   ← Product Analyst 产出（本规格书）
├── TASK_BOARD.md
├── SESSION_LOG.md / ADR-NNN.md / BUG-NNN.md
```

<SECTION-END:feat-fmt>
## 完整格式

```markdown
# 需求规格 — [功能名]

## 概述
- 来源需求：[用户原始 vibe / PRD 链接]
- 澄清时间：[日期]
- 风险标签：P0 / P1 / P2

## 1. 用户故事（维度1 范围边界）
- 作为 [角色]，我想要 [功能]，以便 [目的]
- 本期范围：[列表]
- 本期不做：[列表]（原因 / 二期）
- 依赖：[功能A 依赖 功能B]

## 2. 验收标准
### 2.1 交互流程（维度2）
- Given / When / Then ……
### 2.2 异常边界（维度3）
| 场景 | 处理方式 | 提示文案 |
|------|----------|----------|
### 2.3 数据规则（维度4）
| 字段名 | 类型 | 必填 | 默认值 | 校验规则 | 错误提示 |
|--------|------|------|--------|----------|----------|
### 2.4 非功能需求（维度5）
- 性能 / 兼容性 / 安全（脱敏 · 审计 · 限流）

## 3. 澄清记录（溯源）
| 维度 | 问题 | 用户回答 | 备注 |
|------|------|----------|------|
> 维度剪裁须记理由；用户答「待确认」项须标注。
```

<SECTION-END:feat-end>
## 与 PLAN.md 的关系

```
FEATURE.md（需求，Product Analyst 产出）
  │  Architect 读取 → 计划复盘（设计理解书 → 用户确认）
  ▼
PLAN.md（设计，Architect 产出，冻结）
```

FEATURE.md 是 PLAN.md 的上游输入。Architect 不得修改 FEATURE.md 的需求事实，只能在 PLAN 中演化设计决策。

<SECTION-END:feat-end>
