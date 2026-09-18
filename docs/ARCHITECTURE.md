# Yuan Architecture

## System Boundary

Yuan 是 Agent Platform 内的 Markdown Framework，不是独立 Runtime。Source Repository 中央维护官方资产；Installer 将版本化快照 Vendoring 到每个 Project；Platform 按 `AGENTS.md` 使用这些资产。

```text
User Request
  → Project AGENTS.md
  → Conductor + Core Policy
  → select / restore focused Work
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
│   ├── policies/             Core、Routing、Document、State、Review
│   ├── workflows/            四种 Primary Workflow
│   ├── adapters/             Platform 能力映射与降级策略
│   ├── templates/project/    Project Document 与 Work body 模板
│   └── VERSION               唯一 Framework Version
├── bin/yuanforge-init        Init、Update 与 Check
├── scripts/sync_project.py   兼容的 Source 外部 Update 入口
├── insight/                  可选、只读的 Insight Sidecar 源码与 Dashboard
├── tests/                    Contract 与 Installer Regression
├── benchmarks/               Evaluation Asset，不属于 Framework runtime
└── docs/                     Yuan Repository 自身的 Project Memory
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
│   │   ├── yuan.py           Project-local Launcher
│   │   ├── sessions/         Observation Session
│   │   ├── traces/           当前/历史 Work Trace
│   │   ├── summaries/        已完成 Work Observation Summary
│   │   ├── gaps/             Observation Gap
│   │   └── cache/            当前 Observer Cache
│   └── overrides/            Project Override，Update 永不覆盖
└── docs/
    ├── PRODUCT.md
    ├── ARCHITECTURE.md
    ├── DECISIONS.md
    ├── BACKLOG.md
    ├── STATUS.md             focus + focused Work recovery projection
    ├── MEMORY.md
    ├── WORK.md               legacy v4 single-work compatibility only
    └── works/
        ├── W-101.md          persisted Work canonical state
        ├── W-102.md
        └── archive/          仅保存有长期价值的已完成 Work 摘要
```

Override 优先级为 `Project Override > Vendored Official Asset > Yuan Default`。Override 通过与 Framework Root 相同的相对路径覆盖单个资产；不存在 Override 时直接使用官方文件。

## Multi-Work State and Memory

长期 Project Truth 与 Work execution state 分离：

- Stable Fact 进入 `PRODUCT.md` 或 `ARCHITECTURE.md`。
- 已确认重大选择进入 `DECISIONS.md`。
- 未激活、尚未形成清晰 Work Contract 的请求进入 `BACKLOG.md`。
- 每个 `docs/works/<work-id>.md` 独立保存一个 Work 的 Goal、Scope、Acceptance、Workflow、Stage、Agent、Current Task、Latest Result、Open Findings、Work Learnings、Next Action / Blocker。
- `STATUS.md` 只保存 `focus` 与 focused Work 的短 Recovery Projection。
- 可复用经验、Preference、Convention 和 Pitfall 进入 `MEMORY.md`。
- `docs/WORK.md` 只服务 legacy v4 compatibility，不再是新 Multi-Work 的 canonical state。

`docs/works/` 目录本身就是 Work Registry，不新增 Work Registry Object 或数据库。

### Work lifecycle

Persisted Work state：

```text
ready | active | paused | blocked
```

Completion 不是 active-store 的长期状态。一个 Work 满足 Acceptance、Verification、Risk-driven Review、Known Issue disclosure 与 `Open Findings = 0` 后先 Distill；有长期历史价值时写精炼摘要，再移除对应 `docs/works/<id>.md`。其它 Work 原样保留。

### Phase 2 concurrency boundary

Phase 2 是：

```text
Multiple Persisted Works
+ one focused interaction
+ one or more active Works only with real execution isolation
+ one Implementation Writer per workspace
```

因此：

- 单 active Work 保持 Phase 1 compatibility，`execution` 可以省略；
- 多个 `active` Work 只在每条 lane 都声明 `execution.mode: isolated`、唯一 Platform workspace 与唯一真实 `agent.instance` 时合法；纯 `subagent` / `background-process` channel label 与 `persona-degraded` 不能作为并发证明；
- 有 active Work 时 `STATUS.focus` 必须指向其中一个 active Work。多个合法 isolated active Work 之间可以切换 focus，切换本身不构成 Pause、Completion 或 Archive；
- focused Work 完成并移除后，如果仍有 active Work，STATUS 必须 handoff 并完整投影一个 remaining active Work；用户已明确目标时优先该 Work，否则使用 Work id 的稳定字典序首个。只有不存在 active Work 时才允许 `focus: null / work_state: idle`；
- Yuan 只验证 Agent Platform 已提供的 execution identity 与 workspace isolation，不创建 Scheduler、Worker Pool、后台 Daemon、自动 branch/worktree、merge queue 或 mutation-overlap runtime；
- isolated execution 可以并发，但向共享目标的 Integration 仍由 Conductor 串行收敛。

Work 是 execution isolation boundary；Task 是 Work 内部可判定步骤；Attempt 是 Task 的一次执行尝试。这些是功能关系，不要求把它们都升级成新的持久化对象。

## STATUS Recovery Projection

新格式 STATUS 至少表达：

```yaml
focus: W-102
work: W-102
work_state: active
workflow: complex-bug
stage: implement
agent:
  id: backend-dev
  state: active
```

其中 `work/work_state/workflow/stage/agent/quality` 都是 focused Work 的派生投影。Canonical State 在 `docs/works/W-102.md`；Conductor 每次 State Commit 在同一逻辑步骤更新 Work + STATUS，Guard 检查 projection drift。

没有 focus 时 STATUS 为 `focus: null / work_state: idle`。这里 idle 只表示 Project Recovery Index 当前没有 focus，不是 persisted Work state。

## State Commit Guard

`framework://policies/state-contract.md` 是状态词汇的唯一语义契约，`framework://tools/state_guard.py` 是只读执行门。

Guard 动态从 Workflow frontmatter 与 Agent Contract 取得 Canonical Workflow / Stage / Agent，并验证：

- Work 文件名 stem 与 frontmatter `id` 一致；
- persisted Work state 合法；
- active / paused / blocked 对 Current Task / Next Action / Blocker 的要求；
- 单 active Work 保持 legacy/Phase 1 compatibility；
- 多 active Work 必须全部满足 `execution.mode: isolated`、唯一 workspace、唯一真实 `agent.instance`，并拒绝 channel-only identity 与 `persona-degraded` 伪并发；
- 存在 active Work 时 focus 必须落在某个 active Work；STATUS projection 与 focused Work 一致。

Conductor 是 `docs/works/*.md` / `STATUS.md` 的唯一正式 State Writer。每个 Dispatch 前、Specialist Focused Result 返回后以及 Create / Focus / Activate / Pause / Resume / Block / Switch / Distill 都执行 State Commit；Guard 未输出 `STATE_VALID` 时不得继续 Dispatch。Specialist 只返回 `work_updates`。

Legacy Project 如果 STATUS 没有 `focus` 字段，Guard 继续按旧 `WORK.md + STATUS.md` contract 读取。Framework Update 不迁移 Project-owned Work State；下一次 Conductor 能可靠取得 Work identity 的正式 Commit 才迁入 `docs/works/<id>.md`。

## Update Boundary

`update` 不要求旧 Framework 自证，也不以 Version、Integrity 或旧 Runtime 健康状态阻止更新。它强制用最新官方快照替换 `.yuan/framework/` 与 Framework-owned `AGENTS.md`，同时保持以下 Project-owned 内容完整：

- `docs/`，包括全部 `docs/works/` persisted Work；
- `.yuan/overrides/`；
- Project Source、Test、Config 和其他业务文件。

Update 不迁移或解释 Project-owned 内容。对 canonical Multi-Work Project，它在写入前扫描全部 `docs/works/*.md`：任一 Work 为 `active` 都阻止 Update；canonical Work 无法读取、frontmatter/state 无法判定或 state 不属于 `ready | active | paused | blocked` 时同样 fail closed，并返回明确的 Update blocker。只有没有 canonical Work registry 的 legacy Project 才继续使用旧 compatibility 判断。更新后的 Check 只报告问题，不自动修复。

## Insight Multi-Work Observation

Insight 是只读 Sidecar。Phase 2 保留 `Snapshot.work` 作为 focused Work compatibility view，同时维护 `Snapshot.works`，为每个 persisted Work 建立语义视图；文件变化按 Work 归属生成 semantic diff，而不是只靠 focused Work 或全局 file hash 推断。

Multi-Work trace 使用：

```text
.yuan/insight/traces/<work-id>.jsonl
```

因此 non-focused active Work 的变化写入自己的 trace，不污染 focused Work。Legacy single-work Project 继续兼容 `traces/current.jsonl`。

Insight 明确区分：

```text
focus switch != Work completion
canonical Work removal = Work completion
```

focus 在多个 isolated active Work 间切换时不生成 Completion Summary。任意 canonical Work 在 Distill 后真正移除时，不论它是否 focused，都使用该 Work 的最后已知状态完成自己的 trace/summary lifecycle。

CLI/Dashboard 的当前 Evidence 仍以 focused Work 为消费边界：Multi-Work 下只读取 `traces/<focus>.jsonl`。如果 durable observer cache 的 `current_work_id` 与当前 `STATUS.focus` 不一致，说明 focus change 不在已证明的 observation coverage 内；此时不把旧 Work trace 归因给新 focus，而返回空 transitions 并把 Coverage 降为 PARTIAL。

Coverage 只要求当前布局真实需要的状态源：Multi-Work 有 focus 时要求 `STATUS.md + focused Work file`；`focus:null` 只要求 STATUS；legacy 模式才要求 `WORK.md + STATUS.md`。Transition、Trace、Summary、Gap 与 Coverage 全部位于 `.yuan/insight/`，不写回 Project State。Insight 复用 Framework State Guard 的问题码，不维护第二套状态词汇，也不自动改写状态。
