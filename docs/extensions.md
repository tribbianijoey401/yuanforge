# Capability Profile 与 Custom Extension

## Bundled Profile

发行包从 `src/yuan/profiles/<profile-id>/profile.json` 自动发现 Profile。新增 Profile 不需要修改 Kernel，只需提供：

- `profile.json`：版本、Required Rules、Agent/Skill Catalog、`use_when` 与确定性 Workflow；
- `rules/*.md`；
- `agents/*.md`；
- `skills/<skill-id>/SKILL.md`。

安装时使用：

```powershell
python -B scripts/sync_project.py install <项目> --capability-profile vibe-coding
```

项目更新默认继续使用 Install Record 固定的 Profile；如果新发行包不再提供该 Profile，更新 fail-closed，不会静默切换。在空 Run 或 `COMPLETE` 安全边界可显式切换：

```powershell
python -B scripts/sync_project.py update <项目> --capability-profile <新-profile-id>
```

## 运行时发现与调用

```powershell
python -B .yuan/bin/yuan.pyz --root . capability list
python -B .yuan/bin/yuan.pyz --root . capability route --risk R1 --signal backend
python -B .yuan/bin/yuan.pyz --root . capability resolve --agent architect --skill writing-plans
```

`list` 返回 Catalog 与 Workflow。`route` 从已确认 Risk/Signal 生成唯一 Routing、Agent→Skill `assignments` 和所有需要读取的路径/Digest；它是 Work 接受时 Kernel 重算的路由来源。`resolve` 仅用于显式加载自定义能力或诊断。文件被篡改时命令失败。

Bundled Workflow 必须覆盖 R0/R1/R2、至少一个 Signal、全部 Agent 的 Skill Assignment，并声明会随 Artifact 变化而失效的 Reviewer。新增 Agent 却没有 Assignment 会使 Profile fail-closed。

## Project Custom Extension

每个自定义扩展位于 `.yuan/extensions/custom/<extension-id>/`，包含 `extension.json` 以及声明的 `rules/`、`agents/`、`skills/` 文件。自定义 id 在 Catalog 中自动加命名空间，例如 `team:deploy-review`。

先编写不含 `digest` 或带占位 Digest 的草稿，再执行：

```powershell
python -B .yuan/bin/yuan.pyz --root . capability bind-custom .yuan/extensions/custom/team --write
```

该命令先完整读取和校验草稿，再原子更新 `extension.json`。`capability list` 会验证 Descriptor 和逐文件 Digest；无效自定义扩展会被隔离到 `custom_errors`，不会破坏 Core 或托管 Profile。调用示例：

```powershell
python -B .yuan/bin/yuan.pyz --root . capability resolve --skill team:deploy-review
```

Custom Extension 只能指导 Proposal 或产生 Evidence，不能修改 Core Result、Install Record、托管 Profile 或其确定性 Risk Route。需要把 Custom Agent/Skill 纳入强制 Routing 时，应发布新的 Bundled Profile 版本，而不是依赖隐式 Prompt。
