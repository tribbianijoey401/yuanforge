# task-004 Held-out Review

> 最终判决：`PASS`（两轮返工前的 Blocker 证据保留如下）
> 被测提交：`337ff581eb3754874cb1c4fcc891e96e77a8cc31`
> 独立角色：Tester（未参与 task-003 实现）
> 测试结果：11 项，8 PASS，3 FAIL，0 skip，0 xfail

## 合规路径

以下基线能力通过：

- author-visible 基线 suite 能产生结构化 PASS receipt；
- manifest、candidate、validator 内容篡改会使 suite 失败；
- validator timeout 与解析错误失败关闭；
- 缺失负类失败关闭；
- expected reason 不允许被额外故障污染；
- UTF-8 manifest、candidate 和 receipt 可往返；
- 正常 nested receipt 使用同目录临时文件并由 `os.replace` 原子落盘。

## 对抗路径与 Blocker

### M1-B01：执行命令没有绑定到 trusted validator

manifest 保持有效哈希，`trusted_files` 仍绑定仓库内的
`validators/pass_validator.py`，但 `validator.command` 被设置为
`../outside_validator.py`。当前 verifier 执行了 suite root 外的程序并返回
PASS。

这证明 `trusted_files` 当前只是装饰性声明，不能证明实际执行的程序是受信
validator。该缺陷破坏 Genesis trust root，属于 P0 Blocker。

### M1-B02：receipt 可以在成功后覆盖被验证输入

把 `--receipt` 指向 `candidates/valid/protocol.md` 后，verifier 先基于原文件
计算 PASS，再把 PASS receipt 原子替换到该 candidate 路径，最后以退出码 0
结束。

因此 receipt 所陈述的 candidate hash 与命令结束时的真实 candidate 不一致，
证据在创建瞬间即过期。receipt 目的地必须在 suite 执行前与 manifest、
candidate 树及 trusted validator 集合做不相交检查。

### M1-B03：重复 check ID 可虚增断言

受哈希绑定的 validator 输出 `assertions: 2`，但两个 check 使用相同 ID。
当前 verifier 将其计作两个独立断言并 PASS。这允许单一检查复制多次以满足
非零或未来的数量门禁，属于测试完整性缺陷。

### M1-B04：输入保护依赖 manifest 已经可信

r1 `c6d3798` 关闭前三项后，Tester 使用一个未提前告知实现者的组合攻击：
传入冻结前的正确 hash、随后篡改 manifest，并让 `--receipt` 指向一个
candidate 文件。verifier 正确返回非零，却因为 hash 不匹配时跳过 protected
input discovery，把 FAIL receipt 覆盖到了 candidate。

失败关闭不仅要求“不给 PASS”，也要求拒绝路径不破坏被验证输入。manifest
尚未建立信任或无法解析时，verifier 无法安全枚举其输入，因此至少必须机械
拒绝把 receipt 写入 manifest 所在 suite root 内。

## 反作弊裁决

- 实现与 held-out tests 分离；Tester 未修改 verifier。
- 没有删弱断言、skip、xfail、吞异常或阈值豁免。
- 3 个失败均是作者可见测试之外的攻击输入。
- visible 9/9 PASS 不能覆盖上述信任边界，故不能据此放行 M1。

## 路由

`task-003` 退回 Backend Dev。修复后必须原样运行 held-out suite；Tester 将
重新核验全部需求并生成最终 `receipt.json`。在此之前，`task-004` 保持阻塞，
`task-005` 不得晋升。

机器可读证据见 `held-out-pre-fix.json`。

## 最终关闭

- r1 `c6d3798` 关闭 M1-B01、M1-B02、M1-B03。
- r2 `f46c4e4` 关闭组合攻击 M1-B04，并把 receipt 输出隔离提前到 manifest
  信任建立之前。
- Tester 对 r2 独立运行 31 项测试：31 PASS、0 FAIL、0 skip、0 xfail。
- 最后一轮新增 junction 逃逸、suite-root 前缀相邻路径和原子写父路径异常
  三个变体，全部通过。
- 冻结 manifest 运行 14 个 checks，结构化 `receipt.json` 为 PASS。
- 用户原始 8 个 tracked dirty 与 2 个 untracked 文件哈希全部仍与 M0a 一致。

最终机器证据见 `held-out-final.json` 和 `receipt.json`。M1 Gate 可以放行。
