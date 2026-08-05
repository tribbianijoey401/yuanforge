# Yuan 运行时开销盘点（Cost Audit）

> 实测环境：Python 3.11.15 / Yuan harness 0.8.1 / vibe-coding profile
> 实测日期：2026-08-05 · 测试项目：`/tmp/yuan-cost-test`（全新安装）
> 测试任务：**在 README.md 末尾追加一行文字**（最小 R0 文档需求）

---

## 一句话结论

**一个 <100 token 的真实任务，框架要注入 ≈ 32–50K token 的仪式上下文、跑 22 条 kernel 命令、要求 8 个角色全部 handoff，才能让 Reducer 判定 COMPLETE。** 仪式成本与任务成本完全脱钩，这就是"运行时间比 agent 平台流程还长"的根源。

---

## 第一层：静态上下文税（每次对话开场固定开销）

| 项目 | 字节 | 说明 |
|---|---|---|
| AGENTS.md bootstrap block | 8,964 B | 每次会话注入 |
| `.yuan/protocol.md` 全文 | 8,817 B | bootstrap 要求"读取" |
| `status` 输出 | 601 B | 开场必跑 |
| `capability list` 输出 | **10,314 B** | 开场必跑，最大单项 |
| `memory resume` 输出 | 101 B | 开场必跑 |
| **小计（JSON+md，未含引用文件）** | **≈ 28.8 KB** | ≈ 9–10K token |

`capability route --risk R0` 之后，bootstrap 要求 agent 逐个读取引用文件：

| 引用 | 字节 |
|---|---|
| rules（8 个全量） | 6,996 B |
| agents（8 个） | 5,681 B |
| skills（8 个） | 8,616 B |
| **小计** | **≈ 21.3 KB** | ≈ 7K token |

**开场固定税合计 ≈ 50 KB ≈ 16–17K token**——此时任务还没开始。

---

## 第二层：单命令 JSON 体积

| 命令 | 输出字节 |
|---|---|
| status | 601 |
| capability list | 10,314 |
| capability route R0 | 7,433–8,227 |
| capability route R1 | 5,669 |
| capability route R2 | 5,308 |
| intake template | 329 |
| intake confirm | 610 |
| work template | 3,234 |
| work accept | 4,350 |
| attempt begin | 1,529 |
| attempt observe | 1,523 |
| verify | 2,354 |
| reduce | 736 |

route 返回的是元数据（path+digest）而非正文，但**引用文件必须全部读进上下文**，实际成本见第一层。`capability list` 单条 10KB 是最大信封。

---

## 第三层：最小任务全链路（README 加一行）

**22 条 kernel 命令，JSON 输出合计 49,282 B（≈16K token），纯子进程 wall time 5.2s**（不含 LLM 每步推理——实际 LLM 轮次 ≥22，每轮都要重读上下文）。

```
status → capability list → memory resume
→ intake template → seal → check → confirm
→ capability route
→ work template → seal → bind-verifier → seal → confirm → accept
→ attempt template → begin → dispatch → observe
→ verify
→ handoff × N（每个角色 template+seal+record = 3 条）
→ reduce → memory checkpoint
```

**最致命的发现**：`reduce` 的未满足原因明确列出——

> 未完成或已过期的 Role Handoff：**architect, design-reviewer, documentation-engineer, memory-curator, quality-auditor, spec-reviewer, security-auditor, tester**

**给 README 加一行字，需要 8 个角色全部完成 handoff 才能 COMPLETE。** 每个 handoff = 3 条命令 + 需引用 Evidence。这就是开销爆炸的核心。

---

## Top 3 最肥开销点（按 token×频率）

1. **R0 也强制 8 角色 handoff** — 风险分级形同虚设，R0 收全价仪式。占全链路开销大头。
2. **开场固定税 ≈16K token** — protocol 全文 + capability list 10KB + 8 rules/8 agents/8 skills 引用文件，与任务大小无关。
3. **每命令全量 JSON 信封** — digest/id/schema_version/echo 字段反复进上下文，单 `capability list` 就 10KB。

---

## 附带发现：harness 接口自身的摩擦成本

这些是"框架分身能力弱、反复执行失败"的直接来源——LLM 必须用上下文去试错补齐接口缺口，每次失败都在烧 token：

1. `work template` 默认 grant scope = `["src","tests"]`，改 README 不在范围 → mutating 动作直接 `WAIT_AUTH`，agent 得自己悟出要改 `scopes`。
2. `seal` 输出是**完整记录**必须整体回写，bootstrap 未说明。
3. `bind-verifier` 的输入是 **work 文件**，但 bootstrap 表述为"先写 verifier 再 bind"，易误解。
4. 参数风格不一致：`attempt begin` 收文件路径，`dispatch/observe` 收 `--attempt id`。
5. Artifact Reviewer 的 READY handoff 必须引用**当前 Evidence**，否则 BLOCKED。

---

## 瘦身方向（对应 A–D，零新概念）

- **A. 按风险分级收费**：R0 跳过 intake 双确认与 8 角色 handoff，一条轻量 checkpoint 直接干活；R1 单步 attempt；R2 保留完整仪式。
- **B. Kernel 输出增量化**：所有命令加 brief 模式，上下文只回「决定 + delta + 下一步」，完整 JSON 落盘 `.yuan-run/`。
- **C. 检查移出会话**：integrity/conformance 改后台/update 时跑，不在会话内同步阻塞。
- **D. 事实恢复缓存**：protocol.md 不逐会话重读（bootstrap 已编码要点）；status 带文件指纹缓存。

**预期收益**：R0 类任务上下文从 ≈50K token 降到 ≈3–5K token，kernel 命令从 22 条降到 ≤5 条。
