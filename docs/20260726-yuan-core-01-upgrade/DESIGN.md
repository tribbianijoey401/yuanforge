# Yuan Core 0.1 冻结设计

> 设计状态: `0.1.0-candidate / frozen-for-implementation`
> 冻结日期: 2026-07-26
> 来源: clean-room 第一性原理设计 + 独立 Design Review + 用户明确确认
> 约束: 本文不从现有 YuanForge 的角色、阶段、Gate 或目录结构推导 Core

## 1. 定义

Yuan 不是 Agent 编排框架，而是约束非确定性 LLM 的最小软件工程 Harness：

```text
Human → Work Contract
              ↓
Persistent Memory → Context Builder → LLM candidate
                                         ↓
                          Deterministic Harness
                    validate → journal → execute
                              → collect evidence
                                         ↓
                         Deterministic Reducer
```

LLM 是唯一自适应推理器，但不是事实源、执行裁判或完成裁判。

## 2. 五个 Core 原语

| 原语 | 必要职责 | 删除后的独立失败 |
|------|----------|-----------------|
| `Protocol` | 定义推进、证据、授权、预算、恢复和 reducer 规则 | 相同状态可得到互相冲突的完成判定 |
| `Work Contract` | 固化意图、类型化 AC、约束、授权边界和 verifier 绑定 | 冷启动后无法确定要完成什么 |
| `Run Memory` | 保存有界、可重建的当前运行投影 | 必须重放无限历史且无法确定当前失败假设 |
| `Attempt` | 记录一次有限尝试、策略指纹和副作用 journal | 无法阻止无新证据的同策略无限重试 |
| `Evidence` | 保存不可变、可追溯的外部观察和验证回执 | “通过”退化为 LLM 自述 |

`Knowledge` 不是 Core 原语。删除 Knowledge 只降低效率，不破坏当前 Work 的正确性，因此它属于可选扩展。

## 3. 六种 Tick 结果

| 结果 | 确定性语义 |
|------|------------|
| `CONTINUE` | 获得了与未满足 AC 相关的新证据，并存在合法下一步 |
| `CORRECT` | 新证据推翻当前假设，仍有不同策略和预算 |
| `COMPLETE` | 全部完成谓词由有效证据满足 |
| `BLOCKED` | 没有安全合法动作，或状态/副作用结果无法确定 |
| `WAIT_AUTH` | 下一步明确，但超出已授予的授权边界 |
| `BUDGET_EXIT` | Tick、工具或策略预算耗尽；不得等同成功 |

同策略重试拒绝条件：

```text
same strategy fingerprint
+ same relevant inputs
+ no new evidence
= reject execution
```

## 4. 完成谓词

```text
COMPLETE :=
  every required typed AC has valid evidence
  AND evidence targets the current artifact and declared environment
  AND every safety invariant holds
  AND no side effect is pending or UNKNOWN
```

以下事实均不能单独推出 COMPLETE：

- LLM 声称完成；
- 所有 Task 终态；
- 命令退出码为 0；
- 断言数量为 0；
- Review PASS；
- Git 干净；
- 文档齐全；
- 已提交、已合并、已部署。

## 5. 八项 Mandatory Semantics

1. **Verifier 预绑定**：每个类型化 AC 必须在 Work revision 冻结时绑定预先信任的 verifier；LLM 不得在看到结果后替换判据。
2. **不可变 revision**：Work、Protocol、Harness 和 Validator 都以不可变 revision 标识；任何修改创建新 revision。
3. **证据三重绑定**：Evidence 必须绑定产物哈希、环境标识和 verifier revision/hash，缺一不可。
4. **验证失败关闭**：verifier 崩溃、零断言、日志缺失、输出不可解析、范围错误或证据过期一律不通过。
5. **状态可重建**：Run Memory 是有界投影，不是唯一历史；损坏时须从 Work、Attempt、Evidence 重建。
6. **副作用不可绕行**：LLM 不得绕过 Harness 直接调用会改变世界的工具；所有副作用先校验授权与范围。
7. **自修改信任根**：框架自修改必须由旧信任根、独立 verifier 或明确人工授权验证，不能仅由新版本验证自身。
8. **副作用崩溃语义**：副作用 Attempt 使用 `PREPARED → EXECUTING → OBSERVED → COMMITTED/UNKNOWN`；无法确认结果时必须进入 UNKNOWN 并阻塞重复执行。

## 6. 一次 Tick

1. 读取不可变 Protocol revision、Work revision 与当前 Run Memory。
2. 按指针渐进加载必要产物和 Evidence。
3. LLM 提出一个假设及至多一个变更性动作。
4. Harness 校验范围、授权、预算、策略重复和 verifier 绑定。
5. 变更世界前写入 `PREPARED` Attempt；执行期间更新 journal。
6. 调用已绑定 verifier，收集结构化 Evidence。
7. 校验证据绑定、新鲜度、断言数量和完整性。
8. Reducer 只归约为六种结果之一，并原子更新 Run Memory 投影。

## 7. 最小平台 Port

Core 正确性只要求：

1. 文件读取与原子写入；
2. 命令执行及结构化回执；
3. 一次 LLM 推理。

多 Agent、后台任务、特殊 Goal API、数据库、消息队列、Git 和部署系统均为可选能力。Adapter 缺失能力时必须标记 unsupported，不能静默改变 Protocol 语义。

## 8. Trust Root 与验证层

### Genesis Trust Root

- 用户确认的本文与 FEATURE AC；
- 独立 Design Review 的通过结论；
- 冻结的 bootstrap verifier 负向 fixtures 及预期结果；
- M0a 原始现场快照、基线 commit 和哈希 manifest。

### 非信任输入

现有 `scripts/run-ptg-cal-check.py` 和引用但不存在的 `framework-self-test` 不得作为 Genesis 证明。只有新 bootstrap verifier 先证明自己能拒绝 empty candidate、零断言和 known-bad fixtures 后，才可验证 inert Core candidate。

### 证据层

| 事实 | 机制 |
|------|------|
| 逻辑真值 | 绑定到 AC 的测试/verifier Evidence |
| 物理真值 | 真实或隔离环境的命令/集成 Evidence |
| 结构真值 | 独立 bootstrap/core conformance verifier |
| 审查真值 | 独立 reviewer 产生的 Evidence；不能替代前三层 |

## 9. Authority 与迁移不变量

1. 任一时刻只有一个 writable runtime authority。
2. Shadow conversion 单向生成新投影，不双写旧、新状态。
3. authority switch 前必须通过历史重放、writer guard、回退演练和 Adapter conformance。
4. 旧规范条款必须逐条进入 `Core / Extension / Knowledge / Fixture / Obsolete-with-proof`，覆盖率 100%。
5. `Obsolete-with-proof` 必须保存原条款 hash、淘汰原因和替代条款或反例 fixture。
6. 清场前保留内容寻址回退包；用户看过完整报告并再次确认后才 tombstone。

## 10. Core 之外

以下机制只能作为经过评估证明有净收益的 Extension、recipe 或 Knowledge：

- 固定专家团、角色顺序与多 Agent；
- 通用 Phase、Gate 编号与 DAG；
- TDD 的固定书写顺序；
- 固定审查人数和档位角色；
- PTG/CAL 名称与特定测试工具；
- DocsOS、知识图谱、Promotion；
- Git、PR、部署状态机；
- UI 规则和行业设计知识。

它们可以产生 Evidence，但不能重定义 Core 的完成语义。
