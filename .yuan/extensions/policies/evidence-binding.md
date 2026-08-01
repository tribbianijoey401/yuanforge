# Policy: Evidence Binding

> **扩展分类**：policy（可选）
> **禁用影响**：专业结论不再强制绑定 Evidence，Agent 自述可被接受
> **依赖**：INVARIANTS（铁律 Ⅵ 文档即代码 + 原则 证据优先）

---

## 概述

Evidence Binding 要求所有专业结论（Spec Reviewer、Security Auditor、Quality Auditor、Tester）必须引用具体的 Evidence 文件，禁止纯自述。

## 规范

| 声明 | 必须引用 | 示例 |
|------|---------|------|
| "AC 已满足" | 具体 Evidence ID | `E-AC-001` |
| "无安全漏洞" | 检查列表 | `SEC-001 pass` |
| "测试通过" | 测试日志 | `E-TEST-005 pass` |
| "性能达标" | 性能指标 | `E-PERF-003` |

## 与 Core 的关系

- Evidence Binding 是 INVARIANTS 的证据原则的执行细化
- Core Schema Validation 不检查 Evidence 引用完整性
- Core Reducer 只检查 Evidence 文件是否存在且 result=pass
- 禁用后：Agent 自述可被接受，不影响 Core 完成判定

## 禁用时的降级行为

- 专业结论可以不含 Evidence 引用
- Core 仍可验证 Evidence 文件，但不再强制要求
- 证据链完整性检查降级为 Advisory

---

## 版本

| 字段 | 值 |
|------|-----|
| schema | yuan.policy.evidence-binding/v1 |
| category | policy |
| depends_on | INVARIANTS.IVI |
| required_in_core | false |
