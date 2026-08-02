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

退出 Evidence：自包含 Zipapp Test、两次构建逐字节一致、Release/Source Hash 验证与完整 Conformance Suite。

## 永久复杂度限制

- Protocol 不超过 500 个非空行。
- Reference Kernel 超过 3,000 行 Python 前必须进行 Design Review。
- Core 只使用标准库。
- 不要求 Daemon、SQLite/Database、Network Service、Role System 或隐藏 Extension。
- Extension 可以提出候选或生产 Evidence，但不能增加 Result 或改变 Core Completion Truth。
