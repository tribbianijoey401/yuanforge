# Yuan vNext 架构

## 一句话模型

Yuan 是包裹 Agent 平台的最小确定性控制内核：LLM 提出候选，平台执行动作，不可变 Record 保存事实，预绑定 Verifier 生成 Evidence，纯 Reducer 给出结果。

```mermaid
flowchart LR
    U["人类意图"] --> W["不可变 Work"]
    L["LLM Proposal"] --> A["Attempt"]
    W --> A
    A --> P["平台动作 / Port"]
    P --> M["Artifact Manifest + Receipt"]
    M --> V["预绑定 Verifier"]
    V --> E["不可变 Evidence"]
    W --> R["纯 Reducer"]
    A --> R
    E --> R
    R --> O["六种结果之一"]
    W --> G["Hash-chain Ledger"]
    A --> G
    E --> G
    G --> RM["可重建 Run Memory"]
```

## 权威模型

系统只有三类权威：

1. 人类选择已发布的 Protocol/Kernel，并定义 Work。
2. Kernel 验证 Record、Grant、Budget、副作用和 Evidence。
3. Verifier 证明具体 Acceptance Criterion 对应的事实。

LLM 从来不是上述权威。`AGENTS.md` 只是帮助 LLM 进入协议的 Adapter 指令。

运行中的 Kernel 只对当前 Run 有权威，无权批准或否决其继任版本。这样既消除了“旧规则批准新规则”的循环，又不允许候选版本静默替换当前 Run 已固定的版本。

## 模块边界

| Module | 机械职责 |
|---|---|
| `canonical.py` | 唯一 Canonical JSON 编码与 SHA-256 Identity |
| `paths.py` | Relative Path 约束与 Scope 匹配 |
| `validate.py` | Work、Proposal、Evidence、Grant 与 Binding 语义 |
| `artifacts.py` | 有界稳定枚举、Manifest 与 Diff |
| `ledger.py` | 不可变 Event/Blob、Hash Chain、Atomic Head 与恢复 |
| `runtime.py` | Work/Attempt/Evidence 生命周期与确定性 Replay |
| `reducer.py` | 纯六结果判定 |
| `identity.py` | 已安装 Protocol、Kernel 与 Environment Binding |
| `cli.py` | 只做 JSON Adapter，不引入第二套语义 |

Core 只使用 Python 标准库。发行物可以是单个 `yuan.pyz`，不要求 Daemon、Database、Scheduler 或平台服务。

项目安装器属于 Deployment Adapter。它把 `yuan.pyz` 固定到 `.yuan/bin/`，以 Managed Block 合并 `AGENTS.md`，并通过外部同步命令更新；它不能修改 Core Result。Candidate 必须绑定 Release Manifest、Conformance 与 Source，所有部署动作通过项目锁串行化。Runtime 更新只在没有 Active Work 或当前 Work 已 `COMPLETE` 时激活，非终态只 Stage Candidate；更新前的完整部署快照允许在相同 Work Binding 边界安全回滚。

## Profile 保证等级

| 能力 | GUIDED | AUDITED | ENFORCED |
|---|---:|---:|---:|
| Protocol 引导 | 是 | 是 | 是 |
| 不可变 Ledger/Replay | 是 | 是 | 是 |
| 预绑定 Verifier 执行 | 是 | 是 | 是 |
| 未声明 Artifact 修改检测 | 不承诺 | 是 | 是 |
| 物理副作用中介 | 否 | 否 | 是 |

参考实现提供 `GUIDED` 与 `AUDITED`。在安装符合规范的 Action Port 前，配置会拒绝宣称 `ENFORCED`。

## Record 拓扑

```text
.yuan/
  config.json                 Profile 与不可变 Binding
  protocol.md                 固定的 Protocol Bytes
.yuan-run/
  current.json                可替换 Run Pointer
  blobs/sha256/aa/bb...       内容寻址 Receipt/Manifest
  runs/<run-id>/
    events/00000001-<sha>.json
    head.json                 可恢复的 Hash-chain Pointer
    run-memory.json           一次性 Projection
```

Work、Attempt Transition、Evidence 与 Result 都是 Ledger Event。Artifact Manifest 与 Tool Receipt 是 Blob。Head 和 Run Memory 是 Projection；丢失它们不会破坏权威历史。

## 标准 AUDITED 生命周期

1. `yuan init` 固定 Protocol、Kernel、Environment 与 Profile。
2. `yuan work template` 创建 Work 草稿。
3. `yuan work bind-verifier` 计算 Verifier Closure Hash 并重新封装 Work。
4. `yuan work accept` 验证 Work 并固定初始 Artifact。
5. `yuan attempt begin` 验证 Relevant Input、Grant、Budget 与重复策略。
6. `yuan attempt dispatch` 持久化打开 Mutation Window。
7. Agent 只执行已声明动作。
8. `yuan attempt observe` 关闭窗口、验证 Diff，并记录 `COMMITTED` 或 `UNKNOWN`。
9. `yuan verify` 直接运行预绑定只读 Verifier 并创建 Evidence。
10. `yuan reduce` 派生唯一结果并刷新 Run Memory。

## 安全声明

`AUDITED` 是开放 Agent 平台上的 Detective/Corrective Harness。它能检测 Out-of-band Artifact 修改并使陈旧 Evidence 失效，但不能认证 `.yuan-run` 是否被拥有任意写权限的恶意进程重写。`ENFORCED` 需要平台或 OS 隔离；它是更强的部署 Profile，不是 Prompt 声明。

## 工程能力层

Core 只定义确定性语义，不承担全部软件工程知识。发行包默认携带 `vibe-coding` Capability Profile：Rules 约束工作纪律，Agents 隔离职责，Skills 提供按需流程。它们只能帮助编写 Work/Proposal、指导动作或生成 Evidence，不能增加 Primitive、Result 或修改 `COMPLETE` 谓词。

托管能力逐文件绑定到 Capability Manifest 和 Install Record，并参与安装事务、更新、完整性检查与回滚。每个 Bundled Profile 通过 `profile.json` 自描述，Kernel 无需硬编码 Profile 名称；Runtime 的 `capability list/resolve` 提供确定性发现与最小上下文加载。

项目能力位于 `.yuan/extensions/custom/<extension-id>/`，不进入框架托管集合。Custom Descriptor 自绑定逐文件 Digest；损坏的自定义扩展被隔离并报告，不会使 Core 或托管 Profile 成为隐藏依赖。
