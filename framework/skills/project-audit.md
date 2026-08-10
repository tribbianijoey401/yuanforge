---
name: project-audit
description: Existing Project 接入、Architecture 恢复或高影响变更前使用，以 Repository Evidence 建立当前事实。
version: 4.0.0
---

# Project Audit Skill

## vNext Reference Routing

- Code Organization Risk：读取 `framework://references/01-standards/code-organization.md` 的相关 Rule 与 Anti-pattern Section。
- Generated Code Risk：读取 `framework://references/01-standards/generated-code-failure-modes.md` 的对应 Failure Mode Section。
- Production Readiness：读取 `framework://references/01-standards/production-readiness-scorecard.md` 的目标 Level 与 Dimension Section。
- Yuan Framework 自身回归：读取 `framework://references/01-standards/framework-failure-modes.md` 的匹配 Anti-pattern。

## Evidence Order

1. 可运行行为与 Test Result
2. Source、Config、Migration、Dependency 与 Entry Point
3. Git History 和已确认 Decision
4. 当前 Project Document
5. Generic Reference 或推测

文档与代码冲突时记录 Drift，不用文档覆盖 Repository Fact，也不擅自猜测原始意图。

## Procedure

1. 扫描 Repository Tree、Build/Test Command、Entry Point 和主要 Dependency。
2. 识别 Module Boundary、Data Flow、Public Interface、State、External System 和 Trust Boundary。
3. 运行最小安全 Baseline Check，记录可复现 Evidence。
4. 对照七类 Project Document，分类为 Missing、Stale、Contradictory 或 Verified。
5. 只在 Signal 命中时加载专业 Reference，对当前风险做 Focused Audit。
6. 更新稳定 Product/Architecture Fact；未确认重大选择进入 Decision Proposal，不直接写成 Confirmed。
7. 形成首个 Active Work 或把无关 Item 写入 Backlog。

## Output

- Current System Summary
- Module / Interface Map
- Verified Build and Test Baseline
- Document Drift
- High-risk Finding 与 Evidence
- 推荐的最小 Next Work
