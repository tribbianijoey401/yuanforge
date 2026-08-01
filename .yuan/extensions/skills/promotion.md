# Skill: Promotion (Skill Registry)

> **扩展分类**：skill（可执行）
> **禁用影响**：Skill 晋升管线降级为手动
> **依赖**：workflows/promotion.md

---

## 概述

Promotion Skill 定义 Skill 从草稿（draft）到正式发布（published）再到降级（deprecated）的完整流程。

## 状态转换

```
draft → review → published → deprecated
         ↓          ↓
       rejected  re-review
```

## 执行步骤

1. 创建 draft Skill（`_drafts/` 目录）
2. 提交 review（由 Spec Reviewer 审查）
3. 通过审查后发布到 `skills/` 目录
4. 发现缺陷时标记为 deprecated

## 与 Core 的关系

- Skill 晋升是知识管理流程，不是 Core 完成语义
- Core 不关心 Skill 的状态，只关心执行结果
- 禁用后：Skill 直接维护，无晋升管线

---

## 版本

| 字段 | 值 |
|------|-----|
| schema | yuan.skill.promotion/v1 |
| category | skill |
| workflow_dependency | workflows/promotion.md |
| required_in_core | false |
