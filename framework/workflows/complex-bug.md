# Workflow：Complex Bug

```text
读取 Status、Work 与相关 Memory
→ 用普通语言确认 Observed / Expected Behavior
→ 加载 Systematic Debugging Skill
→ 建立 Failing Test 或可重复 Reproduction
→ 区分 Observation、Hypothesis 与 Verified Fact
→ 一个 Implementation Agent 完成 Root-cause Fix
→ Focused Test 与 Regression
→ Risk-driven Review
→ User Acceptance
→ Memory Distillation
```

两种实质不同的 Hypothesis 均失败后停止继续 Patch，由 Architect 或未参与当前 Patch 的相关 Dev 在 Independent Context 中重新分析 Failure Model。Platform 不支持时使用 Persona Switch 并说明限制。
