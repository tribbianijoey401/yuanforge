# Yuan

Yuan 是运行在 Codex、Hermes 等现有 Agent Platform 上的、Markdown 驱动的 AI 软件工程 Mentor、长期 Project Memory 与多角色协作 Framework。它让用户像平常一样描述需求，同时在内部提供更可靠的需求澄清、Context 恢复、专业分工、Verification 和经验沉淀。

Yuan 的首要目标是提高 Vibe Coding 的代码质量，不是建设独立 Runtime 或工具控制平面。

## 工作方式

```text
自然语言 Request
  → Dynamic Routing 选择一个 Primary Workflow
  → 只加载需要的 Agent
  → Agent 根据自己的 Contract 与当前 Signal 调用需要的 Skill
  → Skill 按 Signal 读取相关 Reference Section
  → 一个 Writer 实施，Test / Reviewer 按 Risk 验证
  → 更新 Status 与长期 Memory
```

核心依赖关系只有一条：`Routing → Agent → Skill → References`。这保证了角色负责“谁来做”，Skill 负责“怎么做”，References 负责“需要哪些专业知识”，避免全部资产同时进入 Context。

运行时路径不依赖当前目录猜测：`project://docs/STATUS.md` 指向 Project 文件，`framework://policies/core.md` 指向带 Override 优先级的 Framework 文件，`skill://references/...` 指向当前 Skill 自带资产。这些是逻辑定位符，不是真实目录名或 URL；Agent 在调用文件工具前解析它们。

## 四种 Primary Workflow

| Workflow | 使用场景 | 默认最小角色集 |
|---|---|---|
| Small Change | 局部、清晰、低 Risk 修改 | Conductor + 一个相关 Dev |
| Complex Bug | Bug、Regression、Timeout、Lock、多次修复失败 | Conductor + Dev + Tester |
| New Feature | 新增或改变用户可观察 Behavior | Conductor + Product Analyst + Dev + Tester |
| Large Project | 模糊目标、跨 Feature、广泛 Architecture 影响 | Conductor + Product Analyst + Architect + Dev + Tester |

UI Designer 和 Reviewer 都按任务 Signal 与 Risk 加载，不固定启动完整专家团。

## Project Memory

安装后的 Project 默认使用七类人类可读文档：

| Document | 职责 |
|---|---|
| `PRODUCT.md` | 稳定 Product Fact、Target User、Business Rule 与 Boundary |
| `ARCHITECTURE.md` | 当前 System Structure、Module、Interface 与 Constraint |
| `DECISIONS.md` | 已确认重大 Product / Architecture Decision |
| `BACKLOG.md` | 未激活 Request 与 Deferred Item |
| `WORK.md` | 唯一 Active Work、Scope、Acceptance、Plan 与 Progress |
| `STATUS.md` | 短小的跨 Session Recovery Checkpoint |
| `MEMORY.md` | 可复用 Pitfall、Verified Finding、Preference 与 Convention |

`TASK_BOARD` 只在复杂 Work 中按需嵌入 `WORK.md`；`SESSION` 默认取消；`PROGRESS` 合并到 `WORK.md` 与 `STATUS.md`。

用户说“我要先离开”“工作挂起吧”或“暂停”时，任何 Workflow 都会先把可恢复 Checkpoint 写回 `WORK.md`，保留当前 Workflow / Stage，再将 `STATUS.work_state` 设为 `paused` 并停止派发。Pause 不归档、不清空 Work；下次用户说继续时从 Next Action 恢复。

每次正式 State Commit 还必须通过 Framework 自带的只读 State Guard。Stage 从当前 Workflow frontmatter 取精确值；Agent ID 从 Agent Contract 文件名取精确值，并且必须被当前 Workflow 声明。具体动作以 WORK 的 Current Task 为唯一真相源；Persona/Subagent/Session 标签写入可选 `agent.instance`。Guard 未输出 `STATE_VALID` 时，Conductor 修正同一次 Commit，不能继续 Dispatch。

## Yuan Insight

Yuan Insight 是 Yuan 官方的只读 Sidecar，通过操作系统文件事件观察 `WORK.md`、`STATUS.md` 与 Framework Definition，生成 Coverage、Trace、Work Summary、Expected vs Observed Signal 和 Dashboard。Windows 使用 `ReadDirectoryChangesW`，Linux 使用 `inotify`；原生监听不可用时明确显示 `polling-fallback` 与 Partial coverage。它不修改 Yuan Core State，失败时不影响 Agent Routing 与 Project Memory。

Yuan Core 不为 Dashboard 维护 revision：Conductor 是 `WORK.md` / `STATUS.md` 的唯一正式 State Writer；Insight 在自己的 Observation Data 中维护 transition index、gap 与 coverage。

Insight 复用 Framework State Guard 的问题码，不维护第二套状态词汇，也不自动改写状态。遇到非法 Stage 或 Agent 时，Dashboard 同时显示原始 `UNKNOWN STAGE` / `UNREGISTERED ACTOR` 和修复指引，不会把未知执行者隐藏掉。

如果 `WORK.md` 或 `STATUS.md` 缺失/不可读，Dashboard 显示 `STATE UNAVAILABLE`、Coverage 为 `UNKNOWN`，并提示通过 update/bootstrap 只补缺失文档；不会把缺失状态误报为 IDLE。

Installer 将官方 Tool 安装到 `.yuan/insight/tool/`，同目录中的 `sessions/`、`traces/`、`summaries/`、`gaps/` 和 `cache/` 是 Project 的 Insight Observation Data。`update` 只替换 `tool/` 与 Launcher，不删除已有 Observation Data。

安装后启动 Dashboard：

```powershell
python -B .yuan/insight/yuan.py observe . --web
```

从 Source Package 安装后也可使用：

```powershell
python -m pip install ./insight
yuan observe . --web
```

## 安装

```powershell
python -B bin/yuanforge-init C:\path\to\project --mode existing --force
```

新 Project：

```powershell
python -B bin/yuanforge-init C:\path\to\new-project --force
```

安装完成后，直接在 Agent Platform 中描述你的 Product Goal、Bug 或修改需求。Yuan 会自动恢复 Project Context；Routing 选择 Workflow 和 Agent，Agent 根据自己的 Contract 选择 Skill，Skill 再选择必要 References。用户不需要在 Prompt 中指定 Phase、Agent 或 Skill。

## 强制更新

```powershell
python -B scripts/sync_project.py update C:\path\to\project
```

`update` 总是用当前 Source 的最新官方资产替换 Project 中的 `.yuan/framework/`，不会因旧 Version、Integrity 或旧 Runtime 损坏而拒绝。以下内容保持不变：

- `docs/` Project Memory
- `.yuan/overrides/` Project Override
- Project Source、Test、Config 与其他业务内容

Update 不迁移或解释这些 Project-owned 文件，只读取 `STATUS.work_state` 做最小安全检查：已识别的 `active` Work 必须先完成并 Distill，或显式 Pause；旧格式、缺失或无法判定的状态直接更新，不需要迁移或额外参数。

每次 Update 都逐项输出被替换的 Yuan-managed 路径；实际存在但未替换的 Project Document、Override 与 Insight Observation Data 会以 `PRESERVED <path> | <reason>` 输出。`.gitignore` 只合并 Yuan 必需规则，并明确标记为 `MERGED`。

需要检查安装结果时运行：

```powershell
python -B scripts/sync_project.py check C:\path\to\project
```

## Source Repository

```text
yuanforge/
├── AGENTS.md                 Agent Platform 入口
├── framework/
│   ├── agents/               13 个成熟 Agent Contract
│   ├── skills/               17 个工程 Skill
│   ├── references/           32 个专业 Reference（原知识资产全部保留并补入迁移经验）
│   ├── policies/             Core、Routing、Review 与可选纪律
│   ├── workflows/            四种 Primary Workflow
│   ├── adapters/             Platform Mapping 与降级
│   └── templates/project/    七类 Project Document 模板
├── bin/yuanforge-init        Init / Update / Check 实现
├── scripts/sync_project.py   兼容更新入口
├── insight/                  可选的 Yuan Insight Sidecar 与 Dashboard
├── tests/                    Contract 与 Installer Regression
└── docs/                     Yuan 自身的 Project Memory
```

详细产品边界见 [`docs/PRODUCT.md`](docs/PRODUCT.md)，Architecture 与调用规则见 [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md)，当前迁移进度见 [`docs/WORK.md`](docs/WORK.md)。
