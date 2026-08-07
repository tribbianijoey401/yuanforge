---
name: project-bootstrap
description: 新 Project 初始化或 Existing Project 接入 Yuan 时使用，建立七类 Project Document 与首个 Context Baseline。
version: 4.0.0
---

# Project Bootstrap Skill

## vNext Reference Routing

- New Project 需要 Stack Recommendation 时，读取 `references/architecture/mvp-stack.md` 的匹配 Product Section。
- 需要初始 Module Boundary 时，读取 `references/01-standards/code-organization.md` 的相关 Stack 与 Layer Section。
- 涉及特定 Platform 时，只读取 `references/platforms/{platform}.md` 的相关 Section。

Existing Project 的 Repository Fact 高于 Generic Reference，不得用推荐模板覆盖已经验证的 Architecture。

## New Project

1. 运行 Installer 建立 Vendored Framework 与七类 Document。
2. 由 Product Analyst 通过 Mentor Loop 形成 Product Goal、Target User、Scope 和 Acceptance。
3. Yuan 推荐最小可交付 Stack 与 Boundary；重大 Product/Architecture 选择由用户确认。
4. 初始化 `PRODUCT.md`、`ARCHITECTURE.md`、`WORK.md` 和 `STATUS.md`，其余 Document 保留明确空状态。
5. 按 Request 进入 New Feature 或 Large Project Workflow。

## Existing Project

1. 运行 Installer；不覆盖已有 `docs/`、Override 和 Source。
2. 使用 `project-audit` Skill 从 Repository、Test、Config、Git History 与可运行行为恢复 Fact。
3. 把稳定 Product、Architecture、Decision、Backlog、Status 和 Memory 写入七类 Document。
4. 明确文档与代码冲突；以可验证 Repository Fact 为准，不臆造原始意图。
5. 建立 Active Work 后进入匹配 Workflow。

## User Experience

安装结束后只提示用户自然描述 Goal、Bug 或修改需求。不要要求用户说“进入某 Phase”、指定 Agent、调用 Skill 或理解内部 Routing。
