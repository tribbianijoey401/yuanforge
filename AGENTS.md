# Yuan 源码仓库

<!-- yuan:bootstrap:start -->
# Yuan Agent Bootstrap

当 `.yuan/config.json` 存在时，本项目启用 Yuan Harness。固定入口为：

```text
python -B .yuan/bin/yuan.pyz --root .
```

## 1. 每次对话先恢复事实

1. 运行 `<入口> status` 和 `<入口> capability list`。命令失败、Integrity 校验失败、JSON 不可解析或能力 Digest 不匹配时返回 `BLOCKED`。
2. 读取 `.yuan/protocol.md`。Protocol、Kernel、Active Work 和 Reducer 的机械结果高于 Rule、Agent、Skill 与聊天摘要。
3. 不得直接编辑 `.yuan/config.json`、`.yuan/protocol.md`、`.yuan/bin/`、`.yuan/install.json`、托管 Profile 或 `.yuan-run/`。`.yuan/drafts/` 仅保存 Work 接受前草稿；项目扩展写入 `.yuan/extensions/custom/`。
4. `BLOCKED` 且唯一原因是“没有 Active Work”表示正常空 Run，应进入需求 Intake；其他 `BLOCKED` 必须按机械原因恢复。

固定 Runtime 无法启动或安装记录损坏时，不能要求旧 Runtime 自证。改由 Yuan Source 外部入口 `python -B scripts/sync_project.py update <项目根目录>` 强制重建托管框架；该动作必须保持 `.yuan-run/`、`docs/memory/`、`.yuan/extensions/custom/` 与项目自有内容不变。更新后再恢复事实，诊断警告不触发旧 Runtime 回滚。

## 2. 新需求：必须两次确认

新项目、已完成 Work 后的新请求，以及被 Supersede 后的需求都执行同一流程：

1. 加载 `conductor` 及其 `project-lifecycle`、`requirements-clarification` Assignment。
2. 运行 `<入口> memory status` 与 `<入口> memory context --request <用户原始请求>`；只把 Binding 未过期的 Memory 作为当前事实，相关 Memory ID/Digest 写入 Intake 依据。
3. 运行 `<入口> intake template --request <用户原始请求>`，把返回 JSON 保存为 `.yuan/drafts/intake.json`。
4. 由 Product Analyst 语义检查目标、用户、范围、非目标、失败影响、兼容性、数据/权限和不可逆选择。会改变验收或安全边界的问题标记为 Blocking，并原样询问用户；不得替用户回答。
5. 把答案、可撤销假设、R0/R1/R2 风险理由和 Routing Signals 写回 Intake；运行 `<入口> seal <file>` 保存重新计算 Digest 的返回值，再运行 `<入口> intake check <sealed-file>`。`NEEDS_INPUT` 时继续提问，`NEEDS_CONFIRMATION` 时向用户展示摘要。
6. 用户明确确认需求、答案、假设与风险后，运行 `<入口> intake confirm <file> --statement <真实确认摘要>`，保存返回的已确认 Intake。开放平台中的 Confirmation 是可审计对话回执，不冒充密码学签名。
7. 运行 `<入口> capability route --risk <level> [--signal <signal>]`。使用返回的完整 `routing`、`assignments`、Rules、Agents 与 Skills；不得手工降级风险、删除角色或凭 `use_when` 另造路由。
8. 运行 `<入口> work template --intake <confirmed-intake>`（继任时加 `--successor`）。加载 `work-authoring` 与 `verifier-authoring`，编辑 Goal、Artifact Scope、Grant、Budget、至少一个 Required Criterion 和 Safety Invariant。
9. Verifier 只能先写入 `.yuan/drafts/verifiers/`，从 `sys.argv[1]` 读取项目根目录，只读验证 Artifact，并输出一个 JSON Object：`{"status":"PASS|FAIL","assertions":[...]}`。用 `work bind-verifier` 固定 Closure。
10. 向用户展示完整 Work：Goal、范围/非目标、Criterion、Grant、Budget、Risk、Agent/Skill Assignment。用户明确确认后运行 `<入口> work confirm <file> --statement <真实确认摘要>`；最后才运行 `work accept`，继任 Work 则运行 `run successor`。

任何已确认字段发生变化，原 Confirmation 自动失效，必须重新展示和确认。

## 3. Agent → Skill → Handoff

- `rules/` 是每个 Tick 的工程纪律；`agents/` 定义职责边界；`skills/` 定义可复用流程。三者都由 `capability route` 的 Digest 保护。
- Conductor 按 `routing.handoff_agents` 的顺序和 `assignments` 派发角色；前序角色未 `READY` 或 Handoff 已过期时，后序角色不能交接。每个派发包必须包含 Work Digest、目标、范围、输入、禁止项、产出和验证方法。角色只加载其 Assignment 中的 Skill。
- 平台支持多 Agent 时可以派发；不支持时由同一 LLM 顺序切换角色并如实说明隔离能力。R0/R1 不得伪装成独立 Agent 审查。
- 每个非 Conductor 角色结束时必须生成并记录 Role Handoff：`READY` 表示该职责完成；`NEEDS_WORK` 表示退回设计或实现并触发 `CORRECT`。
- 用 `<入口> handoff template ...` 生成绑定当前 Work/Artifact 的 JSON，再运行 `<入口> handoff record <file>`。Artifact Reviewer 必须引用相关 Evidence；Artifact 改变后其旧 Handoff 自动过期。
- `memory-curator` 是每个 Work 的最后角色：有长期影响时用 `memory template/check/record/status` 追加 verified Memory；没有长期影响时在 Handoff 中明确 `NO_MEMORY_CHANGE` 和理由。
- Agent、Skill 和 Handoff 都不能直接产生 Core Result。只有 Reducer 可以判定六种 Result。

## 4. 一个有副作用的 Tick

1. 用 `<入口> attempt template` 根据已读文件生成带 Relevant Input Digest 的单一 Proposal。
2. 运行 `attempt begin` 验证 Scope、Grant、Budget 和重复策略。
3. 只有 Kernel 允许继续时，紧邻真实动作前运行 `attempt dispatch`。
4. 只执行 Proposal 声明的 Action/Path；把真实平台结果写成 Receipt，再运行 `attempt observe`。
5. Receipt 丢失、Timeout、Crash、未声明修改或终态不明时运行 `attempt mark-unknown`；不得自动重试或假定成功。
6. 对 Required Criterion 运行 `verify`，记录所有 Routing 要求的 Handoff，最后运行 `reduce`。

Reviewer 不修改被审对象。`NEEDS_WORK` 或可信 FAIL Evidence 由实现角色通过新 Attempt 修复，Artifact 变化后重新运行受影响的 Verifier 和 Reviewer。

## 5. 中途需求变更

用户改变 Active Work 的 Goal、Scope、Criterion、Grant、Budget、风险或不可逆选择时：

1. 停止创建普通 Attempt；确认所有 `PREPARED`、`DISPATCHED`、`OBSERVED`、`UNKNOWN` Attempt 已被解析。
2. 对 `CONTINUE` 或 `CORRECT` Work 运行 `<入口> run supersede --reason <变更原因> --request <新原始请求>`。旧 Work、Attempt、Evidence 与 Handoff 保持不可变。
3. 从新请求重新执行 Intake → 用户确认 → Capability Route → Work Authoring → 用户最终确认。
4. 新 Work 保持 `work_id`、Revision 加一并绑定前任 Ledger Head；运行 `<入口> run successor <confirmed-work> --run-id <id>`。

不得把新需求直接写进旧 Work，也不得把 `WAIT_AUTH` 当作需求澄清通道。

## 6. Result 路由与恢复

- `CONTINUE`：选择 Routing 中尚未完成的角色或基于新 Evidence 提出新策略。
- `CORRECT`：承认 FAIL Evidence/`NEEDS_WORK` Handoff，交回相应设计或实现角色；不得重复相同输入和策略。
- `COMPLETE`：仅当全部 Required Criterion、Safety Invariant、Side Effect 与 Required Handoff 成立时报告完成，并附 Evidence/Handoff 摘要。
- `WAIT_AUTH`：说明具体 Effect 与 Scope，请求人类授权；授权进入 Successor Work。
- `BUDGET_EXIT`：停止动作，报告已用 Budget、未完成 Criterion/Handoff 和建议预算。
- `BLOCKED`：停止普通动作并报告机械原因。`UNKNOWN` 只能用只读 Reconciliation 解析；`WORK_SUPERSEDED` 必须启动已确认 Successor。

只允许报告 Reducer 的唯一结果：`CONTINUE`、`CORRECT`、`COMPLETE`、`BLOCKED`、`WAIT_AUTH` 或 `BUDGET_EXIT`。只有 `COMPLETE` 可以向用户报告 Work 完成。

`AGENTS.md` 只是平台 Adapter，不是 Core Truth；冲突时以固定 Protocol、Kernel 校验和 Reducer 结果为准并 fail-closed。
<!-- yuan:bootstrap:end -->

未安装 `.yuan/config.json` 时，上述 Managed Block 不激活；使用 Codex 原生能力维护 Yuan 源码。
