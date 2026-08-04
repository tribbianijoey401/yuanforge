# Yuan Harness vNext

Yuan 是一个协议优先、面向持久化 LLM 软件工程的 Harness。它不试图让模型更聪明，而是让工作结果可验证、可恢复、可审计。

参考实现刻意保持精简：

- Markdown 定义语义。
- Python 标准库微内核提供确定性锚点。
- JSON Event 不可变并使用内容寻址。
- Run Memory 是可由 Ledger 重建的一次性投影。
- `docs/memory/` 是由 Work/Evidence 支持、可提交 Git 的追加式项目长期记忆。
- 开放 Agent 平台默认使用 `AUDITED` Profile；受控平台可以安装 `ENFORCED` Adapter。
- 默认安装 `vibe-coding` 能力 Profile，提供具体的 Rules、Agents 与 Skills；它们指导 LLM 工作，但不重定义 Core Truth。
- 新需求通过 Intake 与完整 Work 两次用户确认；Risk/Signal 机械生成 Agent→Skill Assignment，角色以可重放 Handoff 闭环。

## 推荐用法：安装并由 LLM 开始工作

从 Yuan 源码仓库执行：

```powershell
python -B scripts/sync_project.py install G:\projects\my-project --profile AUDITED --capability-profile vibe-coding
```

推荐脚本会先运行完整 Conformance，只有报告中的 Harness 与 Artifact Digest 同时匹配 Candidate 才允许安装。Git Commit 与 Worktree dirty 状态会写入目标项目的 Install Record。

也可以先安装 Yuan CLI，再执行同一能力：

```powershell
python -m pip install .
python -B scripts/run_conformance.py
yuan project install G:\projects\my-project --profile AUDITED --capability-profile vibe-coding --release-root .
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
   请读取项目根目录 AGENTS.md，并按照 Yuan Agent Bootstrap 从 Intake 开始新需求；需要时向我提问，并在需求摘要和完整 Work 两个节点等待我确认。我的需求是：<在这里描述需求>
   ```

3. 会话中断、切换平台或稍后恢复时，向 LLM 发送：

   ```text
   请读取项目根目录 AGENTS.md，检查 Yuan 当前状态，并按照 Yuan Agent Bootstrap 继续未完成的 Work；只有 Reducer 返回 COMPLETE 时才报告完成。
   ```

LLM 会先读取 Bootstrap，通过项目内固定 Runtime 恢复状态。没有 Active Work 时，它先创建 Intake：只询问会改变验收或安全边界的问题，把答案、假设、风险和 Signals 展示给用户确认；随后由 `capability route` 生成不可删减的 Agent→Skill Assignment。完整 Work、Verifier、授权和预算会再次展示给用户确认，之后才开始修改。用户不需要手工重述此前过程。安装脚本成功后也会显示以上提示；机器可解析的单个 JSON 保留在标准输出，提示写入标准错误流。

执行期间，每个路由角色都必须记录 `READY` 或 `NEEDS_WORK` Handoff。审查角色的 Handoff 绑定当前 Artifact，代码变化会让旧审查自动过期。Required Evidence 和 Required Handoff 都成立，Reducer 才会返回 `COMPLETE`。

如果用户中途改变已确认需求，LLM 不会修改旧 Work：它先解析在途副作用，追加 `WORK_SUPERSEDED`，然后从新 Intake、两次用户确认和确定性 Routing 创建绑定旧 Head 的 Successor Work。这样旧实现与新意图不会混在同一历史中。

默认能力层包含：

- `rules/`：边界、工作流、Evidence、风险审查、计划、测试与交付规则。
- `agents/`：除工程实现与审查角色外，还包含 Runtime Maintainer、Debugger 和每个 Work 必经的 Memory Curator。
- `skills/`：除既有工程流程外，还包含 Runtime Recovery、Memory Retrieval 与 Memory Distillation。

框架更新会原子更新这些托管能力。项目专属规则或 Skill 放入 `.yuan/extensions/custom/<extension-id>/`，使用 Custom Extension Descriptor 绑定后会进入同一 Catalog；安装器不会覆盖它们。完整扩展协议见 [Capability Profile 与 Custom Extension](docs/extensions.md)。

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
yuan project update G:\projects\my-project
```

`update` 强制激活当前 Yuan Source，不调用旧 Runtime，也不检查旧版本、Install Record、Active Work 或 Conformance，不产生 `UNCHANGED/STAGED`，不保存或回滚旧框架。它重建 Runtime、Config、Protocol、Bootstrap、Adapter 与 Bundled Profile；`.yuan-run/`、`docs/memory/`、`.yuan/extensions/custom/` 和 `AGENTS.md` 项目自有内容必须逐字节保留。更新后的 `status` 只作为诊断；失败返回 Warning，不恢复旧 Runtime。

旧 Runtime 无法启动时，可先运行不依赖目标 Runtime 的外部诊断：

```powershell
python -B scripts/sync_project.py diagnose G:\projects\my-project
```

脚本结果含义：

- `INSTALLED`：安装完成，可以使用上面的“开始新工作”提示。
- `UPDATED`：当前 Yuan Source 已强制激活；`memory_preserved` 必须为 `true`，Runtime 诊断可能是 `PASS` 或 `WARNING`。

## 手动 Core 流程

```powershell
python -m pip install -e .
yuan --root . init --profile AUDITED
yuan intake template --request "实现可验证需求" > intake.draft.json
# 填写问题答案、假设、风险和 Signals；展示给用户并取得明确确认：
yuan seal intake.draft.json > intake.sealed.json
yuan intake check intake.sealed.json
yuan intake confirm intake.sealed.json --statement "用户确认需求摘要" > intake.json
yuan work template --intake intake.json > work.draft.json
# 编辑草稿，在 .yuan/drafts/verifiers/ 创建只读 Verifier，然后绑定文件闭包并接受 Work：
yuan work bind-verifier work.draft.json --criterion AC-001 > work.bound.json
# 展示完整 Work、角色路由、授权和预算，并取得用户最终确认：
yuan work confirm work.bound.json --statement "用户确认完整 Work Contract" > work.json
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
# 对 Routing 中每个角色生成并记录 READY/NEEDS_WORK Handoff：
yuan handoff template --handoff-id HANDOFF-TEST-001 --agent tester --to user --phase verification --status READY --summary "验证通过" --evidence EVD-001 > handoff.json
yuan handoff record handoff.json
# Memory Curator 在最后一个 Handoff 前追加长期记忆，或明确 NO_MEMORY_CHANGE：
yuan memory template --memory-id MEM-FEATURE-001 --kind feature --title "功能" --summary "已验证事实" --details "Evidence 支持的长期说明" > memory.json
yuan memory check memory.json
yuan memory record memory.json
yuan memory status
yuan reduce
```

每条命令只输出一个 JSON Object。失败采用 fail-closed 策略并返回非零 Exit Code。运行时位于 `.yuan-run/`；删除投影不会丢失事实，`yuan rebuild` 可从不可变 Event 重建 Run Memory。

如果进程在写入不可变 Event 后、推进 Ledger Head 前崩溃，运行 `yuan recover`。它会先验证完整 Event Chain，再修复派生 Head。普通 Append 会自动回收 PID 已退出的崩溃锁；仍存活的持有者和近期损坏锁不会被误删。`--force-stale-lock` 只用于操作员确认后的异常恢复。

## 项目长期记忆

`.yuan-run/` 保存一次 Run 的不可变事实；`docs/memory/records/` 保存跨会话、可提交 Git 的语义知识。Memory 支持 `feature`、`decision`、`pitfall`、`module` 和 `convention`，同一 ID 通过不可变 Revision 演进并绑定 Work Digest、PASS Evidence、Artifact、Ledger Head 与可选文件 Digest。`yuan memory context --request <需求>` 使用离线确定性的中文二元词片、英文词项、字段权重、稀有词权重和完整短语加分检索相关知识，并返回命中词项；它不上传项目内容或依赖外部 Embedding。`memory status` 标记 Binding 已变化的 stale 记录，`memory rebuild` 可重建 `index.json` 与 `INDEX.md`。

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

M0–M8 均已完成；详细语义、限制与退出 Evidence 见 [开发路线图](docs/roadmap.md)。开放 Agent 平台的实际保证等级仍是 `AUDITED`；这不是未完成项，而是对平台旁路能力的诚实边界。
