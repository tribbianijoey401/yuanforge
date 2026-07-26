# 悬而未决登记册（OPEN-DECISIONS）

> **第三记忆通道**：ADR 存"已定死的结论"，pitfalls 存"吃过的亏"，本登记册存"还没定、正悬着的决策"。三者互补，缺一不可。
> **只写不看等于没写**：每次开工把未决项自动复现到上下文最前，逐条判断能否关闭。
> **来源**：参考 MVP 专家团 open-decisions-register 规范（`architect.md` 的 Spec 即契约段已引用；`doc-engineer.md` 阶段整合已接归档钩子）。

---

## 纪律

- **触发**：出现"定不下来 / 先放一放"的任何东西（缺密钥、等下游、有歧义设计、开放问题、延后校验、有保留接受的边界）→ 立刻落条，不留在聊天里或脑子里
- **归类**：只用下列三类固定 slug，不发明新类别
- **字段**：Date / Source / Open item / Related constraints / Current leaning / Blocked by / Resolves when（缺失填 `none yet`）
- **只追加**：新条目永远追加到末尾，绝不重写/删除已有条目
- **就地关闭**：解决时把 `OPEN` 翻成 `RESOLVED` 并补 `Resolution`（决定了什么 + 为什么 + 日期），不删除
- **位置**：本文件随代码提交（项目内可见、可 diff），不进 gitignore 临时目录
- **复现**：每次任务/阶段开始，把仍 `OPEN` 的条目复现到工作上下文最前，带 `(N 未决 + M 已决)` 汇总，逐条判断能否关闭（有界、自门控、fail-open）

---

## 三类固定 slug

| slug | 含义 | 典型触发 |
|------|------|----------|
| `waiting-on-external-condition` | 受阻于本次交付之外的条件 | 缺密钥/凭据、等下游任务、等上游答复 |
| `design-decision-to-evaluate` | 有歧义、待重新评估的设计选择 | 会话存 cookie 还是 Redis、选哪个 ORM |
| `existing-design-boundary` | 有保留地接受的既有边界/局限 | v1 只单区域部署、暂不做多租户 |

---

## 登记模板

```markdown
## OPEN — <category> — <标题>
- Date: YYYY-MM-DD
- Source: <发起它的需求 / ADR 编号 / Task ID>
- Open item: <一句话说清到底什么没定/没做>
- Related constraints: <性能/合规/接口/成本>
- Current leaning: <当前倾向/临时方案，无则 none yet>
- Blocked by: <卡住决策的东西>
- Resolves when: <什么发生了这条就能定——必须可判定的具体条件>

## RESOLVED — <category> — <标题>
- Resolution: <决定了什么 + 为什么 + 日期>
```

> 一条 OPEN 被关闭后若产出稳定可复用结论，可顺手沉淀成 ADR 或事实；踩坑类则进 `knowledge/pitfalls/`。
