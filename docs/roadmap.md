# 可执行开发路线图

路线按语义依赖排序。每个里程碑只有在对应 Conformance Test 通过后才算完成，文字声明不能代替 Evidence。

## M0 — Protocol 与纯 Kernel（已完成）

- Canonical JSON/SHA-256。
- Work、Proposal、Evidence、Path、Grant 与 Verifier 验证。
- 固定优先级的六结果 Reducer。
- Protocol 与 Kernel 规模预算。

退出 Evidence：Canonicalization 与全部六个 Reducer 分支的确定性测试。

## M1 — 持久化 AUDITED Runtime（已完成）

- 不可变 Event Hash Chain 与内容寻址 Blob Store。
- Artifact Baseline/Diff 与 Out-of-band Mutation 检测。
- `PREPARED -> DISPATCHED -> OBSERVED -> COMMITTED/UNKNOWN`。
- Run Memory 重建与 Head 恢复。
- Relevant Input Fingerprint 与无新 Evidence 重复策略拒绝。
- 明确的 `WAIT_AUTH` 与 `BUDGET_EXIT`。

退出 Evidence：Happy Path Replay 等价、Ledger 篡改、Head 中断、未授权动作、超额 Charge、陈旧输入、未声明修改与 Out-of-band 修改测试。

## M2 — Verifier Gateway（已完成）

- Work 预绑定 Verifier Closure。
- 无 Shell、隔离 Python、Timeout 与只读 Audit Hook。
- Verifier 前后 Artifact 检查。
- Kernel 生成 PASS/FAIL Evidence，并强制正数 Assertion。
- CLI 不提供任意导入 PASS Evidence 的入口。

退出 Evidence：合法完成、可信 FAIL -> `CORRECT`、伪造 Verifier、陈旧 Artifact、Closure 不匹配与 Protocol/Kernel Pin 测试。

## M3 — Reconciliation 与 Run 继任（已完成）

- 为 `UNKNOWN` 提供带独立 Probe 的 Typed Reconciliation Attempt。
- 通过 Terminal Resolution Event 确认 `COMMITTED`/`NO_EFFECT`，不重写原 Attempt。
- 新 Work Revision/New Run 显式绑定 Predecessor。
- Authorization Grant 作为新不可变 Revision 导入，而不是编辑历史。

退出 Evidence：`DISPATCHED`/`OBSERVED` 转 `UNKNOWN`、模糊状态保持 `BLOCKED`、`COMMITTED`/`NO_EFFECT` Reconciliation、越 Scope 拒绝与 Work Revision 继任测试。

## M4 — Adapter Conformance（已完成）

- Scoped File CAS、Bounded Command 与 LLM Proposal 的稳定 Port 接口。
- 每项能力显式 `SUPPORTED`/`UNSUPPORTED` 的 Capability Descriptor。
- Codex `AUDITED` Adapter 文档与机器 Descriptor。
- `ReferencePort` 提供可被受控平台独占接入的机械边界；开放 Agent 平台没有物理隔离时，CLI 与 Descriptor 继续拒绝虚假 `ENFORCED` 声明。

退出 Evidence：Adapter Negative Fixture、File CAS、无 Shell Bounded Command、Path Escape、Proposal Receipt 和机器可读 Conformance Report。

## M5 — 确定性发行（已完成）

- 可复现 `yuan.pyz`、内容寻址 Release Manifest 与 SHA-256 Checksum；身份签名由持有发布密钥的外部 Release Pipeline 负责，Core 不内置密钥。
- 在全新环境运行完整 Conformance Suite。
- 旧规则无权批准或否决新 Release。
- 本次暴力重构不再实现旧框架数据迁移。
- 轻量项目安装器固定 `yuan.pyz`、合并 Agent Bootstrap；当时实现的 Stage/Update/Rollback 语义已由 M9 的强制更新取代。

退出 Evidence：自包含 Zipapp Test、两次构建逐字节一致、Release/Source Hash 验证与完整 Conformance Suite。

## M6 — 可恢复部署（已完成）

本节记录当时退出 Evidence；其中 Update/Stage/Rollback 的产品语义已由 M9 取代，首次安装与发行验证仍保留。

- 安装、更新、状态与回滚共用 Project Deployment Lock。
- Candidate 强制绑定 Release Manifest、完整 Conformance、Harness Digest 与 Git/Package Source。
- 首次安装是可重试事务，失败不留下伪安装状态。
- 更新前保存完整 Deployment Snapshot，Rollback 恢复全部 Managed File 而非只替换 Runtime。
- `STAGED` Candidate 具有内容寻址 Metadata，并自动清理陈旧 Candidate。
- GitHub CI 验证 Push/PR；Tag Pipeline 发布 Checksum 与 Artifact Provenance。

退出 Evidence：非法 Run ID/Conformance 无残留、并发锁、Stage Metadata、完整 Update/Rollback、Wheel 安装和 CI Workflow。

## M7 — 可调用工程能力层（已完成）

- Bundled Capability Profile 自动发现与安装时显式选择。
- 带 `use_when` 的 Rules/Agents/Skills Catalog，以及 Runtime `list/resolve` 路由。
- 首个空 Run、Verifier 草稿、Work 接受与首个 `COMPLETE` 的闭合流程。
- Custom Extension 命名空间、逐文件 Digest、错误隔离和更新保留。
- Profile 文件增删参与安装事务、Snapshot 与 Rollback。

退出 Evidence：Catalog 完整性、Runtime 解析、Custom Extension 篡改隔离，以及空项目从 `BLOCKED: 没有 Active Work` 到 `COMPLETE` 的端到端测试。

## M8 — 用户意图与角色流程闭环（已完成）

- Intake 持久化 Blocking Question、Answer、Assumption、Risk/Signal 与第一次用户确认。
- 完整 Work Contract 在 Verifier、Grant、Budget 与 Routing 固定后获得第二次用户确认。
- Capability Workflow 确定性生成 Risk/Signal Route 和 Agent→Skill Assignment；Work 接受时 Kernel 重算，不能手工降级。
- 每个 Routing 角色通过不可变 `READY/NEEDS_WORK` Handoff 交接；Artifact Reviewer Handoff 随 Artifact 变化过期。
- `NEEDS_WORK` 进入 `CORRECT`；Required Evidence 与 Required Handoff 共同构成 Completion Predicate。
- 非终态需求变化通过 `WORK_SUPERSEDED` 和绑定旧 Head 的 Successor 闭环，不编辑历史。

退出 Evidence：未回答 Intake/未确认 Work 拒绝、确定性 Routing、Required/Stale/Negative Handoff Gate、未解析 Attempt 禁止 Supersede，以及确认后的 Successor 端到端测试。

## M9 — 强制 Runtime 更新、诊断能力与长期记忆（已完成）

- `update` 不再调用旧 Runtime，不检查版本、Install Record、Active Work 或 Conformance，不产生 `UNCHANGED/STAGED`，不保存或回滚旧框架。
- 更新重建全部托管框架，并对 `.yuan-run/` 与 `docs/memory/` 做前后内容指纹校验；Custom Extension 与项目自有 Managed Block 外内容保持不变。
- 外部 `diagnose` 输出 Runtime 命令、Exit Code、stdout/stderr、Memory 指纹和明确恢复路由。
- `debugging/deployment` Signal 确定性选择 Debugger、Runtime Maintainer 与完整 Skill；每个 Work 最终选择 Memory Curator。
- `yuan.memory/v1` 提供追加 Revision、Work/Evidence/Artifact/Ledger Binding、文件 stale 检测、上下文检索及 JSON/Markdown 索引重建。

退出 Evidence：损坏 Runtime/Config/Install Record 后强制修复、非终态 Work 立即更新、项目 Memory 字节保持、诊断路由、Memory Revision/Context/Staleness 与端到端 Handoff Gate 测试。

## 永久复杂度限制

- Protocol 不超过 500 个非空行。
- 纯状态 Core Kernel 限制为 2,000 个非空 Python 行；Deployment/Release 限制为 1,000 行，Capability/CLI 限制为 1,200 行，Platform Port 物理中介边界限制为 250 行，Long-term Memory 层限制为 400 行，空行不计。新增 Python 模块必须显式归类；职责分层避免一个聚合预算同时冻结互不相关的演进方向。
- Core 只使用标准库。
- 不要求 Daemon、SQLite/Database、Network Service、Role System 或隐藏 Extension。
- Extension 可以提出候选或生产 Evidence，但不能增加 Result 或改变 Core Completion Truth。
