# Skill: Debug Feedback Loop

> **扩展分类**：skill（可执行）
> **禁用影响**：诊断协议降级为手动执行
> **依赖**：无

---

## 概述

Debug Feedback Loop Skill 提供系统化的诊断流程：隔离→二分→假设→验证→修复。

## 执行步骤

1. **Isolate**：确认失败范围，排除无关因素
2. **Bisect**：二分定位问题边界
3. **Hypothesize**：提出可能原因
4. **Verify**：验证假设
5. **Fix**：实施修复
6. **Confirm**：确认修复有效

## 与 Core 的关系

- 调试是 Dev 的执行策略，不是 Core 完成语义
- Core 不关心调试过程，只关心 Evidence 结果
- 禁用后：Dev 手动调试，无结构化诊断协议

---

## 版本

| 字段 | 值 |
|------|-----|
| schema | yuan.skill.debug-loop/v1 |
| category | skill |
| required_in_core | false |
