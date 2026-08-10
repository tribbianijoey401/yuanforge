---
name: systematic-debugging
description: Bug、Regression、Test Failure、Timeout、Lock 或多次修复无效时使用的四阶段根因调试方法。
version: 4.0.0
---

# Systematic Debugging Skill

## vNext Reference Routing

- 怀疑 Generated Code Silent Failure、Hallucinated API 或 Context Loss：读取 `framework://references/01-standards/generated-code-failure-modes.md` 的对应 Section。
- 需要设计 Regression Surface：读取 `framework://references/01-standards/test-discipline.md` 的 Impact Graph 与 Regression Section。
- 修复经验应转为长期 Regression：读取 `framework://references/01-standards/self-improving-memory.md` 的 Persistent Regression Section。
- Context 过大导致定位困难：读取 `framework://references/01-standards/context-engineering.md` 的 JIT、Compaction 与 Scratchpad Section。

## Phase 1：Reproduce

1. 分开记录 Observed Behavior、Expected Behavior、Environment 和 Frequency。
2. 收集错误、Log 和最近 Change，建立最小可重复步骤。
3. 优先建立 Failing Test；无法自动化时写明可重复 Manual Reproduction。
4. 将 Reproduction 与当前 Evidence 作为 `work_updates` 返回 Conductor，由 Conductor 提交到 `project://docs/WORK.md`；不要先 Patch。

## Phase 2：Locate

1. 从失败边界反向追踪 Data Flow、Call Path、State、Process、Lock 和 External Dependency。
2. 读取相关 `ARCHITECTURE.md`、`DECISIONS.md` 与 `MEMORY.md` Section，确认原始 Constraint 和已知 Pitfall。
3. 通过最小 Probe 或对照实验缩小可疑范围；Observation 与 Hypothesis 分开记录。
4. 只在 Signal 命中时加载相应 Reference Section。

## Phase 3：Root Cause

1. 解释为什么当前设计或实现必然产生该现象，而不只描述出错位置。
2. 用失败 Test、最小实验、Code Path 或 Process Evidence 证伪替代 Hypothesis。
3. 两种实质不同 Hypothesis 均失败时停止继续 Patch，交给 Architect 或未参与修改的 Dev 重建 Failure Model。
4. 涉及 Timeout 时检查完整 Process Tree 的终止、回收、Lock Ownership 与 Unknown Outcome；不得只停止父级等待。

## Phase 4：Fix and Regression

1. 选择直接消除 Root Cause 的最小修改，不用掩盖 Symptom 的 Retry、Recover 或 Rebuild 代替修复。
2. 保持失败 Test，完成一个 Writer 的 Fix。
3. 运行 Focused Test、受影响 Regression 和必要的真实环境验证。
4. 将 Verification 作为 `work_updates` 返回 Conductor；可复用的 Signal、Cause、Rule 和 Regression Evidence 可建议写入 `project://docs/MEMORY.md`，由有权限的角色处理。

## Output

- Reproduction
- Verified Observation 与被否定 Hypothesis
- Root Cause + Evidence
- Fix Scope
- Regression Result
- Residual Risk 与 Memory Change
