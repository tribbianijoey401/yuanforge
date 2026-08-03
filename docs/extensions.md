# Capability Profile 与 Custom Extension

## Bundled Profile

发行包从 `src/yuan/profiles/<profile-id>/profile.json` 自动发现 Profile。新增 Profile 不需要修改 Kernel，只需提供：

- `profile.json`：版本、Required Rules、Agent Catalog、Skill Catalog 和 `use_when`；
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
python -B .yuan/bin/yuan.pyz --root . capability resolve --agent architect --skill writing-plans
```

`list` 返回描述和触发条件，不需要读取全部文件。`resolve` 总是返回全部 Required Rules，并为所选 Agent/Skill 返回路径与 Digest。LLM 只读取这些文件；文件被篡改时命令失败。

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

Custom Extension 只能指导 Proposal 或产生 Evidence，不能修改 Core Result、Install Record 或托管 Profile。
