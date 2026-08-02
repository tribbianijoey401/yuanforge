# Yuan Harness vNext

Yuan 是一个协议优先、面向持久化 LLM 软件工程的 Harness。它不试图让模型更聪明，而是让工作结果可验证、可恢复、可审计。

参考实现刻意保持精简：

- Markdown 定义语义。
- Python 标准库微内核提供确定性锚点。
- JSON Event 不可变并使用内容寻址。
- Run Memory 是可由 Ledger 重建的一次性投影。
- 开放 Agent 平台默认使用 `AUDITED` Profile；受控平台可以安装 `ENFORCED` Adapter。

## 快速开始

```powershell
python -m pip install -e .
yuan --root . init --profile AUDITED
yuan work template > work.draft.json
# 编辑草稿，然后绑定 Verifier 文件闭包并接受 Work：
yuan work bind-verifier work.draft.json --criterion AC-001 > work.json
yuan work accept work.json
# 按 schemas/attempt.schema.json 创建 proposal.json：
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

M0–M5 均已完成；详细语义、限制与退出 Evidence 见 [开发路线图](docs/roadmap.md)。开放 Agent 平台的实际保证等级仍是 `AUDITED`；这不是未完成项，而是对平台旁路能力的诚实边界。
