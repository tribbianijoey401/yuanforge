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

### Phase 1 concurrency boundary

Phase 1 是：

```text
Multiple Persisted Works
+ one focused interaction
+ at most one active Work
+ one Implementation Writer
```

因此：

- 可以同时保存多个 `ready` / `paused` / `blocked` Work；
- 最多一个 `active` Work；有 active Work 时 `STATUS.focus` 必须指向它；
- 查看另一个 ready/paused/blocked Work 不等于并发执行；
- 正式切换执行前必须先让当前 active Work complete / pause / block；
- Phase 1 不建设 Scheduler、Worker Pool、后台 Daemon、mutation overlap detector 或自动 branch/worktree manager。

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
- Phase 1 不允许多个 active Work；
- active Work 必须被 focus；
- STATUS projection 与 focused Work 一致。

Conductor 是 `docs/works/*.md` / `STATUS.md` 的唯一正式 State Writer。每个 Dispatch 前、Specialist Focused Result 返回后以及 Create / Focus / Activate / Pause / Resume / Block / Switch / Distill 都执行 State Commit；Guard 未输出 `STATE_VALID` 时不得继续 Dispatch。Specialist 只返回 `work_updates`。

Legacy Project 如果 STATUS 没有 `focus` 字段，Guard 继续按旧 `WORK.md + STATUS.md` contract 读取。Framework Update 不迁移 Project-owned Work State；下一次 Conductor 能可靠取得 Work identity 的正式 Commit 才迁入 `docs/works/<id>.md`。

## Update Boundary

`update` 不要求旧 Framework 自证，也不以 Version、Integrity 或旧 Runtime 健康状态阻止更新。它强制用最新官方快照替换 `.yuan/framework/` 与 Framework-owned `AGENTS.md`，同时保持以下 Project-owned 内容完整：

- `docs/`，包括全部 `docs/works/` persisted Work；
- `.yuan/overrides/`；
- Project Source、Test、Config 和其他业务文件。

Update 不迁移或解释 Project-owned 内容。它只读取 STATUS 的 focused Work projection 做最小安全判断：明确 `active` 时停止并要求先 complete / pause / block；旧格式、缺失或无法判定的状态按 compatibility 规则放行。更新后的 Check 只报告问题，不自动修复。

## Insight Multi-Work Observation

Insight 是只读 Sidecar。Snapshot 读取 `STATUS.focus` 后只把 focused Work 装入当前语义 Snapshot，同时对 `docs/works/*.md` 维护 content hash，以观察 Work create/remove/switch。Windows watcher 递归观察 Project Root；Linux inotify 同时监听 `docs/` 和动态 `docs/works/`。

Insight 明确区分：

```text
focus switch != Work completion
```

W1 → W2 时，W1 的当前 Trace 只轮转/保存，不写完成 Summary；只有 canonical `docs/works/W1.md` 在 Distill 后真正移除，才生成 W1 Summary。之后 Resume W1 时新的 Trace 可以继续追加到该 Work 的历史 Trace。

Coverage 只要求当前布局真实需要的状态源：Multi-Work 有 focus 时要求 `STATUS.md + focused Work file`；`focus:null` 只要求 STATUS；legacy 模式才要求 `WORK.md + STATUS.md`。因此旧 compatibility 文件不会成为新 Multi-Work Dashboard 的假必需依赖。

Transition index、Trace、Gap 和 Coverage 全部位于 `.yuan/insight/`，不写回 Project State。Insight 复用 Framework State Guard 的问题码，不维护第二套状态词汇，也不自动改写状态。
