# Yuan 源码仓库

<!-- yuan:bootstrap:start -->
# Yuan Agent Bootstrap

当 `.yuan/config.json` 存在时，本项目启用 Yuan Harness。固定入口为：

```text
python -B .yuan/bin/yuan.pyz --root .
```

## 1. 每次对话先恢复事实

1. 运行 `<入口> status` 和 `<入口> capability list --brief`。命令失败、Integrity 校验失败、JSON 不可解析或能力 Digest 不匹配时返回 `BLOCKED`。只有需要完整能力元数据时才运行不带 `--brief` 的 `capability list`。
2. 不要每次会话全文读取 `.yuan/protocol.md`：Protocol 已由 Runtime 完成 Digest 绑定校验。只有当命中本 Bootstrap 未覆盖的决策条款（确认有效性、副作用类别、Result 语义、Replay 与恢复）时，才读取 `.yuan/protocol.md` 的对应章节。Protocol、Kernel、Active Work 和 Reducer 的机械结果高于 Rule、Agent、Skill 与聊天摘要。
3. 不得直接编辑 `.yuan/config.json`、`.yuan/protocol.md`、`.yuan/bin/`、`.yuan/install.json`、托管 Profile 或 `.yuan-run/`。`.yuan/drafts/` 仅保存 Work 接受前草稿；项目扩展写入 `.yuan/extensions/custom/`。
4. `BLOCKED` 且唯一原因是“没有 Active Work”表示正常空 Run，应进入需求 Intake；其他 `BLOCKED` 必须按机械原因恢复。

固定 Runtime 无法启动或安装记录损坏时，不能要求旧 Runtime 自证。改由 Yuan Source 外部入口 `python -B scripts/sync_project.py update <项目根目录>` 强制重建托管框架；该动作必须保持 `.yuan-run/`、`docs/memory/`、`.yuan/extensions/custom/` 与项目自有内容不变。更新后再恢复事实，诊断警告不触发旧 Runtime 回滚。

用户入口只表达意图、范围、限制或“继续”。不得要求用户用提示词指定从 Intake、某个 Agent 或某个 Skill 开始；这些节点只能由本 Bootstrap、固定 Runtime 状态、Memory 恢复结果和 `capability route` 自动触发。

`recover`、`rebuild` 与 `memory rebuild` 是操作员恢复命令，不属于正常需求流转；只有 Ledger Head、派生 Run Memory 或 Memory 派生索引损坏时才可使用，并应在结果中说明恢复原因。

## 2. 新需求：按风险确认

新项目、已完成 Work 后的新请求，以及被 Supersede 后的需求都执行同一流程。确认级别与风险和不可逆性挂钩：确认保护的是不可逆动作前的意图对齐，可逆的低风险任务只付轻量确认。

1. 用户用自然语言提出新需求时，Conductor 自动加载 `project-lifecycle` 与 `requirements-clarification` Assignment；不得要求用户点名内部阶段、Agent 或 Skill。
2. 运行 `<入口> memory resume --request <用户原始请求>`；先读取 `CURRENT.md` 对应的连续性检查点，再使用 Binding 未过期的长期知识。相关 Memory ID/Digest 写入 Intake 依据，`hypothesis` 只能作为待验证线索。
3. 风险预检：在生成 Intake 前，按 `rules/03-risk-and-review.md` 把请求归类为 R0/R1/R2——认证、权限、支付、密钥、数据删除、迁移、生产发布归 R0；常规功能、API、持久化、依赖升级归 R1；文档、小型样式、非行为配置归 R2。存疑时升一级，绝不降级；Intake 语义检查中发现 Blocking 问题时同样只能升级风险。
4. 运行 `<入口> intake template --request <用户原始请求>`，保存为 `.yuan/drafts/intake.json`，并把预检的风险等级与理由写入 `risk`。由 Product Analyst 语义检查目标、范围、失败影响与不可逆选择；会改变验收或安全边界的问题标记为 Blocking 并原样询问用户，不得替用户回答。R2 需求允许合并检查步骤、省略与风险无关的维度。
5. 运行 `<入口> seal <file>` 保存重新计算 Digest 的返回值，再运行 `<入口> intake check <sealed-file>`。`NEEDS_INPUT` 时继续提问。
6. R2 轻量泳道：`intake check` 返回 `NEEDS_CONFIRMATION` 时展示返回的 `summary`（需求、问题答案、假设、风险、Signals），取得用户一次确认；然后用同一确认声明依次运行 `intake confirm`、起草 Work（`work template` + `bind-verifier`）、`work confirm` 与 `work accept`，不再就 Work 单独询问用户。低风险任务的 Work 形态由风险路由与 Verifier、Reducer 机械兜底；起草结果明显偏离用户请求时必须停下来说明。
7. R0/R1 完整泳道：先展示需求摘要（至少包含需求、问题答案、假设、风险、Signals 与 Subject Digest，不能只询问“是否确认”），用户确认后运行 `<入口> intake confirm <file> --statement <真实确认摘要>`；再起草 Work 并单独展示完整 Work，用户第二次确认后运行 `work confirm`，最后 `work accept`。
8. 运行 `<入口> capability route --risk <level> [--signal <signal>] --brief`。Routing 是 Agent、Skill 与审查要求的唯一来源；不得手工降级风险、删除角色或凭 `use_when` 另造路由。只读取当前阶段要派发角色对应的 Agents/Skills 文件（`assignments` 已指明每个角色加载哪些 Skill），不得预读全部路由引用的全文。
9. 运行 `<入口> work template --intake <confirmed-intake>`（继任时加 `--successor`）。加载 `work-authoring` 与 `verifier-authoring`，编辑 Goal、Artifact Scope、Grant、Budget、至少一个 Required Criterion 和 Safety Invariant。Verifier 只能先写入 `.yuan/drafts/verifiers/`，从 `sys.argv[1]` 读取项目根目录，只读验证 Artifact，并输出一个 JSON Object：`{"status":"PASS|FAIL","assertions":[...]}`。用 `work bind-verifier` 固定 Closure。
10. 开放平台中的 Confirmation 是可审计对话回执，不冒充密码学签名。任何已确认字段发生变化，原 Confirmation 自动失效，必须重新展示和确认。

## 3. Agent → Skill → Handoff

- `rules/` 是每个 Tick 的工程纪律；`agents/` 定义职责边界；`skills/` 定义可复用流程。三者都由 `capability route` 的 Digest 保护。
- Conductor 按 `routing.handoff_agents` 的顺序和 `assignments` 派发角色；前序角色未 `READY` 或 Handoff 已过期时，后序角色不能交接。每个派发包必须包含 Work Digest、目标、范围、输入、禁止项、产出和验证方法。角色只加载其 Assignment 中的 Skill。
- 平台支持多 Agent 时可以派发；不支持时由同一 LLM 顺序切换角色并如实说明隔离能力。R0/R1 不得伪装成独立 Agent 审查。
- 每个非 Conductor 角色结束时必须生成并记录 Role Handoff：`READY` 表示该职责完成；`NEEDS_WORK` 表示退回设计或实现并触发 `CORRECT`。
- 用 `<入口> handoff template ...` 生成绑定当前 Work/Artifact 的 JSON，再运行 `<入口> handoff record <file>`。Artifact Reviewer 必须引用相关 Evidence；Artifact 改变后其旧 Handoff 自动过期。
- `memory-curator` 维护两条时间线：每次角色交接、会话暂停或阻塞前用 `memory checkpoint` 更新连续性；形成稳定知识、已确认决策或问题经验时用 `memory template/check/record/status` 追加相应类型的长期 Memory。知识需要 PASS，决策绑定用户确认，经验绑定 FAIL/Attempt；不得把猜测写成 verified。Work 收尾没有长期变化时仍需保存最终检查点，并在 Handoff 中说明 `NO_MEMORY_CHANGE`。
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
3. 从新请求重新执行风险预检、Intake、按风险确认、Capability Route、Work Authoring 与用户最终确认。
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
