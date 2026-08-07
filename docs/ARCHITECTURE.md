# Yuan Architecture

## System Boundary

Yuan 是 Agent Platform 内的 Markdown Framework，不是独立 Runtime。Source Repository 中央维护官方资产；Installer 将版本化快照 Vendoring 到每个 Project；Platform 按 `AGENTS.md` 使用这些资产。

```text
User Request
  → Project AGENTS.md
  → Conductor + Core Policy
  → Dynamic Routing + Primary Workflow
  → Selected Agent
  → Agent-declared Skill
  → Skill-selected Reference Section
  → Platform Tool / File / Command
  → Verification + Focused Result
  → Project Document Update
```

## Canonical Source Structure

```text
yuanforge/
├── AGENTS.md                 Platform 入口与 Project 行为契约
├── README.md                 人类入口
├── framework/
│   ├── agents/               专业角色、边界与 Skill Assignment
│   ├── skills/               可复用工程方法与 Reference Routing
│   ├── references/           只供 Skill 按 Signal 读取的专业知识
│   ├── policies/             Core、Routing、Document、Review 与可选纪律
│   ├── workflows/            四种 Primary Workflow
│   ├── adapters/             Platform 能力映射与降级策略
│   ├── templates/project/    七类 Project Document 模板
│   └── VERSION               唯一 Framework Version
├── bin/yuanforge-init        Init、Update 与 Check
├── scripts/sync_project.py   兼容的 Source 外部 Update 入口
├── tests/                    Contract 与 Installer Regression
└── docs/                     Yuan Repository 自身的七类 Project Document
```

## Dependency Direction

唯一合法的专业知识调用方向是：

```text
Routing → Agent → Skill → References
```

- Conductor 只决定 Workflow 和 Agent，不直接读取 References。
- Agent 只加载自己 Contract 声明的 Skill，不绕过 Skill 读取 References。
- Skill 根据当前 Work 的 Retrieval Signal 选择 Reference，并只读相关 Section。
- References 是被动知识源，不能反向触发 Skill 或 Agent。

Framework 中的所有路径均以 Framework Root 为基准。Source 中是 `framework/`，安装后是 `.yuan/framework/`。

## Project Layout

```text
project/
├── AGENTS.md
├── .yuan/
│   ├── VERSION
│   ├── install.json
│   ├── framework/            官方 Vendored Snapshot，Update 可整体替换
│   └── overrides/            Project Override，Update 永不覆盖
└── docs/
    ├── PRODUCT.md
    ├── ARCHITECTURE.md
    ├── DECISIONS.md
    ├── BACKLOG.md
    ├── WORK.md
    ├── STATUS.md
    ├── MEMORY.md
    └── work/archive/         仅保存有长期价值的已完成 Work 摘要
```

Override 优先级为 `Project Override > Vendored Official Asset > Yuan Default`。Override 通过与 Framework Root 相同的相对路径覆盖单个资产；不存在 Override 时直接使用官方文件。

## State and Memory

七类 Project Document 是默认 Truth Source：

- Stable Fact 进入 `PRODUCT.md` 或 `ARCHITECTURE.md`。
- 已确认重大选择进入 `DECISIONS.md`。
- 唯一 Active Work 进入 `WORK.md`，短恢复点进入 `STATUS.md`。
- 可复用经验、Preference、Convention 和 Pitfall 进入 `MEMORY.md`。
- 未激活需求进入 `BACKLOG.md`。

`TASK_BOARD` 只在 Complex Work 内作为 `WORK.md` 的可选段落；`SESSION` 默认取消；`PROGRESS` 合并到 `WORK.md` 与 `STATUS.md`；Graph、Event 和 Proposal 不属于 vNext MVP。

## Update Boundary

`update` 不要求旧 Framework 自证，也不以 Version、Integrity 或旧 Runtime 健康状态阻止更新。它强制用最新官方快照替换 `.yuan/framework/` 与 Framework-owned `AGENTS.md`，同时保持以下 Project-owned 内容完整：

- `docs/`
- `.yuan/overrides/`
- Project Source、Test、Config 和其他业务文件

安装和更新后的 `check` 只报告当前布局、Dangling Reference 和 Contract 问题，不回滚最新版本。
