# Focused Output Policy

角色输出用于可靠 Handoff，不用于保存完整推理。每个 Agent 只输出下游完成职责所需的信息。

## Focused Result Contract

Agent 完成时返回 Focused Result，最小字段：

```yaml
outcome: completed | partial | blocked | failed
summary: <short result summary>
skills_applied:
  - <skill id>        # Agent 声明本任务实际采用的方法
verification:
  - <evidence / verification result>
risks:
  - <open risk>
next: <recommended next action>
```

语义约束：

- `outcome` 是 Agent 对自身工作的报告，**不等于 Task Done**。Conductor 根据 Done Conditions 判断任务是否真正满足完成标准。
- `skills_applied` 语义是 "Agent **reported applied** this Skill"，不是 "verified executed"。它用于：Conductor 知道采用的方法、Reviewer 基于上游方法审查、Correction Routing 避免机械重复、失败 Workflow 知道已尝试过什么。
- `skills_applied` 只在当前 Work 有意义（暂存于 WORK Latest Result），不进入长期 Memory。

## Handoff Dispatch Contract

Conductor Dispatch 一个 Agent 的最小充分信息：

```yaml
task: <this agent's concrete task>
goal: <expected outcome>
done_conditions:
  - <condition 1>
  - <condition 2>
constraints:
  - <constraint>
context_refs:
  - <declared relevant context ref>
```

默认不要求 Agent 完整读取 WORK 或整个项目；Conductor 选择与任务相关的 Context。Agent 之后若发现需要额外信息，可自行读取，不要求向 Conductor 申请，也不做 file-read telemetry。

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
