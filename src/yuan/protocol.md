# Yuan Core Protocol 0.4

状态：Normative。参考 Kernel 实现本文中的确定性条款；每个 Run 固定 Protocol 与 Kernel 的 SHA-256。

## 1. 目标与边界

Yuan 约束非确定性 LLM，使软件工程工作可验证、可恢复、可审计。LLM 提出意图与策略；Harness 负责 Validation、Authorization、Effect Record、Evidence Validity、Replay 与 Completion。

Core 有五项职责，而不是强制要求五个文件：

1. Protocol：稳定语义与 State Machine。
2. Work Contract：已确认 Intake、确定性 Routing、不可变目标、Scope、Grant、Budget 与 Acceptance Criterion。
3. Run Memory：有界、可丢弃的权威历史 Projection。
4. Attempt：一个有界 Hypothesis/Action 及其 Effect Journal。
5. Evidence：绑定 Artifact 与 Verifier 的不可变 Observation。

Agent Role、Planning Style、Git Workflow、TDD、Deployment 与平台 Prompt 属于 Policy 或 Adapter，永远不是 Core Truth。

Intake、Confirmation、Routing 与 Role Handoff 没有增加新的 Core Primitive：前三者是 Work Contract 的形成与绑定记录，Handoff 是 Ledger 中证明角色职责履行的类型化 Event。它们不能替代 Acceptance Evidence。

## 2. 需求确认与风险路由

- Work 接受前必须存在已确认 Intake，固定原始请求、阻塞问题及答案、显式假设、风险等级和 Routing Signal。
- Blocking Question 未回答时只能返回 `BLOCKED/NEEDS_INPUT`；需求摘要尚未确认时只能返回 `BLOCKED/NEEDS_CONFIRMATION`。需求澄清不是 Authorization，不使用 `WAIT_AUTH`。
- Confirmation 必须绑定其完整 Subject Digest。被绑定字段改变时 Confirmation 自动失效；开放平台只声明 `AUDITED` 对话回执，不冒充不可伪造的人类签名。
- 已安装 Capability Profile 必须以纯函数从 Risk/Signal 生成唯一 Routing。Work 接受时 Kernel 重算并逐字节比较，阻止角色或 Skill 被手工删减。
- Verifier Closure、完整 Work 和 Routing 必须再次获得用户最终确认，随后才能接受 Work。

## 3. Profile

- `GUIDED`：只提供 Protocol 引导，不声明机械隔离能力。
- `AUDITED`：在 Attempt 前后生成 Artifact Snapshot，并阻断未声明 Mutation；它是开放 Agent 平台的默认 Profile。
- `ENFORCED`：所有副作用必须经过符合规范的 Yuan Port。只有平台确实限制原生工具时才能声明该 Profile。

Profile 必须显式声明，弱 Profile 不得冒充强 Profile。

## 4. 不可变事实

Work、Attempt、Evidence 与 Event 使用 Canonical JSON 且不可变，其 Identity 为 SHA-256。Ledger 是有序 Hash Chain；Blob 使用 SHA-256 内容寻址。Run Memory 与人类报告都是派生 Projection，不能覆盖 Ledger。

Canonical JSON 使用 UTF-8、Key Sort、Compact Encoding、保留 Unicode 并拒绝 NaN。Record Digest 只省略其顶层 `digest` 字段。

## 5. Tick

一个 Tick 必须有界：

1. 验证固定的 Protocol、Kernel、Work、Ledger 与 Projection。
2. Projection 缺失或陈旧时重建。
3. 最多接受一个 Proposal。
4. 验证 Scope、Grant、Budget、Input Fingerprint 与策略重复。
5. Mutation Dispatch 前持久化 `PREPARED`。
6. 通过 Port 执行（`ENFORCED`），或审计已声明的平台动作（`AUDITED`）。
7. 将 Observation、Postcondition 与 Evidence 绑定到当前 Artifact。
8. 按 Routing 记录角色的 `READY` 或 `NEEDS_WORK` Handoff；Artifact Reviewer Handoff 绑定当前 Artifact 和所引用 Evidence。
9. 确定性归约为唯一 Result。
10. Atomic Replace Projection。

在 Relevant Input 相同且没有更新 Evidence 时，禁止重复相同策略。

## 6. 副作用

Pure Attempt 使用 `NOT_APPLICABLE`。Mutating Attempt 只能遵循：

```text
PREPARED -> DISPATCHED -> OBSERVED -> COMMITTED
                 |            |
                 +----------> UNKNOWN
```

`PREPARED` 必须先于 Dispatch 持久化。`DISPATCHED` 表示真实世界可能已经改变。`OBSERVED` 绑定 Structured Receipt 与 Postcondition。`COMMITTED` 绑定无歧义的最终 Artifact。Dispatch 后发生 Crash、Timeout、Receipt 丢失、状态模糊或未声明 Mutation 时必须进入 `UNKNOWN`。

`UNKNOWN` 阻止 Completion 与自动重试。只有新的独立 Reconciliation Attempt 可以解析它。Core 不自动执行破坏性 Rollback。

## 7. Evidence

Evidence 只有满足以下条件才有效：

- Schema 与 Semantic Validation 通过。
- `PASS` Evidence 具有正数 Assertion、唯一 Assertion ID，且每项都通过。
- 绑定 Active Work Revision、Source Attempt、准确 Artifact Manifest、Environment Fingerprint、Harness 与预绑定 Verifier。
- 包含 Structured Receipt/Output Digest。
- 满足 Acceptance Criterion 的 Independence 要求。

Exit Code、文字声明、Self Review、空 Test Suite 或陈旧 Artifact 都不是 Completion Evidence。结构有效的 `FAIL` Evidence 是可信反证，可触发 `CORRECT`，但不能满足 Completion。

Role Handoff 证明 Routing 中某角色已经履行职责。Handoff 按 Work 中的确定顺序记录，前序角色未 `READY` 或其 Artifact Binding 已过期时，后序角色不得交接。`NEEDS_WORK` 是可信的角色退回；`READY` 只有绑定 Active Work，且对 Artifact Reviewer 仍绑定当前 Artifact 时有效。Handoff 不能让失败或缺失的 Criterion Evidence 变成 PASS。

## 8. Completion 与 Result

`COMPLETE` 要求：每个 Required Acceptance Criterion 都有当前有效 PASS Evidence；全部 Safety Invariant 成立；所有 Side Effect 都是 `COMMITTED` 或 `NOT_APPLICABLE`；Routing 要求的全部 Role Handoff 都是当前有效 `READY`。

Reducer 按以下固定顺序返回第一个满足的 Result：

1. `BLOCKED`：状态不一致、存在 `UNKNOWN`、发生 Corruption、Work 已 `WORK_SUPERSEDED`，或没有安全合法的下一步。
2. `WAIT_AUTH`：具体且原本合法的下一步缺少 Authorization。
3. `BUDGET_EXIT`：已记录的具体 Proposal 无法放入剩余 Budget。
4. `COMPLETE`：且仅当 Completion Predicate 成立。
5. `CORRECT`：新 Evidence 反驳当前 Hypothesis，或最新 Role Handoff 为 `NEEDS_WORK`，且仍有合法替代策略。
6. `CONTINUE`：工作取得进展且存在合法下一步。

Result 只能是：`CONTINUE`、`CORRECT`、`COMPLETE`、`BLOCKED`、`WAIT_AUTH`、`BUDGET_EXIT`。

## 9. Authorization 与 Budget

Authorization 默认拒绝。Work Grant 必须同时匹配 Action Type、Side-effect Class 与每个受影响 Relative Path。Path 不得为 Absolute Path、逃逸 Artifact Root、穿越 Link 或命中禁止 Scope。Budget Maximum 不可变。

每个 Attempt 固定 Charge 一个 Tick 和一个 Attempt，并附带声明的 Tool/Time Cost。如果具体 Proposal 无法放入剩余额度，Ledger 记录 `BUDGET_EXHAUSTED`，此后 `BUDGET_EXIT` Predicate 才成立。Attempt 执行期间数值恰好达到 Maximum，不会使该 Attempt 产生的 Evidence 失效。

只有具体合法动作超出当前 Grant 或属于 High-impact Effect 时才请求 Human Authorization。授权产生新 Work Revision 或 Content-addressed Grant Event，绝不编辑历史。

## 10. 需求变更、Replay 与恢复

Active Work 的已确认字段不能原地修改。用户在 `CONTINUE` 或 `CORRECT` 期间改变需求时，必须先解析所有在途/未知 Attempt，再追加 `WORK_SUPERSEDED` Event。旧 Run 归约为带 `successor_required` 的 `BLOCKED`；新的 Intake、两次 Confirmation、Routing 和 Successor Work 必须绑定旧 Ledger Head。旧 Work、Attempt、Evidence 与 Handoff 均保持可审计。

Replay 必须验证完整 Event Chain、Record Digest、Work Binding、连续 Attempt Sequence、Journal Transition、Artifact Binding、Budget 与 Evidence。任何歧义都 fail-closed。

Projection 只保存有界 Pointer，可删除并重建。Replay 绝不能从已存储的 Result 推断 `COMPLETE`。

## 11. 升级权威

运行中的 Core 不批准或否决继任者。框架源码是普通 Version-controlled Project；维护者或 CI 在 Active Run 外构建并验证 Candidate，发布 Hash/Signature，并为下一个 Run 显式选择它。已有 Run 保持固定。Migration Adapter 只能把旧不可变 Record 转换为新版本 Record，不能重写历史。

Install/Update/Diagnose 是外部控制面操作：只能从框架源码外部发起，绝不依赖被替换 Runtime 的自证、旧 Install Record、Active Work 或旧 Conformance 作为放行门禁。控制面失败必须输出 Exit Code、stdout/stderr 尾部与涉及路径等完整取证。旧状态不一致不是控制面错误，而是新 Runtime 激活后的前向 Reconciliation 任务；Conformance 在 Release 构建期执行并以证据绑定 Artifact，部署期只验证证据。

## 12. Conformance

符合规范的实现必须提供确定性 Fixture，覆盖 Canonical Hash、Invalid Record、Ledger Tamper、Replay Equivalence、全部 Reducer Branch、Intake 阻塞与确认失效、确定性风险路由、Work 最终确认、Role Handoff Gate/过期/退回、中途 Supersede/Successor、Evidence Attack、Budget Exhaustion、Authorization、Path Escape、Undeclared Mutation、`UNKNOWN` 与 Crash Recovery。可选 Adapter 与 Policy 不能改变 Core Result。
