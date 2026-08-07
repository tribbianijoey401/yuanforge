# Yuan

Yuan 是运行在 Codex、Hermes 等现有 Agent Platform 上的、Markdown 驱动的 AI 软件工程 Mentor、长期 Project Memory 与多角色协作 Framework。它让用户像平常一样描述需求，同时在内部提供更可靠的需求澄清、Context 恢复、专业分工、Verification 和经验沉淀。

Yuan 的首要目标是提高 Vibe Coding 的代码质量，不是建设独立 Runtime 或工具控制平面。

## 工作方式

```text
自然语言 Request
  → Yuan Mentor 澄清关键 Product 问题并给出推荐
  → Dynamic Routing 选择一个 Primary Workflow
  → 只加载需要的 Agent
  → Agent 调用需要的 Skill
  → Skill 按 Signal 读取相关 Reference Section
  → 一个 Writer 实施，Test / Reviewer 按 Risk 验证
  → 更新 Status 与长期 Memory
```

核心依赖关系只有一条：`Routing → Agent → Skill → References`。这保证了角色负责“谁来做”，Skill 负责“怎么做”，References 负责“需要哪些专业知识”，避免全部资产同时进入 Context。

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

## 安装

```powershell
python -B bin/yuanforge-init C:\path\to\project --mode existing --force
```

新 Project：

```powershell
python -B bin/yuanforge-init C:\path\to\new-project --force
```

安装完成后，直接在 Agent Platform 中描述你的 Product Goal、Bug 或修改需求。Yuan 会自动恢复 Project Context、选择 Workflow、Agent、Skill 和必要 References；不需要在 Prompt 中指定 Phase、Agent 或 Skill。

## 强制更新

```powershell
python -B scripts/sync_project.py update C:\path\to\project
```

`update` 总是用当前 Source 的最新官方资产替换 Project 中的 `.yuan/framework/`，不会因旧 Version、Integrity 或旧 Runtime 损坏而拒绝。以下内容保持不变：

- `docs/` Project Memory
- `.yuan/overrides/` Project Override
- Project Source、Test、Config 与其他业务内容

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
│   ├── skills/               18 个工程 Skill
│   ├── references/           32 个专业 Reference（原知识资产全部保留并补入迁移经验）
│   ├── policies/             Core、Routing、Review 与可选纪律
│   ├── workflows/            四种 Primary Workflow
│   ├── adapters/             Platform Mapping 与降级
│   └── templates/project/    七类 Project Document 模板
├── bin/yuanforge-init        Init / Update / Check 实现
├── scripts/sync_project.py   兼容更新入口
├── tests/                    Contract 与 Installer Regression
└── docs/                     Yuan 自身的 Project Memory
```

详细产品边界见 [`docs/PRODUCT.md`](docs/PRODUCT.md)，Architecture 与调用规则见 [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md)，当前迁移进度见 [`docs/WORK.md`](docs/WORK.md)。
