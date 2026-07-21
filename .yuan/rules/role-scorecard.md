# role-scorecard.md — 角色规范符合性审计

> 定位：审计 instrument，**不是规则制定处**。各 agent 的门禁/执行权限/对抗要求已在创建时（role-contract.md）固化进合约；本卡只**核查创建是否做对**。
> 用法：每 agent 在 7 原理（P-A~P-G）上 0–3 分；目标 ≥2.5/3 才合入（铁律Ⅹ 闸门）。

## 评分矩阵（种子：§一 诊断现态的 17 项 + 一.5 复审发现）

| 角色 | P-A DRY | P-B 基准 | P-C 对抗 | P-D 门禁 | P-E 非职责 | P-F 骨架 | P-G 闭环 | 均分 |
|------|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| Conductor | 1 | 2 | 1 | 2 | 0 | 1 | 1 | 1.1 |
| Product Analyst | 1 | 0 | 0 | 1 | 0 | 1 | 1 | 0.6 |
| Architect | 1 | 2 | 0 | 0 | 0 | 1 | 1 | 0.7 |
| Frontend Dev | 1 | 0 | 1 | 1 | 0 | 1 | 1 | 0.8 |
| Backend Dev | 1 | 0 | 1 | 1 | 0 | 1 | 1 | 0.8 |
| Design Reviewer | 1 | 2 | 2 | 1 | 1 | 2 | 1 | 1.4 |
| Spec Reviewer | 3 | 3 | 3 | 3 | 3 | 3 | 3 | 3.0 |  ← 金标准
| Security Auditor | 3 | 3 | 3 | 3 | 3 | 3 | 3 | 3.0 |  ← 金标准
| UX Reviewer | 3 | 3 | 3 | 3 | 3 | 3 | 3 | 3.0 |  ← 金标准
| Quality Auditor | 1 | 2 | 1 | 1 | 0 | 1 | 1 | 1.1 |
| Tester | 0 | 2 | 2 | 3 | 1 | 2 | 2 | 1.7 |
| Doc Engineer | 1 | 1 | 1 | 1 | 0 | 1 | 2 | 1.0 |
| UI Designer | 1 | 2 | 1 | 1 | 1 | 1 | 1 | 1.1 |

## 优先级（按均分从低到高改写）
Product Analyst(0.6) < Architect(0.7) < Frontend/Backend Dev(0.8)
< Doc Engineer(1.0) < Conductor(1.1) = Quality Auditor(1.1)
< UI Designer(1.1) < Design Reviewer(1.4) < Tester(1.7)
< 标杆三份(3.0，不改写)

## 审计检查点（每条核查合约「创建时」是否已声明，而非运行期才定）
- P-A DRY：共享词汇/要求引用 contract-conventions.md，未把跨 agent 内容抄进本合约；路由条目对齐共享路由表。
- P-B 基准：合约「工作依据」填了本 agent 具体的冻结基准文件。
- P-C 对抗：合约「对抗式审查」填了本 agent 具体对抗目标，且满足 ≥1 尝试要求。
- P-D 门禁：合约「门禁定义」固化了本 agent 档位 + 是否可执行 + 可判定通过谓词（无主观自检）。
- P-E 非职责：合约显式声明「执行权限 / 不负责」，边界划到层。
- P-F 骨架：符合 role-contract.md 节结构（含门禁定义段）。
- P-G 闭环：产出命名消费者 + 反馈/蒸馏通道。
