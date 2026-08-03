# Yuan Harness vNext

Yuan 是一个协议优先、面向持久化 LLM 软件工程的 Harness。它不试图让模型更聪明，而是让工作结果可验证、可恢复、可审计。

参考实现刻意保持精简：

- Markdown 定义语义。
- Python 标准库微内核提供确定性锚点。
- JSON Event 不可变并使用内容寻址。
- Run Memory 是可由 Ledger 重建的一次性投影。
- 开放 Agent 平台默认使用 `AUDITED` Profile；受控平台可以安装 `ENFORCED` Adapter。
- 默认安装 `vibe-coding` 能力 Profile，提供具体的 Rules、Agents 与 Skills；它们指导 LLM 工作，但不重定义 Core Truth。

## 推荐用法：安装并由 LLM 开始工作

从 Yuan 源码仓库执行：

```powershell
python -B scripts/sync_project.py install G:\projects\my-project --profile AUDITED
```

推荐脚本会先运行完整 Conformance，只有报告中的 Harness 与 Artifact Digest 同时匹配 Candidate 才允许安装。Git Commit 与 Worktree dirty 状态会写入目标项目的 Install Record。

也可以先安装 Yuan CLI，再执行同一能力：

```powershell
python -m pip install .
python -B scripts/run_conformance.py
yuan project install G:\projects\my-project --profile AUDITED --release-root .
```

安装器会：

- 把确定性 Runtime 固定为目标项目的 `.yuan/bin/yuan.pyz`。
- 创建 `.yuan/config.json`、`.yuan/protocol.md`、Release Manifest、Conformance Evidence、Adapter Descriptor 和 Install Record。
- 安装 `.yuan/extensions/vibe-coding/` 下的规则、Agent 角色和按需 Skill，并把每个文件绑定到 Install Record。
- 在保留项目原文的前提下，安装或更新 `AGENTS.md` 中带标记的 Yuan Bootstrap。
- 在 `.gitignore` 中维护 `.yuan-run/`、Draft、Candidate 和本地 Release Backup。
- 初始化首个空 Run；之后由 Agent 根据用户意图 Author Work。

安装完成后，用户只需要在目标项目中向 Codex 等 Agent 描述需求。Agent 通过项目固定入口运行 Yuan：

```powershell
python -B .yuan/bin/yuan.pyz --root . status
```

推荐流程：

1. 使用 Codex、Claude Code 等 Agent 打开目标项目根目录。
2. 开始一个新项目或新需求时，直接向 LLM 发送：

   ```text
   请读取项目根目录 AGENTS.md，并按照 Yuan Agent Bootstrap 开始一个新的 Work。我的需求是：<在这里描述需求>
   ```

3. 会话中断、切换平台或稍后恢复时，向 LLM 发送：

   ```text
   请读取项目根目录 AGENTS.md，检查 Yuan 当前状态，并按照 Yuan Agent Bootstrap 继续未完成的 Work；只有 Reducer 返回 COMPLETE 时才报告完成。
   ```

LLM 会先读取 Bootstrap，再通过项目内固定 Runtime 恢复 Run Memory、Work、Attempt 和 Evidence。用户不需要手工重述此前过程。安装脚本成功后也会显示以上提示；机器可解析的单个 JSON 保留在标准输出，提示写入标准错误流。

默认能力层包含：

- `rules/`：边界、工作流、Evidence、风险审查、计划、测试与交付规则。
- `agents/`：Conductor、Product Analyst、Architect、前后端开发、设计、规格、安全、质量、UX、Tester 和 Documentation Engineer。
- `skills/`：仓库审计、Work 编写、计划、TDD、系统化调试、代码审查、多 Agent 开发和发布交接。

框架更新会原子更新这些托管能力。项目专属规则或 Skill 放入 `.yuan/extensions/custom/`，安装器不会覆盖它们。

详细安装边界与目录结构见 [项目安装与更新](docs/installation.md)。

## 推荐用法：同步 Yuan 更新

先更新 Yuan 源码仓库，再同步目标项目：

```powershell
git pull
python -B scripts/sync_project.py update G:\projects\my-project
```

或使用已升级的全局 CLI：

```powershell
python -m pip install --upgrade .
python -B scripts/run_conformance.py
yuan project update G:\projects\my-project --release-root .
```

更新不会删除 `.yuan-run/`，不会覆盖 `AGENTS.md` 的项目自有内容或 `.yuan/extensions/custom/`。安装、更新和回滚共用项目级 Deployment Lock。没有 Active Work 或当前结果为 `COMPLETE` 时，新 Runtime 原子激活并保存包含 Runtime、Config、Protocol、Bootstrap、Adapter、能力 Profile 和 Release Evidence 的完整旧部署快照；其他非终态会返回 `STAGED`，需要在当前 Work 完成后再次运行更新命令。

检查当前部署和暂存 Candidate：

```powershell
python -B scripts/sync_project.py status G:\projects\my-project
```

更新成功后如需恢复旧部署，使用 `status` 或更新返回值中的 SHA-256：

```powershell
python -B scripts/sync_project.py rollback G:\projects\my-project <runtime-digest>
```

Rollback 只在没有 Work，或当前 Work 已 `COMPLETE` 且仍绑定目标快照的 Profile/Protocol/Harness/Environment 时执行。它不修改任何 `.yuan-run` Event。

脚本结果含义：

- `INSTALLED`：安装完成，可以使用上面的“开始新工作”提示。
- `UNCHANGED`：目标项目已经是当前版本，可直接开始或继续 Work。
- `UPDATED`：新 Runtime 已激活，可让 LLM 继续读取当前状态。
- `STAGED`：当前 Work 未完成；先使用“继续未完成工作”提示，达到 `COMPLETE` 后再次执行 `update`。
- `ROLLED_BACK`：目标完整部署快照已经恢复并通过其固定 Runtime 自检。

## 手动 Core 流程

```powershell
python -m pip install -e .
yuan --root . init --profile AUDITED
yuan work template > work.draft.json
# 编辑草稿，然后绑定 Verifier 文件闭包并接受 Work：
yuan work bind-verifier work.draft.json --criterion AC-001 > work.json
yuan work accept work.json
# 根据当前文件自动绑定 Relevant Input Digest：
yuan attempt template --attempt-id ATT-001 --strategy "实现需求" --claim "修改满足 AC" --falsification "Verifier 失败" --input src/app.py --action-type file-write --path src --side-effect-class filesystem --grant-id GRANT-001 > proposal.json
yuan attempt begin proposal.json
# 紧邻真实动作之前执行：
yuan attempt dispatch --attempt ATT-001
# Agent 仅执行已声明动作，然后记录观察：
# 把平台回执写入 receipt.json：
yuan attempt observe --attempt ATT-001 --receipt receipt.json
yuan verify --criterion AC-001 --attempt ATT-001
yuan reduce
```

每条命令只输出一个 JSON Object。失败采用 fail-closed 策略并返回非零 Exit Code。运行时位于 `.yuan-run/`；删除投影不会丢失事实，`yuan rebuild` 可从不可变 Event 重建 Run Memory。

如果进程在写入不可变 Event 后、推进 Ledger Head 前崩溃，运行 `yuan recover`。它会先验证完整 Event Chain，再修复派生 Head。除非操作员显式传入 `--force-stale-lock`，否则不会破坏近期 Append Lock。

## 信任边界

`AGENTS.md` 只是 Adapter 引导，不是 Trust Root。正确性来自内核对不可变 Work、Attempt、Evidence、Artifact Hash 和确定性 Reducer 的验证。

在 `AUDITED` 下，Yuan 能检测未声明的工作区修改，但无法物理阻止平台绕过它。在 `ENFORCED` 下，平台 Adapter 必须把所有副作用路由到 Yuan Port。

框架升级是外部 Release，不是运行中内核的自我批准：每个 Run 固定 Protocol 与 Kernel Digest，维护者或 CI 在该 Run 外构建和验证下一候选版本。

`AUDITED` 能让意外绕过或遵循指令的违规操作 fail-closed，但不能防御一个已拥有 `.yuan-run` 任意写权限的恶意进程。该威胁模型需要 OS/平台隔离与 `ENFORCED` Adapter，因此参考实现不会仅凭配置宣称 `ENFORCED`。

## Conformance 与发行

```powershell
python -B scripts/run_conformance.py
python -B scripts/build_zipapp.py
python -B dist/yuan.pyz --root . release verify dist/release-manifest.json --artifact dist/yuan.pyz --check-source
```

Conformance Suite 会验证全部 Unit Test、Schema、Codex `AUDITED` Adapter、Protocol/Kernel 规模预算、Zipapp 自包含运行和两次构建逐字节一致性，并生成 `dist/conformance-report.json`。

`main` 的 Push/Pull Request 会由 GitHub Actions 自动运行 Conformance 和 Wheel 构建。推送与 `pyproject.toml` 版本一致的 `v*` Tag 时，Release Workflow 会发布 `yuan.pyz`、Manifest、Conformance Report、SHA-256 文件和 GitHub Artifact Provenance。

M0–M6 均已完成；详细语义、限制与退出 Evidence 见 [开发路线图](docs/roadmap.md)。开放 Agent 平台的实际保证等级仍是 `AUDITED`；这不是未完成项，而是对平台旁路能力的诚实边界。
