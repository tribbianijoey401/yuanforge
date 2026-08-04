# 项目安装与更新

## 目标

Yuan 的交付层保持“安装一次，随后由 `AGENTS.md` 自动触发”的 Vibe Coding 体验；Core 仍由项目固定的确定性 Runtime 提供事实校验。安装器是外部 Deployment Adapter，不参与 Reducer Truth。

## 首次安装

```powershell
python -B scripts/sync_project.py install <目标项目> --profile AUDITED --capability-profile vibe-coding
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
  .yuan-run/                       Ledger、Blob 与 Projection，不提交 Git
  docs/memory/                     Work/Evidence 支持的追加式长期记忆，提交 Git
```

安装器不会覆盖现有 `AGENTS.md`。没有 Yuan 标记时追加 Managed Block；已有且唯一时只替换该 Block；标记缺失、重复或顺序错误时 fail-closed。安装前会完成 Run ID、Managed Block 和 Release Evidence 校验；任一步失败都会恢复所有原文件，因此可以直接重试。

## Agent 启动

项目内所有 Yuan 命令都使用固定入口：

```text
python -B .yuan/bin/yuan.pyz --root .
```

这样全局 Python Package 的升级不会静默改变项目 Runtime。Bootstrap 先验证状态与 Catalog；空 Run 从 Intake 开始，取得需求确认后由 `capability route` 返回固定 Profile 的 Rules、Agent→Skill Assignment 和审查要求。完整 Work 再次确认后才能接受。Verifier 在 Work 接受前只能创建于 `.yuan/drafts/verifiers/`，不会形成未受管辖的 Artifact 修改。执行角色必须记录 Handoff；只有 Core Reducer 的 `COMPLETE` 可以报告完成。

首个 Run 没有 Work，因此初始 `status` 返回 `BLOCKED` 且原因为“没有 Active Work”。这不是故障：Agent 应依次完成 Intake、问题回答、用户确认、风险路由、Work/Verifier 和最终用户确认。后续新请求通过 Successor Work/New Run 继续；非终态需求变更先 `WORK_SUPERSEDED`，不重写历史。

## 同步更新

```powershell
python -B scripts/sync_project.py update <目标项目>
```

更新过程：

1. 计算 `.yuan-run/` 与 `docs/memory/` 的逐文件内容指纹。
2. 直接从当前 Yuan Source 构建最新 Runtime；不运行旧 Runtime，不读取旧 Install Record，也不执行 Conformance 准入。
3. 清理旧 Bundled Profile（保留 `extensions/custom/`），重建 Runtime、Protocol、Config、Adapter、Profile、Install Record 和两个 Managed Block。
4. 再次计算项目 Memory 指纹；任何变化都作为更新错误报告。
5. 使用新 Runtime 执行 `status`。失败只写入 `diagnostics: WARNING`，已激活的新 Runtime 不回滚。

`update` 的定义就是强制替换框架层，因此没有版本比较、`UNCHANGED`、Active Work Gate、`STAGED`、Deployment Snapshot 或自动回滚。默认部署当前发行包的默认 Profile，也可用 `--capability-profile` 显式选择。即使旧 Runtime、Config、Install Record 或 Managed Block 已损坏，更新仍不依赖它们；只有最新 Runtime 无法构建、目标无法写入或项目 Memory 被改变才会失败。

更新仍使用 `.yuan/.deployment.lock` 避免两个更新进程同时写入。它不修改 `.yuan-run/current.json`、任何 Ledger Event、`docs/memory/` 或 `.yuan/extensions/custom/`。新 Runtime 必须兼容历史 Work/Event/Evidence Schema；兼容性由 Yuan 自身 CI 的历史项目 Fixture 保证，不由目标项目的旧 Runtime 批准。

## 外部诊断与状态

```powershell
python -B scripts/sync_project.py diagnose <目标项目>
python -B scripts/sync_project.py status <目标项目>
```

`diagnose` 不依赖目标 Runtime，返回托管文件存在性、Memory 指纹、写权限、Runtime 命令、Exit Code、stdout/stderr，以及建议的 `runtime-maintainer`/`runtime-recovery` 路由。`status` 则由已经激活的新 Runtime 重建当前 Run。

## 长期记忆

项目事实分为两层：`.yuan-run/` 保存不可变运行历史，`docs/memory/` 保存跨 Work 的语义知识。Memory Record 以 JSON Revision 追加，绑定来源 Work、PASS Evidence、Artifact、Ledger Head 和可选文件 Digest；`index.json` 与 `INDEX.md` 都可重建。Memory Curator 是每个 Work 的最后角色：有长期影响时记录 Memory，没有影响时在 Handoff 中明确 `NO_MEMORY_CHANGE`。

## 返回状态

- `INSTALLED`：首次安装完成。
- `UPDATED`：当前 Yuan Source 已强制激活且项目 Memory 指纹保持不变；诊断可以为 `PASS` 或 `WARNING`。
- `ERROR`：构建、写入或 Memory 保持失败；错误包含阶段、类型和 Runtime Maintainer 路由建议。
