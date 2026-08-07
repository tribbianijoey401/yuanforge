# Active Work

## Goal

在 `main@b8fc389` 的成熟 Yuan 内容基础上完成 vNext 内容保留式迁移，使 Repository、Installer 和 Project 使用方式符合《Yuan vNext 需求共识与产品蓝图》，并落实 `Routing → Agent → Skill → References`。

## Scope

- 将 Agent、Skill、Reference、Policy 和 Adapter 收敛到 `framework/`，保留其专业正文与 Git History。
- 建立 Dynamic Routing、四类 Primary Workflow、Risk-driven Review 和 Focused Output。
- 将 Project Memory 收敛为七类 Document，并迁移有效 Decision、Pitfall、Anti-pattern 和 Progress。
- 将 Installer 改为最新官方快照强制 Update，保护 Project Document、Override 和业务内容。
- 增加 Contract、Dangling Reference、Content Preservation 和 Installer Regression Test。

## Non-goals

- 不实现 Runtime、Ledger、Reducer、Gateway、Authority Chain 或 Daemon。
- 不重新创作已有 Agent、Skill 和 Reference 的专业知识。
- 不在本 Work 中完成真实大型 Project 的 Complex Bug MVP。

## Acceptance

- [x] Source Repository 顶层只保留清晰的人类入口、Framework、Installer/Test 和七类 Project Document。
- [x] 13 个现有 Agent Contract、18 个 Skill 与原有 Reference 的有效专业内容被保留，并补入迁移经验。
- [x] 每个 Agent 都声明 Activation、Skill Assignment、Reference Boundary 和 Focused Output。
- [x] 每个 Skill 都声明 Reference Routing；Agent 不存在直接读取 Reference 的指令。
- [x] Dynamic Routing 能区分 Small Change、Complex Bug、New Feature 和 Large Project。
- [x] `update` 无旧版本/旧 Runtime Gate，且保留 `docs/`、`.yuan/overrides/` 和 Project 自有内容。
- [x] Installer 提示用户自然描述需求，由 Yuan 自动 Routing，不要求用户点名 Agent 或 Skill。
- [x] Contract Test、Installer Test、Dangling Reference Check 和 `git diff --check` 通过。

## Migration Matrix

| main Asset | vNext Disposition | Content Strategy |
|---|---|---|
| `contracts/` | `framework/agents/` | 完整保留正文，新增 vNext Header |
| `.yuan/skills/` | `framework/skills/` | 完整保留方法，新增 Reference Routing |
| `references/` | `framework/references/` | 完整保留，由 Skill 按 Section 加载 |
| `.yuan/rules/` | `framework/policies/` | Core 精简；其余按 Signal 激活 |
| `.yuan/platforms/` | `framework/adapters/` | 保留并改为 Platform Mapping |
| 固定 Phase / Gate | `framework/workflows/` + Risk Policy | 专业方法保留，固定全流程退出 Core |
| `TASK_BOARD` | `WORK.md` 可选 Section | 只在 Complex Work 使用 |
| `PROGRESS` / `SESSION` | `WORK.md` + `STATUS.md` | 合并恢复职责 |
| Knowledge / Pitfall | `MEMORY.md` | 去重并保留可复用经验 |
| Graph / Event / Proposal | 退出 vNext MVP | 不迁移 Runtime State；Git History 可追溯 |
| v3 Specs / Runtime | 退出 vNext MVP | 在 Decision 中记录 Supersede 原因 |

## Progress

- [x] 恢复 `main@b8fc389` 作为内容基线，撤回空骨架方案。
- [x] 保留式迁移 Agent、Skill、Reference、Policy 与 Adapter。
- [x] 建立 Dynamic Routing、Primary Workflow 和 Reference Routing。
- [x] 建立七类 Project Document，并吸收现有长期知识。
- [x] 完成 Source Root、Installer、Override 和 Validation。

## Verification

- `python -B bin/yuanforge-init . --check`：PASS，0 warning。
- `python -B -m unittest discover -s tests -v`：7/7 PASS。
- `git diff --check`：PASS。
