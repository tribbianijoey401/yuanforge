# Yuan Core Protocol 0.2

状态：Normative。参考 Kernel 实现本文中的确定性条款；每个 Run 固定 Protocol 与 Kernel 的 SHA-256。

## 1. 目标与边界

Yuan 约束非确定性 LLM，使软件工程工作可验证、可恢复、可审计。LLM 提出意图与策略；Harness 负责 Validation、Authorization、Effect Record、Evidence Validity、Replay 与 Completion。

Core 有五项职责，而不是强制要求五个文件：

1. Protocol：稳定语义与 State Machine。
2. Work Contract：不可变意图、Scope、Grant、Budget 与 Acceptance Criterion。
3. Run Memory：有界、可丢弃的权威历史 Projection。
4. Attempt：一个有界 Hypothesis/Action 及其 Effect Journal。
5. Evidence：绑定 Artifact 与 Verifier 的不可变 Observation。

Agent Role、Planning Style、Git Workflow、TDD、Deployment 与平台 Prompt 属于 Policy 或 Adapter，永远不是 Core Truth。

## 2. Profile

- `GUIDED`：只提供 Protocol 引导，不声明机械隔离能力。
- `AUDITED`：在 Attempt 前后生成 Artifact Snapshot，并阻断未声明 Mutation；它是开放 Agent 平台的默认 Profile。
- `ENFORCED`：所有副作用必须经过符合规范的 Yuan Port。只有平台确实限制原生工具时才能声明该 Profile。

Profile 必须显式声明，弱 Profile 不得冒充强 Profile。

## 3. 不可变事实

Work、Attempt、Evidence 与 Event 使用 Canonical JSON 且不可变，其 Identity 为 SHA-256。Ledger 是有序 Hash Chain；Blob 使用 SHA-256 内容寻址。Run Memory 与人类报告都是派生 Projection，不能覆盖 Ledger。

Canonical JSON 使用 UTF-8、Key Sort、Compact Encoding、保留 Unicode 并拒绝 NaN。Record Digest 只省略其顶层 `digest` 字段。

## 4. Tick

一个 Tick 必须有界：

1. 验证固定的 Protocol、Kernel、Work、Ledger 与 Projection。
2. Projection 缺失或陈旧时重建。
3. 最多接受一个 Proposal。
4. 验证 Scope、Grant、Budget、Input Fingerprint 与策略重复。
5. Mutation Dispatch 前持久化 `PREPARED`。
6. 通过 Port 执行（`ENFORCED`），或审计已声明的平台动作（`AUDITED`）。
7. 将 Observation、Postcondition 与 Evidence 绑定到当前 Artifact。
8. 确定性归约为唯一 Result。
9. Atomic Replace Projection。

在 Relevant Input 相同且没有更新 Evidence 时，禁止重复相同策略。

## 5. 副作用

Pure Attempt 使用 `NOT_APPLICABLE`。Mutating Attempt 只能遵循：

```text
PREPARED -> DISPATCHED -> OBSERVED -> COMMITTED
                 |            |
                 +----------> UNKNOWN
```

`PREPARED` 必须先于 Dispatch 持久化。`DISPATCHED` 表示真实世界可能已经改变。`OBSERVED` 绑定 Structured Receipt 与 Postcondition。`COMMITTED` 绑定无歧义的最终 Artifact。Dispatch 后发生 Crash、Timeout、Receipt 丢失、状态模糊或未声明 Mutation 时必须进入 `UNKNOWN`。

`UNKNOWN` 阻止 Completion 与自动重试。只有新的独立 Reconciliation Attempt 可以解析它。Core 不自动执行破坏性 Rollback。

## 6. Evidence

Evidence 只有满足以下条件才有效：

- Schema 与 Semantic Validation 通过。
- `PASS` Evidence 具有正数 Assertion、唯一 Assertion ID，且每项都通过。
- 绑定 Active Work Revision、Source Attempt、准确 Artifact Manifest、Environment Fingerprint、Harness 与预绑定 Verifier。
- 包含 Structured Receipt/Output Digest。
- 满足 Acceptance Criterion 的 Independence 要求。

Exit Code、文字声明、Self Review、空 Test Suite 或陈旧 Artifact 都不是 Completion Evidence。结构有效的 `FAIL` Evidence 是可信反证，可触发 `CORRECT`，但不能满足 Completion。

## 7. Completion 与 Result

`COMPLETE` 要求：每个 Required Acceptance Criterion 都有当前有效 PASS Evidence；全部 Safety Invariant 成立；所有 Side Effect 都是 `COMMITTED` 或 `NOT_APPLICABLE`。

Reducer 按以下固定顺序返回第一个满足的 Result：

1. `BLOCKED`：状态不一致、存在 `UNKNOWN`、发生 Corruption，或没有安全合法的下一步。
2. `WAIT_AUTH`：具体且原本合法的下一步缺少 Authorization。
3. `BUDGET_EXIT`：已记录的具体 Proposal 无法放入剩余 Budget。
4. `COMPLETE`：且仅当 Completion Predicate 成立。
5. `CORRECT`：新 Evidence 反驳当前 Hypothesis，且仍有合法替代策略。
6. `CONTINUE`：工作取得进展且存在合法下一步。

Result 只能是：`CONTINUE`、`CORRECT`、`COMPLETE`、`BLOCKED`、`WAIT_AUTH`、`BUDGET_EXIT`。

## 8. Authorization 与 Budget

Authorization 默认拒绝。Work Grant 必须同时匹配 Action Type、Side-effect Class 与每个受影响 Relative Path。Path 不得为 Absolute Path、逃逸 Artifact Root、穿越 Link 或命中禁止 Scope。Budget Maximum 不可变。

每个 Attempt 固定 Charge 一个 Tick 和一个 Attempt，并附带声明的 Tool/Time Cost。如果具体 Proposal 无法放入剩余额度，Ledger 记录 `BUDGET_EXHAUSTED`，此后 `BUDGET_EXIT` Predicate 才成立。Attempt 执行期间数值恰好达到 Maximum，不会使该 Attempt 产生的 Evidence 失效。

只有具体合法动作超出当前 Grant 或属于 High-impact Effect 时才请求 Human Authorization。授权产生新 Work Revision 或 Content-addressed Grant Event，绝不编辑历史。

## 9. Replay 与恢复

Replay 必须验证完整 Event Chain、Record Digest、Work Binding、连续 Attempt Sequence、Journal Transition、Artifact Binding、Budget 与 Evidence。任何歧义都 fail-closed。

Projection 只保存有界 Pointer，可删除并重建。Replay 绝不能从已存储的 Result 推断 `COMPLETE`。

## 10. 升级权威

运行中的 Core 不批准或否决继任者。框架源码是普通 Version-controlled Project；维护者或 CI 在 Active Run 外构建并验证 Candidate，发布 Hash/Signature，并为下一个 Run 显式选择它。已有 Run 保持固定。Migration Adapter 只能把旧不可变 Record 转换为新版本 Record，不能重写历史。

## 11. Conformance

符合规范的实现必须提供确定性 Fixture，覆盖 Canonical Hash、Invalid Record、Ledger Tamper、Replay Equivalence、全部 Reducer Branch、Evidence Attack、Budget Exhaustion、Authorization、Path Escape、Undeclared Mutation、`UNKNOWN` 与 Crash Recovery。可选 Adapter 与 Policy 不能改变 Core Result。
