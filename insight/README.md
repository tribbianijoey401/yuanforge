# Yuan Insight

只读、自包含、旁路运行的 Yuan Framework 自省与调优模块。观察 Yuan 正常工作时已经产生的 Framework Assets 与 Project State，重建一次 Work 的语义执行路径，将 Framework Expected Behavior 与 Observed Behavior 进行比较，帮助 Framework 开发者发现 Agent、Skill、Workflow、Memory、Context 和 Quality 机制中的缺失、重复、失效与优化机会。

**定位：** Yuan 官方能力，但工程上可选、隔离。Insight 失败/删除不影响 Yuan。

## 设计铁律

- 只读：不修改 WORK/STATUS/MEMORY，不参与 Routing，不阻塞 Agent
- 可选：Insight 停止或 Observation Data 缺失不影响 Yuan Core 任何流程
- Fact First：没有事实来源的字段必须 Unknown，禁止假精度
- Expected 来自现有 Framework Definition，不复制规则
- 不做 Event Ledger、不依赖平台 telemetry、不做 exact token、不常驻 LLM
- Trace 与 Signal 分离：Trace 只保存 What Changed，Signal 动态计算 What It Means
- Semantic Real-Time：只在语义状态变化时反映，不做 Heartbeat
- Native First：Windows 使用 `ReadDirectoryChangesW`，Linux 使用 `inotify`；不支持或失效时显式降级为 `polling-fallback`，Coverage 为 Partial
- State Ownership：Project State 只由 Conductor 写入；Insight 的 transition index 不反写 STATUS
- Shared State Contract：复用 `framework://tools/state_guard.py` 的只读结果，不复制规范值、不自动修复
- Missing-state honest：WORK/STATUS 缺失或不可读时显示 `STATE UNAVAILABLE` 与 `UNKNOWN` Coverage，不把空 Parser 结果当成 IDLE

## 用法

```bash
# 从源码直接运行（无需安装）
PYTHONPATH=insight python3 -B -m yuan_insight.cli <project-root> --once    # 一次性 Snapshot
PYTHONPATH=insight python3 -B -m yuan_insight.cli <project-root> --signals # 输出 Signals
PYTHONPATH=insight python3 -B -m yuan_insight.cli <project-root>           # watch 模式（JSONL Trace）
PYTHONPATH=insight python3 -B -m yuan_insight.cli <project-root> --web     # Dashboard（默认 :8765）

# Package 安装后
yuan observe <project-root> --web

# Yuan Installer 安装到 Project 后
python -B .yuan/insight/yuan.py observe . --web
```

## Dashboard

打开 `http://127.0.0.1:8765/`。`--web` 在同一进程启动 Observation Service，后台由原生文件事件唤醒并完成 Debounce / Trace / Gap / Summary；UI 每 0.5s 读取 `/api/state`。`--poll` 只控制 fallback polling / watcher health check 间隔，不是原生模式的采样周期：

- **Work / Execution Map**：Work 状态、Stage Timeline、当前 Agent
- **Agent Matrix**：ACTIVE / COMPLETED / MISSING / NOT REQUIRED
- **Invalid-state visibility**：非法 Stage 显示原始 `UNKNOWN STAGE`；未注册 Agent 显示 `UNREGISTERED ACTOR`；规范 Agent 与可选 Instance 同时展示
- **Skill Matrix**：REPORTED / MISSING / AVAILABLE
- **Signals**：Missing Agent/Skill、Repeated Review、Bug Recurrence、Memory；点击展开 Why（expected/observed/derived/check）
- **Context Footprint**：References / Docs / Sections / Chars / Bytes / Memory
- **Work History**：归档 Work 的 Summary（stages/agents/skills/transitions）

## Signals（v0）

| Signal | 判定条件 | 纪律 |
|---|---|---|
| Missing Agent | Expected 明确 + FULL coverage + 未观察到 | 否则 NOT_OBSERVED/UNKNOWN |
| Missing Skill | Expected 明确 + skills_applied 有事实 | 缺一不判 |
| Repeated Review | Finding 分类跨轮重复 ≥2 | 只报事实不猜根因 |
| Bug Recurrence | 需 Bug identity / Memory linkage | v0 无则 UNAVAILABLE |
| Memory Effectiveness | selected + reported used | 无 usage 证据则 UNAVAILABLE |
| State Divergence | State Guard 报告 WORK / STATUS / Workflow / Stage / Agent checkpoint 不一致 | 保留原始值，只读报告，交由 Conductor 修复 |

## 存储

```text
.yuan/insight/
├── sessions/<session>.json     # Observation Session + Baseline
├── traces/<work>.jsonl         # 归档 Work Trace（保留最近 N=50）
├── traces/current.jsonl        # 活跃 Work 的 Trace
├── summaries/<work>.json       # 长期 Work Summary，不随 Trace Retention 删除
└── gaps/<session>.jsonl        # Observation Gap
```

`.yuan/insight/tool/` 是 Installer 管理的官方 Tool；其余目录是 Observation Data。删除 Observation Data 不影响 Yuan Core，但会丢失 Insight History。

## 目录

```text
insight/
├── pyproject.toml
├── yuan_insight/
│   ├── cli.py          # 入口：--once / --signals / watch / --web
│   ├── fswatch.py      # ReadDirectoryChangesW / inotify 原生事件源
│   ├── watcher.py      # Native wakeup + hash confirmation + debounce；polling fallback
│   ├── observer.py     # CLI/Web 共用的 Observation Service 与 Coverage/Gap 生命周期
│   ├── loader.py       # collect → build_snapshot（含 Expected workflow）
│   ├── registry.py     # Agent/Skill/Workflow 注册表（直读 Framework）
│   ├── state_validation.py # 加载 vendored State Guard，不定义第二套契约
│   ├── parsers/        # status/work/framework frontmatter 解析
│   ├── diff.py         # snapshot diff → facts → Transition
│   ├── footprint.py    # Declared Context Footprint
│   ├── history.py      # Work Summary 聚合 + 归档
│   ├── trace.py        # JSONL Trace / archive / prune / gap
│   ├── server.py       # Dashboard HTTP Server（标准库）
│   └── signals/        # expected_observed / state_consistency / review / bug / memory
└── web/                # 静态 Dashboard（index.html + app.js）
```

## 测试

```bash
python3 -B -m unittest tests.test_insight tests.test_insight_signals tests.test_insight_phase4 tests.test_insight_web tests.test_insight_history
```

设计依据：`yuan-insight.plan`（Phase 2-6 已实施，Phase 7 Compare Works / richer trends 为非 MVP Later 项）。

`FULL` 表示 Observer 从当前 Work 起点持续运行且原生监听健康，不表示可以重建从未落盘的 Persona。一次 Conductor Commit 对 WORK/STATUS 的连续写入会在 debounce 窗口中合并为一个语义 Transition；彼此独立、稳定落盘的角色状态会分别记录。
