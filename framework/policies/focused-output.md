# Focused Output Policy

角色输出用于可靠 Handoff，不用于保存完整推理。每个 Agent 只输出下游完成职责所需的信息。

## Shape

```text
Status: READY | NEEDS_WORK
Conclusion: 已确定的结论
Evidence: Test、Path、Diff、Log 或可复现结果
Artifact: 新增或修改的产出
Risk / Unknown: 剩余风险与未验证项
Verification: 已执行的方法和结果
Next Action: 下一角色或 Writer 的一个明确动作
Memory: 更新内容或 NO_MEMORY_CHANGE
```

## Boundaries

- 不输出 Chain-of-thought、全部探索、无关 Reference 全文或重复 Project Context。
- Hypothesis 必须标记为 Hypothesis，不能写成 Conclusion。
- Reviewer 使用 `NEEDS_WORK` 时提供可定位 Finding、Evidence 与 Affected Path，但不直接修改 Artifact。
- Tool Timeout 或 Outcome 不明时明确写 `Unknown`，不得假定失败或成功。
- Handoff 只进入当前 Work；只有稳定、可复用内容经 Memory Skill 提炼后才进入长期 Document。
