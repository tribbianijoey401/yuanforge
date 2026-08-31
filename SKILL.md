---
name: yuanforge
title: YuanForge Vibecoding 元框架入口
description: 用 YuanForge 元框架进行 vibecoding 软件开发。当用户要开发功能、加需求、修 Bug、调试、重构、写测试、做 UI/界面设计、审查代码、规划项目，或说"vibecoding""用 yuan""元框架"，以及启动需要跨会话记忆的大型项目迭代时使用。轻任务按需加载方法论直接执行；大任务建立 docs/ 状态文档支持多会话持续推进。
version: 4.0.0-alpha.12
---

# YuanForge — Vibecoding 元框架（伞形入口）

> 本文件只做路由。所有方法细节在 `skill://framework/` 子目录，按下表按需加载，禁止预载全库。

## 定位符说明

`skill://` = 本 SKILL.md 所在仓库根。下文所有路径以它为基准；本仓库内 `framework://` 与 `skill://framework/` 同义。

## 第一步：模式判定

**轻模式（默认）**：单会话能完成、范围清晰的 Feature / Bug / UI / Refactor → 只加载路由表命中行，直接执行。

**重模式**：需要跨会话记忆与持续迭代 → 先做「第三步」再开工。

升级信号（满足任一走重模式）：

- 预计超过一个工作日，或跨 ≥3 个模块
- 用户表达"大项目 / 长期做 / 持续迭代 / 后面还要扩展"
- 本次需要恢复上次未完成的进度

拿不准时先按轻模式开工，出现升级信号再补建状态——升档随时可以，降级零成本。

## 第二步（轻模式）：按需加载路由表

| 需求信号 | 加载 | 备注 |
|---|---|---|
| 新功能 / 新行为 | `skill://framework/skills/vibecoding-workflow.md` + `skill://framework/skills/test-driven-development.md` | Verification First |
| Bug / 回归 / 间歇失败 | `skill://framework/skills/systematic-debugging.md` + `skill://framework/skills/debug-feedback-loop/SKILL.md` | 四阶段根因，先复现后修 |
| 任何写代码任务 | `skill://framework/skills/test-driven-development.md`（必载） | 其内部 Reference Routing 会按 Signal 拉 `references/01-standards/` 的失效模式与代码组织规范 |
| UI / 视觉 / 交互 / 行业 UX | `skill://framework/skills/query-ux-pro-max/SKILL.md` | 行业惯例查表，不凭记忆猜 |
| 需求模糊 / 高影响 | `skill://framework/skills/grilling/SKILL.md`；深度发现用 `skill://framework/skills/deep-requirement-discovery/SKILL.md` | 先澄清后动手 |
| 出 Plan / 任务拆解 | `skill://framework/skills/writing-plans.md` | 计划先行 |
| 交付前审查 | `skill://framework/skills/requesting-code-review.md` | |
| 测试策略 / 边界覆盖 | `skill://framework/agents/tester.md` 的行为规则段 | Tester 方法视角 |

执行纪律（三条，其余细节都在被加载的文件里）：

1. 每次最多加载 2~3 个文件；未命中信号的不读。
2. 被加载 Skill 内的 Reference Routing 继续 Signal 检索 `skill://framework/references/` 对应 Section，不整读。
3. 报告完成前，对照所载 Skill / 合约中的门禁条款逐条自查。

## 第三步（仅重模式）：建立持久状态

1. 项目根无七类文档时，按 `skill://framework/templates/project/` 创建：PRODUCT / ARCHITECTURE / DECISIONS / BACKLOG / WORK / STATUS / MEMORY（已有则不覆盖，非破坏合并）。
2. 读 `skill://AGENTS.md`（完整 Adapter 协议）+ `skill://framework/policies/core.md` 与 `skill://framework/policies/routing.md`，选定 Workflow（small-change / complex-bug / new-feature / large-project）。
3. 之后每次角色推进遵循 Conductor 状态提交纪律（WORK 与 STATUS 同步维护）；`skill://framework/tools/` 下的 State Guard 等工具可选启用。

## 平台适配

- 无 skill 自动发现机制的 Agent：让它读取本文件并照做即可。
- 项目需要脱离本机交付 vendor 快照时（罕见）：运行 `bin/yuanforge-init <project>` 安装到项目，日常不需要。
