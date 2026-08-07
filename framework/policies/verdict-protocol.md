---
name: verdict-protocol
description: 结构化裁决协议（RoleVerdict）— 审查官统一以 verdict/blocking/advisory/evidence 输出
spec_type: rule
version: "1.0.0"
---

# 结构化裁决协议（RoleVerdict）

> **vNext Scope：** 仅由 Routing 选中的 Reviewer / Tester 加载。统一输出 `READY` 或 `NEEDS_WORK`、Finding、Evidence 与 Residual Risk；普通 Agent 不读取。

> **来源**：参考 MVP 开发专家团的 RoleVerdict 协议。
> **目的**：任何审查官 / 测试官的结论都必须以**结构化**形式呈现，便于 Conductor 自动路由（打回 Dev / 升级 Architect / 通知 Tester），而非"我觉得还行"式自由文本。
> **与 YuanForge 的衔接**：YuanForge 已有"对抗式审查 + 三档阻塞"机制，本规则在其上叠加**结构化 verdict 字段**，使 Conductor 的 `dispatch-routing.md` 能机械判定打回 / 升级。

---

## 结构化格式 / 字段

成员回传产出时，必须使用以下 Markdown 代码块格式：

```
verdict: pass | fail
blocking: [{violation, evidence, expectation}]   # fail 时必填
advisory: [{item, reason}]                        # 可选
evidence: [{artifact_ref, line, note}]            # 必填
```

| 字段 | 必填 | 含义 |
|------|------|------|
| `verdict` | 是 | pass=通过 / fail=未通过 |
| `blocking` | fail 时 | 阻断项：违反的验收标准 / 规则 + 证据 + 期望 |
| `advisory` | 可选 | 建议项：非阻断的可改进点 + 理由 |
| `evidence` | 是 | 证据：产出物引用 + 行号 + 具体说明 |

---

## 诊断式打回（fail 时）

- 必须指明「未满足哪条验收标准 / 规则 + 证据 + 期望」，而不是「去改改」。
- 示例：
```
verdict: fail
blocking:
  - violation: "AC-02 重复注册未返回 409"
    evidence: "tests/test_auth.py:42 实际返回 200"
    expectation: "POST /auth/register 邮箱已存在时应返回 409 + 错误信息"
advisory:
  - item: "密码强度校验可加强"
    reason: "当前仅长度校验"
evidence:
  - artifact_ref: "src/api/auth.py"
    line: 88
    note: "未校验 email 唯一性"
```

---

## 过度设计护栏

审查官**只标三类阻断**：
1. 正确性缺陷
2. 需求未满足
3. 契约 / 安全 / 数据完整性破坏

**不标**：风格偏好 / 未被要求的额外特性 / 为覆盖率而覆盖率。

---

## Bounded（打回-重做上限）

- 同一 Task 打回-重做最多 3 轮。
- 连续 3 轮无进展 → 升级通知 Architect / Conductor，不无限循环。

> *本规则与 iron-rules 的"循环收敛"（铁律 Ⅹ）互补：每个 exceed gate 必须收敛，RoleVerdict 的 Bounded 给出"打回次数"机械上限。*
