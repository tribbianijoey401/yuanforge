# 项目安装与更新

## 目标

Yuan 的交付层保持“安装一次，随后由 `AGENTS.md` 自动触发”的 Vibe Coding 体验；Core 仍由项目固定的确定性 Runtime 提供事实校验。安装器是外部 Deployment Adapter，不参与 Reducer Truth。

## 首次安装

```powershell
python -B scripts/sync_project.py install <目标项目> --profile AUDITED
```

脚本先运行完整 Conformance Suite。Candidate Release Manifest、Conformance Report、Harness Digest、Git Revision 和 dirty 状态必须互相一致；Evidence 不匹配时，目标项目保持原样。

安装结果：

```text
<目标项目>/
  AGENTS.md                         保留项目原文，只维护 Yuan 标记区块
  .gitignore                       保留项目原文，只维护 Yuan 标记区块
  .yuan/
    bin/yuan.pyz                   项目固定 Runtime，建议提交 Git
    adapters/codex-audited.json    诚实的开放平台 Capability Descriptor
    config.json                    Profile、Protocol、Harness 与 Environment Binding
    protocol.md                    当前项目固定的 Core Protocol
    release-manifest.json          Candidate 中每个 Source Entry 与 Runtime 的 Digest
    conformance-report.json        与该 Runtime Digest 绑定的完整验证报告
    install.json                   安装内容、Release Evidence 与 Source Binding
    extensions/manifest.json       默认能力 Profile 的版本与逐文件 Digest
    extensions/vibe-coding/        托管的 Rules、Agents 与 Skills
    extensions/custom/             项目自定义能力，更新时保留
    releases/<runtime-digest>/     可校验的完整旧部署快照
  .yuan-run/                       Ledger、Blob 与 Projection，不提交 Git
```

安装器不会覆盖现有 `AGENTS.md`。没有 Yuan 标记时追加 Managed Block；已有且唯一时只替换该 Block；标记缺失、重复或顺序错误时 fail-closed。安装前会完成 Run ID、Managed Block 和 Release Evidence 校验；任一步失败都会恢复所有原文件，因此可以直接重试。

## Agent 启动

项目内所有 Yuan 命令都使用固定入口：

```text
python -B .yuan/bin/yuan.pyz --root .
```

这样全局 Python Package 的升级不会静默改变项目 Runtime。Bootstrap 先验证状态，再加载默认 `vibe-coding` Profile 的基础 Rules，并按当前任务选择 Agent 与 Skill。能力层指导 Work Authoring、Proposal、实施和验证；只有 Core Reducer 的 `COMPLETE` 可以报告完成。

首个 Run 没有 Work，因此初始 `status` 返回 `BLOCKED` 且原因为“没有 Active Work”。这不是故障：Agent 应根据当前用户请求创建 Verifier 和首个 Work。后续新请求通过 Successor Work/New Run 继续，不重写历史。

## 同步更新

```powershell
python -B scripts/sync_project.py update <目标项目>
```

更新过程：

1. 使用旧的项目固定 Runtime 验证当前 Run。
2. 从当前 Yuan Release 构建新的确定性 Candidate，并验证 Manifest、Conformance 与 Source Binding。
3. Candidate 与当前 Runtime 相同则返回 `UNCHANGED`，仅校准 Managed Bootstrap。
4. Active Work 非终态时返回 `STAGED`，Candidate 与带 Digest 的 Metadata 写入被忽略的 `.yuan/candidates/`，旧 Candidate 自动清理，不切换当前 Runtime。
5. 没有 Work 或当前结果为 `COMPLETE` 时，保存完整旧部署快照，更新 Protocol/Config/Bootstrap/能力 Profile/Release Evidence 并原子切换。
6. 使用新固定 Runtime 重新执行 `status`；失败时恢复全部 Managed File。

安装、更新、状态检查和回滚共用 `.yuan/.deployment.lock`。旧部署快照位于 `.yuan/releases/<digest>/`，包含 Runtime、Config、Protocol、Install Record、Adapter、托管能力、Release Evidence 和两个 Managed Block，供本地恢复，不提交 Git。更新不修改 `.yuan-run/current.json`、任何不可变 Event 或 `.yuan/extensions/custom/`；下一个 Successor Work 会绑定新的 Protocol、Harness 和 Environment。

## 状态与回滚

```powershell
python -B scripts/sync_project.py status <目标项目>
python -B scripts/sync_project.py rollback <目标项目> <runtime-digest>
```

Rollback 会先验证 Snapshot 内每个文件和 Managed Block，再保存当前部署快照。只有空 Run，或当前 Work 为 `COMPLETE` 且绑定目标 Snapshot 的 Profile、Protocol、Harness 与 Environment 时才允许恢复；失败时同样恢复操作前状态。

## 返回状态

- `INSTALLED`：首次安装完成。
- `UNCHANGED`：目标项目已使用同一 Release。
- `STAGED`：当前 Work 未终结，候选未激活。
- `UPDATED`：新 Release 已激活并通过固定 Runtime 自检。
- `ROLLED_BACK`：完整旧部署已恢复并通过旧固定 Runtime 自检。
- `ERROR`：安装内容、Managed Block 或 Runtime 状态不合法，未宣称成功。
