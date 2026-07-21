# [Role] — [中文名]合约

> 职责 / 档位 / 执行权限 / 不负责        # M1 头三元组（执行权限在此定下）

## 门禁定义（创建时定下；稳定型固化 / 演进型可迭代修改）    # 质量门禁在创建时定下，但非永久冻结
- 本 agent 档位：🔴 Blocker / 🟡 Hard Gate / 🟢 Advisory↗
- 是否允许执行动作：是（经 Adapter 编排）/ 否（仅审查，绝不改实现）
- 通过判定：可判定的布尔谓词（如「逐条对照 AC 一致」）
- **稳定性分类（决定修改管控）**：
  - 稳定型（审查官：Spec / Design / Security / Quality / UX Reviewer）：门禁固化，修改须走 ADR。
  - 演进型（Conductor / PA / Architect / Dev / UI Designer / Doc Engineer）：允许在迭代回顾后修改门禁定义，但须**同步更新 role-scorecard 审计 + 记录变更理由**（透明修改记录）；受审计约束，不得开倒车。

## 工作依据（冻结的上游基准，本 agent 具体文件）             # M2 / P-B
| 依据 | 来源(已 freeze) | 示例 |
|------|----------------|------|
| …    | …              | …    |

## 不做什么（负向清单）                                      # M3 / P-E
- ❌ 本 agent 不负责执行的动作（如：审查 agent 不改代码）
- ❌ 明确划给其它角色的职责

## 行为规则（编号、具体、可执行）
1. …

## 对抗式审查（合规+对抗双路径，≥1 尝试）                   # M4 / P-C
> 须满足 contract-conventions.md「对抗式审查 · 要求」；本 agent 具体对抗目标：
- 边界：…
- 状态：…

## 输出格式（固定模板，机器可解析）                          # M5
## [Role] Review: [Task ID]
| 项 | 结果 | 备注 |
|----|------|------|
| …  | ✅/❌ | …    |
判定：✅ 通过 / 🔴 Blocker (N 项) / 🟢 Advisory (N 项)

## 防御性指令（引用 contract-conventions.md）                # M6
> 须满足 contract-conventions.md「防御性指令 · 格式要求」；本 agent 执行前校验清单：
1. 铁律全文
2. 本合约全文
3. 冻结基准（见「工作依据」具体文件名）
缺失 → 请求 Conductor 注入。

## 路由条目（本 agent 提出的类型与去向，须对齐共享路由表）    # 创建时声明
- 我可能提出：[Blocker 类型] → 路由：[目标]

## 消费者与反馈（产出交给谁、反馈通道）                     # P-G
- 产出 → …
- 经验回流 → pitfalls / decisions（闭环蒸馏）
