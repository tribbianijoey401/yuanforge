---
name: distill-workspace
description: Work 完成、中断或 Handoff 前，把临时 Context 精炼为七类 Project Document。
version: 4.0.0
---

# Workspace Distillation Skill

## vNext Reference Routing

- 判断经验是否进入长期 Memory：读取 `references/01-standards/self-improving-memory.md` 的 Delta 与 Persistent Regression Section。
- Distillation 可能造成 Context Loss：读取 `references/01-standards/context-engineering.md` 的 Compaction Fidelity Section。

## Procedure

1. 收集 Work Acceptance、Changed Artifact、Test/Manual Evidence、Review Finding、Failed Attempt 和用户确认。
2. 区分 Stable Fact、Confirmed Decision、Current Status、Reusable Pitfall、Backlog 与一次性 Detail。
3. 把每条信息写入唯一对应 Document，不跨文件复制。
4. 对 Memory 去重：相同 Cause 更新现有条目；不同 Cause 才新增条目。
5. 为 Bug 只保留 Signal、Minimal Reproduction、Verified Cause、Fix Rule 和 Regression Evidence。
6. Work 未完成时，更新 `STATUS.md` 的 Current State 与 Next Action。
7. Work 完成且摘要有长期价值时写入 `docs/work/archive/`；否则无需创建 Archive。
8. 确认 Acceptance、Verification、Review 和 `Open Findings = 0` 后，清空 `WORK.md` Active Workspace，并将 `WORK.md` / `STATUS.md` 同时设为 no active work。Distill 是 Completion 的一部分，不在报告完成后延迟执行。

## Exclusions

- 不保存 Chain-of-thought、完整 Session、每次 Tool Call、全部 Agent Output。
- 不把未验证 Hypothesis 写成 Verified Finding。
- 不用 Archive 替代当前 Product、Architecture 或 Decision Truth。

## Output

- Updated Document List
- Added / Merged / Superseded Memory
- Remaining Backlog
- Recovery Checkpoint
- `NO_MEMORY_CHANGE`，如果确实没有长期变化
