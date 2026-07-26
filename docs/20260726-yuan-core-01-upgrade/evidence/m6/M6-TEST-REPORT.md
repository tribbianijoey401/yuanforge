# task-009 M6 Adapter Conformance — Independent Tester Report

> 被测提交：`798fce92c49aaa3aebd0ba4acb759435e4599173`
>
> 角色：独立 Tester（未参与 Core / Adapter 实现）
>
> 首轮判定：`FAIL — M6 Hard Gate BLOCKED`

## 同一套 conformance trace

每个声明为 `supported` 的 Adapter 必须用同一套 trace 证明：

| 边界 | 必须证明 |
|------|----------|
| filesystem | 有界枚举、读取哈希、原子替换、CAS、相对路径 containment |
| command | 有界可取消/超时执行、结构化回执、输出上限与完整流摘要、scope-bound invocation profile |
| LLM | 只产生 proposal，不自动执行 proposal 中的动作，输出结构化回执 |
| unsupported | 缺失能力逐项显式 `unsupported`，带原因，不做语义 fallback |

Core descriptor 的最小机器契约为：

```yaml
schema_version: yuan.adapter-descriptor/v1
adapter_id: manual | hermes
core_protocol_revision: yuan.core.protocol/0.1.0-candidate
status: supported | unsupported
executable_port: required-when-supported
unsupported_reason: required-when-unsupported
capabilities:
  filesystem:
    enumerate: supported | unsupported
    read_hash: supported | unsupported
    atomic_replace: supported | unsupported
    compare_and_swap: supported | unsupported
    path_containment: supported | unsupported
  command:
    bounded_execution: supported | unsupported
    timeout: supported | unsupported
    structured_receipt: supported | unsupported
    output_cap: supported | unsupported
    scope_profile: supported | unsupported
  llm:
    propose_only: supported | unsupported
    no_unmediated_side_effects: supported | unsupported
```

`manual` 是 Core 最低可移植路径，必须绑定可执行 Reference Port。
Hermes 没有 Core executable Port 时可以且应该标记 `unsupported`；Core
不得依赖 Hermes，因此这不是要求虚构平台能力。

## 首轮结果

```text
Core author regression:      30/30 PASS
M6 held-out conformance:       1/5 PASS
                               4/5 FAIL
skip / xfail:                  0
```

通过项：

- command 的 timeout、receipt、output cap、full-stream digest、scope
  profile、无 shell 执行全部通过。

失败项：

1. `M6-B01`：Reference Port 没有有界 `enumerate_files` 及每文件 hash
   的结构化 receipt。
2. `M6-B02`：`propose()` 不会自动执行返回的 file-write proposal，
   但它直接返回 provider 字典，没有 `yuan.tool-receipt/v1 /
   llm-propose / PROPOSED / operation_id`。
3. `M6-B03`：`.yuan/adapters/manual.yaml` 不存在；旧
   `.yuan/platforms/manual.md` 只是人工步骤说明，不能生成 Core
   结构化回执，也没有 executable Port binding。
4. `M6-B04`：`.yuan/adapters/hermes.yaml` 不存在；旧
   `.yuan/platforms/hermes.md` 声称 filesystem/shell 广泛支持，但
   没有可执行 Core Port。修复必须诚实声明 `unsupported`，不能把旧
   Action 文档当作 conformance。

机器证据见
[`held-out-initial.json`](./held-out-initial.json)，独立留出测试见
[`tests/adapter_conformance/test_m6_held_out.py`](../../../../../tests/adapter_conformance/test_m6_held_out.py)。

## 修复路由与复测条件

四个 Blocker 均路由 `backend-dev`。Tester 不实现 Adapter。

复测必须满足：

1. 原样 held-out 5/5 PASS；
2. Core author suite 仍全绿；
3. M1、M3、M4、M5 regression 全绿；
4. 没有修改/弱化 held-out、没有 skip/xfail、没有降低输出或超时门禁；
5. Core candidate manifest 和旧信任根重新绑定修订后的 Core 文件；
6. manual 为可执行 Reference Port mapping；
7. Hermes 若仍无 executable Port，descriptor 必须明确且逐项
   `unsupported`，Core 与 authority switch 不得依赖它。

```yaml
verdict: fail
blocking:
  - M6-B01
  - M6-B02
  - M6-B03
  - M6-B04
advisory: []
route: backend-dev
gate: M6_BLOCKED
```
