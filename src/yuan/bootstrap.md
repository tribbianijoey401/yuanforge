# Yuan Agent Bootstrap

当 `.yuan/config.json` 存在时，本项目启用 Yuan Harness。项目固定的执行入口是：

```text
python -B .yuan/bin/yuan.pyz --root .
```

## 每个项目请求的入口

1. 在处理请求前运行 `<入口> status`；命令失败、状态不可解析或 Integrity 校验失败时返回 `BLOCKED`。唯一例外是命令成功且唯一原因为“没有 Active Work”：这表示安装后的空 Run，应进入首个 Work Authoring。
2. 读取 `.yuan/protocol.md`，以 Active Work 的 Artifact Scope、Grant、Budget 和 Acceptance Criterion 为动作边界。
3. 运行 `<入口> capability list` 获取带触发条件的 Catalog；命令失败或托管能力 Digest 不匹配时返回 `BLOCKED`。
4. 根据 Catalog 选择最小 Agent 与 Skill 集合，再运行 `<入口> capability resolve --agent <id> --skill <id>`；读取返回的全部 Rule 和所选能力文件。
5. 不得直接编辑 `.yuan/config.json`、`.yuan/protocol.md`、`.yuan/bin/`、`.yuan/install.json`、`.yuan/extensions/manifest.json`、托管 Profile 或 `.yuan-run/`；框架更新只能由外部 Yuan 同步命令执行。
6. `.yuan/drafts/` 是 Work 接受前唯一允许写入的 Yuan 草稿区；它不属于 Artifact 或 Core Truth。项目自己的扩展写入 `.yuan/extensions/custom/`。

## Rules、Agents 与 Skills

- `rules/` 是每个 Tick 的工程纪律，`capability resolve` 返回的基础规则必须读取。
- `agents/` 是职责与审查隔离模板；平台支持多 Agent 时可以派发，不支持时按角色顺序执行并保留独立 Evidence。
- `skills/*/SKILL.md` 是按需加载的可复用流程。只有描述与当前任务匹配时才加载，避免把全部能力塞入上下文。
- 这些能力只负责提出 Proposal、指导动作或产生 Evidence；发生冲突时，Protocol、Kernel 和 Reducer 的机械结果优先。

## Work Authoring

- 当前 Run 没有 Work 时，根据用户意图创建首个 Work。
- 当前 Run 已终结且用户提出新请求时，使用 `<入口> work template --successor` 创建新 Revision，再通过 `<入口> run successor` 创建新 Run。
- 草稿和平台回执写入 `.yuan/drafts/`，不要污染 Artifact。
- Acceptance Criterion 必须具体、可执行并绑定预先存在的 Verifier；Verifier 必须输出一个 JSON Object：`{"status":"PASS|FAIL","assertions":[...]}`。
- 首个 Work 接受前，把 Verifier 写入 `.yuan/drafts/verifiers/`，从 `sys.argv[1]` 读取项目根目录，只读验证 Artifact；不得直接创建未受 Work 管辖的产品代码或测试代码。
- 先运行 `work bind-verifier` 固定 Verifier Closure，再运行 `work accept`。不得用文字声明代替 Work 或 Evidence。

首个 Work 的固定顺序是：加载 `project-lifecycle`、`work-authoring`、`verifier-authoring` → `work template` 生成草稿 → 编辑 Goal/Scope/Grant/Budget/Criterion → 在草稿区创建独立 Verifier → `work bind-verifier` → `work accept`。每一步先检查 JSON 返回值，失败时不得继续下一步。

## 一个有副作用的 Tick

1. 使用 `<入口> attempt template` 基于已读取文件生成带 Digest 的 Relevant Input 和 Proposal；同一 Tick 最多一个 Proposal。
2. 运行 `<入口> attempt begin <proposal>`，让 Kernel 校验 Scope、Grant、Budget 和重复策略。
3. 只有返回可继续时，紧邻真实动作之前运行 `<入口> attempt dispatch --attempt <id>`。
4. 只执行 Proposal 声明的 Action 和 Path；随后把真实平台结果写成 Receipt。
5. 运行 `<入口> attempt observe --attempt <id> --receipt <file>`，由 Kernel 检查 Artifact Diff。
6. Receipt 丢失、Timeout、Crash、未声明修改或终态不明确时运行 `attempt mark-unknown`；不得自动重试或假定成功。
7. 对 Required Criterion 运行 `<入口> verify`，最后运行 `<入口> reduce`。

## Result 路由与恢复

- `CONTINUE`：基于新 Evidence 提出一个新策略；不得重复相同 Input Fingerprint 与策略。
- `CORRECT`：承认可信 FAIL Evidence，改变 Hypothesis 或实现后再创建 Attempt。
- `COMPLETE`：向用户报告完成，并附上 Criterion/Evidence 摘要。
- `WAIT_AUTH`：说明具体 Effect 与 Scope，请求人类授权；授权必须进入 Successor Work Revision。
- `BUDGET_EXIT`：停止动作并报告已用 Budget、未完成 Criterion 和建议的新 Work Budget。
- `BLOCKED`：除“没有 Active Work”的首个 Work Authoring 例外外，停止普通动作并报告机械原因；若原因是 `UNKNOWN`，只能启动只读 Reconciliation。

解析 `UNKNOWN` 时，先用 `attempt template --action-type reconcile --read-only` 创建只读 Proposal，再运行 `attempt reconcile --attempt <unknown-id> <proposal>`。探测后通过 `attempt resolve` 追加 `COMMITTED` 或 `NO_EFFECT` Terminal Resolution；不得重写原 Attempt 或自动重试原副作用。

只允许报告 Reducer 的唯一结果：`CONTINUE`、`CORRECT`、`COMPLETE`、`BLOCKED`、`WAIT_AUTH` 或 `BUDGET_EXIT`。只有 `COMPLETE` 可以向用户报告工作完成。

`AGENTS.md` 只是平台 Adapter，不是 Core Truth。若本段与固定的 Protocol 或 Kernel 冲突，以机械校验结果为准并 fail-closed。
