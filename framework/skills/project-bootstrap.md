---
name: project-bootstrap
description: 新 Project 初始化或 Existing Project 接入 Yuan 时使用，建立 Project Memory、Multi-Work Store 与首个 Context Baseline。
version: 4.0.0
---

# Project Bootstrap Skill

## vNext Reference Routing

- New Project 需要 Stack Recommendation 时，读取 `framework://references/architecture/mvp-stack.md` 的匹配 Product Section。
- 需要初始 Module Boundary 时，读取 `framework://references/01-standards/code-organization.md` 的相关 Stack 与 Layer Section。
- 涉及特定 Platform 时，只读取 `framework://references/platforms/{platform}.md` 的相关 Section。

Existing Project 的 Repository Fact 高于 Generic Reference。

## Project Boundary

- Project 边界 = 一个仓库 / 一个部署单元。多模块仓库在仓库根安装并视为单一 Project。
- 子目录确需独立边界（独立 .git、独立发布）时按独立 Project 安装。
- Work 不是 Project：一个 Project 内可存在多个 `project://docs/works/<work-id>.md`。

## New Project

1. 运行 Installer 建立 Vendored Framework 与基础 Project Document。`project://docs/WORK.md` 仍作为 legacy compatibility 模板文件存在，但新 Work 不使用它作为 canonical State。
2. 第一个正式 Work 激活时创建 `project://docs/works/` 和 `project://docs/works/<work-id>.md`；目录不存在不是错误。
3. Product Analyst 通过 Mentor Loop 形成 Product Goal、Target User、Scope、Acceptance。
4. Yuan 推荐最小可交付 Stack 与 Boundary；重大 Product/Architecture 选择由用户确认。
5. 初始化 PRODUCT、ARCHITECTURE、首个 Work 和 STATUS focus/projection。
6. 按 Request 进入匹配 Workflow。

## Existing Project

1. 运行 Installer；不覆盖已有 `project://docs/`、Override 和 Source。
2. 使用 project-audit 从 Repository、Test、Config、Git History 与可运行行为恢复 Fact。
3. 稳定 Product、Architecture、Decision、Backlog 与 Memory 写入长期文档。
4. 若已有 `project://docs/works/*.md`，保持每个 Work 独立；若只有 legacy WORK + old STATUS，不在 Installer/Update 中猜测迁移。
5. 下一次有可靠 Work id 的 Conductor State Commit 才执行 legacy migration，然后进入匹配 Workflow。

## Multi-Work Bootstrap Rule

不要预创建空 Work 文件。只有真正形成独立 Goal / Scope / Acceptance 时才创建 Work。Future Idea 保持 BACKLOG，避免把 Project Memory 变成任务管理系统。

Phase 1 不初始化并行 Scheduler、worker pool、worktree/branch manager 或 mutation overlap runtime。

## User Experience

安装结束后只提示用户自然描述 Goal、Bug 或修改需求。用户可以自然说“新开一个 Work”“切到支付 Bug”“继续 W-102”，不需要理解内部 Agent、Skill、Phase 或 Gate。
