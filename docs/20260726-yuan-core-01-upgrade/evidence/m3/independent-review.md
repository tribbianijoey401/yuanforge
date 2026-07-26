# task-006 M3 Independent Core Review

> 被测提交：`3df925011ac6d99f62b728ab4b6624d24cf2c6d0`
> 独立角色：Tester（未参与 task-005 实现）
> 判决：`PASS — M3_APPROVED`
> held-out：30 checks，30 PASS，0 FAIL，0 skip，0 xfail
> 旧 bootstrap：M1 regression 31/31 PASS；M3 suite 75 checks，7/7 cases matched

```yaml
verdict: pass
blocking: []
advisory: []
evidence:
  - artifact_ref: "docs/20260726-yuan-core-01-upgrade/evidence/m3/held-out-result.json"
    line: 1
    note: "独立 30-check PASS；含 16 组固定种子 protected-scope / previous-root mismatch 纯数据变体"
  - artifact_ref: "docs/20260726-yuan-core-01-upgrade/evidence/m3/bootstrap-receipt.json"
    line: 1
    note: "冻结 M1 verifier 对新 manifest 重绑定 candidate 的 75-check PASS receipt"
  - artifact_ref: "tests/core_01/held_out_validator.py"
    line: 1
    note: "独立 held-out；未修改 Core/M1 verifier，无网络与外部系统副作用"
```

## r1 历史裁决（M3-B06 已由 r2 关闭）

- r1 原 28 项已通过，但新增
  `rebuild-selfmod-revision-and-port-scope-consistent` 发现：
  replay 未强制 self-mod proof，且 BLOCKED scope 被写成 `.`。
- r2 把 self-mod record 纳入 Attempt schema，在 replay 中核对 protected target、
  candidate receipt hash 与 previous/independent/human proof，并按
  Evidence → Attempt → Work 保留 artifact scope。
- 原检查与 16 组随机变体全部通过，M3-B06 关闭。

## 首轮历史裁决（M3-B01–B05 已由 r1 关闭）

```yaml
verdict: fail
blocking:
  - violation: "M3-B01 — AC-03/AC-04 与 Mandatory Semantics 2–4：COMPLETE 接受未绑定、过期或不可验证的 Evidence"
    evidence: "held-out-result.json 中 evidence-must-bind-current-work-revision、evidence-must-bind-work-harness-revision、evidence-must-bind-current-environment-fingerprint、expired-evidence-fails-closed、evidence-immutable-digest-is-verified 均 FAIL；conformance.py::_valid_evidence_for_ac 只比较 AC/verifier/artifact/environment id 的子集"
    expectation: "Evidence 必须匹配当前 Work revision、Work/Harness binding、环境 id+fingerprint；not_after 必须按可信时钟失败关闭；immutable_digest 必须按冻结 canonicalization 复算"
  - violation: "M3-B02 — AC-06 与 Mandatory Semantics 8：Attempt journal 可伪造副作用成功"
    evidence: "held-out-result.json 中 committed-side-effect-requires-bound-receipt、unknown-side-effect-cannot-succeed、mutating-action-type-cannot-claim-non-mutating 均 FAIL；attempt.schema.yaml 允许 tool_receipt=null 与 outcome=SUCCEEDED 独立组合"
    expectation: "OBSERVED/COMMITTED 必须绑定有效 receipt 与 postcondition；UNKNOWN 只能映射 UNKNOWN/阻塞；file-write 等变更动作不能声明 non-mutating"
  - violation: "M3-B03 — AC-05：Run Memory 只有重建文档，没有确定性 replay/rebuild 实现"
    evidence: "held-out-result.json 的 run-memory-has-deterministic-rebuild FAIL；protocol.md §9 描述重建，但 candidate 没有可调用 reducer/replay"
    expectation: "从不可变 Work、按序 Attempt、Evidence 重建投影；缺失历史、digest 不符、顺序歧义和非法 transition 必须 BLOCKED，不能重建 COMPLETE"
  - violation: "M3-B04 — Mandatory Semantics 7：自修改旧信任根仅为说明文字"
    evidence: "held-out-result.json 的 self-modification-has-old-root-enforcer FAIL；protocol.md §11 有规则但 candidate 无机械 authorizer"
    expectation: "authority/Core/Harness/validator 修改必须由 previous root、独立 held-out root 或命名 revision+risk 的人工授权之一机械证明"
  - violation: "M3-B05 — scope/auth 边界可绕过"
    evidence: "held-out-result.json 的 expired-grant-waits-for-authorization 与 command-arguments-cannot-escape-work-scope FAIL；authorization_status 不读取 expires_at；ReferencePort 允许受信 Python 通过 -c 与绝对 argv 写出 Port root"
    expectation: "过期 grant 返回 WAIT_AUTH；命令必须绑定允许的 invocation/profile 或在可证明的 scope sandbox 内执行，不能只信任 argv[0]"
advisory: []
evidence:
  - artifact_ref: "docs/20260726-yuan-core-01-upgrade/evidence/m3/held-out-result.json"
    line: 1
    note: "独立 28-check 语义、失败、卡死、副作用与自修改攻击明细"
  - artifact_ref: "docs/20260726-yuan-core-01-upgrade/evidence/m3/bootstrap-receipt.json"
    line: 1
    note: "冻结 M1 verifier 对内容寻址 Core candidate 的 64-check FAIL receipt"
  - artifact_ref: "tests/core_01/held_out_validator.py"
    line: 1
    note: "task-005 作者未见的独立 held-out verifier"
```

## 信任链核验

1. `scripts/bootstrap-core-verifier.py`、`bootstrap_verifier.py`、
   `bootstrap_verifier_support.py` 的 SHA-256 分别仍等于 M1 冻结值。
2. M1 author-visible manifest 仍为
   `66f20b3a04050135468209e6ead66f3df258f2faff8dbeb8f76a50c635ad8e55`。
3. M1 visible + held-out regression 为 31/31 PASS，0 skip。
4. 外层 M3 manifest 已由独立 Tester 重绑定 task-005 r2 candidate manifest
   `c3d41ac1a056523ad5af4a430e09185f7ab1e732507097ba7546be7f512d72e3`、
   其全部 29 个声明文件、candidate manifest 自身以及独立 validator。
5. 旧 verifier 对正常/empty/known-bad/zero/error/parse 六个 Genesis cases
   及 `yuan-core-01-candidate` 全部匹配；Core case `ACCEPT`，candidate 自检
   没有作为独立 Gate 的唯一证据。

## 场景覆盖

| 场景 | 结果 |
|------|------|
| 正常 | baseline completion、授权、CAS、bounded output PASS |
| 首轮 Blocker | M3-B01–B05 的原 12 个失败全部 PASS |
| 失败关闭 | zero assertions、stale artifact、self-attestation、path escape PASS |
| 卡死 | command timeout 在 1 秒内返回 `TIMED_OUT` receipt，PASS |
| 副作用崩溃 | `UNKNOWN + SUCCEEDED` 已失败关闭，PASS |
| 自修改/rebuild | enforcer 已接入 replay；无 proof、错误 protected kind、错误 previous root 全部 BLOCKED |
| scope 投影 | COMPLETE/BLOCKED 均保留当前 artifact/Port scope，PASS |
| 随机变体 | 固定种子 16 组 protected scope / previous-root mismatch 全部 BLOCKED |

## 路由

- `task-005` r2 接受；M3-B01–M3-B06 全部关闭。
- `task-006` 完成，M3 Hard Gate PASS。
- `task-007` 可晋升执行 M4 Shadow conversion 与回退演练。
