# Skill: Grilling

> **扩展分类**：skill（可执行）
> **禁用影响**：需求追问降级为单次
> **依赖**：无

---

## 概述

Grilling Skill 提供 Product Analyst 的需求追问协议。通过多轮追问澄清模糊需求，直到所有维度明确。

## 执行步骤

1. 识别模糊维度（scope/interaction/exception/data/nonfunctional）
2. 针对每个模糊点提出一个问题
3. 等待用户反馈
4. 记录到 `clarification_log`
5. 重复直到所有维度覆盖

## 与 Core 的关系

- Grilling 是 Product Analyst 的执行策略，不是 Core 完成语义
- Core 只要求 `user_stories` 和 `acceptance_criteria` 字段存在
- 禁用后：PA 直接产出文档，无追问循环

---

## 版本

| 字段 | 值 |
|------|-----|
| schema | yuan.skill.grilling/v1 |
| category | skill |
| required_in_core | false |
