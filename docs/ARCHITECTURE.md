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
  → Conductor State Commit
```

Product Analyst 在同一职责边界内使用两段式 Skill Chain：模糊、高影响或高不确定需求先完整加载 `deep-requirement-discovery`，形成真正 Outcome 与 Product Direction；随后 `grilling` 继承该结果并补齐可开发、可验证的 Spec。两段不拆成不同 Agent，也不建立第二份 Product Truth Source。

## Logical Path Resolution

- `project://<path>` 相对包含入口 `AGENTS.md` 的 Project Root 解析。
- `framework://<path>` 先查 Project `.yuan/overrides/<path>`，再查已解析的 Framework Root。
- `skill://<path>` 相对当前已加载 `SKILL.md` 所在目录解析。

定位符只是契约语法，不映射成同名目录或 URL。运行时文件操作只接收解析后的真实路径；Installer/Check 校验 Framework Locator 的目标存在，Contract Test 禁止关键运行时资产继续使用无根路径。

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
├── insight/                  可选、只读的 Insight Sidecar 源码与 Dashboard
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
│   ├── insight/
│   │   ├── tool/             官方 Insight Tool，Update 只替换此子目录
│   │   ├── yuan.py           Project-local `yuan observe` Launcher
│   │   ├── sessions/         Observation Session
│   │   ├── traces/           近期详细 Trace
│   │   ├── summaries/        长期 Work Observation Summary
│   │   ├── gaps/             Observation Gap
│   │   └── cache/            当前 Observer Cache
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

Conductor 是 `WORK.md` / `STATUS.md` 的唯一正式 State Writer。每个 Dispatch 前和 Specialist Focused Result 返回后都执行 State Commit；单 LLM Persona Switch 也必须回到 Conductor。Specialist 只返回 `work_updates` 提案。STATUS 不保存 visualization revision。

## Update Boundary

`update` 不要求旧 Framework 自证，也不以 Version、Integrity 或旧 Runtime 健康状态阻止更新。它强制用最新官方快照替换 `.yuan/framework/` 与 Framework-owned `AGENTS.md`，同时保持以下 Project-owned 内容完整：

- `docs/`
- `.yuan/overrides/`
- Project Source、Test、Config 和其他业务文件

Update 不迁移或解释 Project-owned 内容。它只在任何写入前读取可明确识别的 `STATUS.work_state: active`：仅该状态停止；`idle`、`paused`、旧格式、缺失或无法判定的状态都直接放行。这样保留旧 Project Document 后，后续升级也无需额外开关。放行后直接替换 `AGENTS.md`、`.yuan/framework/`、`.yuan/insight/tool/`、Launcher、Version 与 Install Metadata；实际保留的 Project Document、Override 和 Insight Observation Data 必须逐项输出路径与原因。Pause 本身只保存 `WORK.md` Checkpoint 并标记状态，不引入 Runtime、Archive 或第二状态系统。

安装和更新后的 `check` 只报告当前布局、Dangling Reference 和 Contract 问题，不回滚最新版本。

## Insight Degraded-State Rendering

Insight 的事实源可以部分可用：例如 `WORK.md` 已有 Active Work，而 `STATUS.md` 尚未形成结构化 Checkpoint。Dashboard 必须展示已经观察到的 Work Goal、Scope、Current Task 与 Latest Result，并把缺失的 Workflow、Stage、Agent 明确标为 `UNKNOWN`；不得把 Unknown 渲染为“无工作”或“无需 Agent”。WORK/STATUS 文件本身缺失或不可读时，Snapshot source availability 产生 `STATE_FILES_MISSING`，Coverage 为 `UNKNOWN`，Dashboard 显示 `STATE UNAVAILABLE`。Framework 同时要求激活 Work 时在同一逻辑步骤维护 `WORK.md` 与结构化 `STATUS.md`，避免长期处于降级状态。

## Insight Observation Backend

Insight Observer 优先订阅操作系统目录事件：Windows `ReadDirectoryChangesW` 递归观察 Project Root，Linux `inotify` 观察 `docs/`。事件只负责唤醒；Snapshot 前仍以 watched file content hash 确认实际变化，避免无关事件进入 Trace。原生源不可用或运行中失效时切换 `polling-fallback`，API/UI 暴露 observation mode 且 Coverage 降为 Partial。

Transition index、Trace、Gap 和 Coverage 全部位于 `.yuan/insight/`，不写回 Project State。Debounce 只合并一次 Conductor Commit 内对 WORK/STATUS 的相邻写入；它不能恢复未曾稳定落盘的中间 Persona。
