# Yuan Agent Bootstrap

当 `.yuan/config.json` 存在时，本项目启用 Yuan Harness。项目固定的执行入口是：

```text
python -B .yuan/bin/yuan.pyz --root .
```

## 每个项目请求的入口

1. 在处理请求前运行 `<入口> status`；命令失败、状态不可解析或 Integrity 校验失败时返回 `BLOCKED`。
2. 读取 `.yuan/protocol.md`，以 Active Work 的 Artifact Scope、Grant、Budget 和 Acceptance Criterion 为动作边界。
3. 不得直接编辑 `.yuan/config.json`、`.yuan/protocol.md`、`.yuan/bin/`、`.yuan/install.json` 或 `.yuan-run/`；框架更新只能由外部 Yuan 同步命令执行。

## Work Authoring

- 当前 Run 没有 Work 时，根据用户意图创建首个 Work。
- 当前 Run 已终结且用户提出新请求时，使用 `<入口> work template --successor` 创建新 Revision，再通过 `<入口> run successor` 创建新 Run。
- 草稿和平台回执写入 `.yuan/drafts/`，不要污染 Artifact。
- Acceptance Criterion 必须具体、可执行并绑定预先存在的 Verifier；Verifier 必须输出一个 JSON Object：`{"status":"PASS|FAIL","assertions":[...]}`。
- 先运行 `work bind-verifier` 固定 Verifier Closure，再运行 `work accept`。不得用文字声明代替 Work 或 Evidence。

## 一个有副作用的 Tick

1. 使用 `<入口> attempt template` 基于已读取文件生成带 Digest 的 Relevant Input 和 Proposal；同一 Tick 最多一个 Proposal。
2. 运行 `<入口> attempt begin <proposal>`，让 Kernel 校验 Scope、Grant、Budget 和重复策略。
3. 只有返回可继续时，紧邻真实动作之前运行 `<入口> attempt dispatch --attempt <id>`。
4. 只执行 Proposal 声明的 Action 和 Path；随后把真实平台结果写成 Receipt。
5. 运行 `<入口> attempt observe --attempt <id> --receipt <file>`，由 Kernel 检查 Artifact Diff。
6. Receipt 丢失、Timeout、Crash、未声明修改或终态不明确时运行 `attempt mark-unknown`；不得自动重试或假定成功。
7. 对 Required Criterion 运行 `<入口> verify`，最后运行 `<入口> reduce`。

只允许报告 Reducer 的唯一结果：`CONTINUE`、`CORRECT`、`COMPLETE`、`BLOCKED`、`WAIT_AUTH` 或 `BUDGET_EXIT`。只有 `COMPLETE` 可以向用户报告工作完成；`UNKNOWN` 必须通过新的只读 Reconciliation Attempt 解析。

`AGENTS.md` 只是平台 Adapter，不是 Core Truth。若本段与固定的 Protocol 或 Kernel 冲突，以机械校验结果为准并 fail-closed。
