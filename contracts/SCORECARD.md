# SCORECARD.md — 角色对齐评分卡

> 用法：每角色在 7 原理（P-A~P-G）上 0–3 分。
> 3=落地可操作 / 2=部分 / 1=提及无机制 / 0=缺失。
> 改写后复打，目标 ≥2.5/3 才合入（铁律Ⅹ 闸门）。

## 评分矩阵（种子：§1 诊断的 17 项发现）

| 角色 | P-A DRY | P-B 基准 | P-C 对抗 | P-D 门禁 | P-E 非职责 | P-F 骨架 | P-G 闭环 | 均分 |
|------|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| Conductor | 1 | 2 | 1 | 2 | 0 | 1 | 1 | 1.1 |
| Product Analyst | 1 | 0 | 0 | 1 | 0 | 1 | 1 | 0.6 |
| Architect | 1 | 2 | 0 | 0 | 0 | 1 | 1 | 0.7 |
| Frontend Dev | 1 | 0 | 0 | 1 | 0 | 1 | 1 | 0.6 |
| Backend Dev | 1 | 0 | 0 | 1 | 0 | 1 | 1 | 0.6 |
| Design Reviewer | 1 | 2 | 2 | 1 | 1 | 2 | 1 | 1.4 |
| Spec Reviewer | 3 | 3 | 3 | 3 | 3 | 3 | 3 | 3.0 |  ← 金标准
| Security Auditor | 3 | 3 | 3 | 3 | 3 | 3 | 3 | 3.0 |  ← 金标准
| UX Reviewer | 3 | 3 | 3 | 3 | 3 | 3 | 3 | 3.0 |  ← 金标准
| Quality Auditor | 1 | 2 | 1 | 1 | 0 | 1 | 1 | 1.1 |
| Tester | 0 | 2 | 2 | 3 | 1 | 2 | 2 | 1.7 |
| Doc Engineer | 1 | 1 | 1 | 1 | 0 | 1 | 2 | 1.0 |
| UI Designer | 1 | 2 | 1 | 1 | 1 | 1 | 1 | 1.1 |

## 优先级（按均分从低到高改写）

Product Analyst(0.6) = Frontend/Backend Dev(0.6) < Architect(0.7)
< Doc Engineer(1.0) < Conductor(1.1) = Quality Auditor(1.1)
< UI Designer(1.1) < Design Reviewer(1.4) < Tester(1.7)
< 标杆三份(3.0，不改写)

## 评分说明（每条原理对应检查点）

- P-A DRY：共享机制是否引用 _shared.md 而非重抄（路由表/防御指令/对抗模板）。
- P-B 基准：是否有上游已冻结产出物作唯一度量尺（如 AC / API 契约 / V-M-D 旋钮）。
- P-C 对抗：是否含对抗式审查段且硬要求 ≥1 尝试。
- P-D 门禁：每个「完成」是否可判定布尔谓词（禁「深度模块」式主观自检）。
- P-E 非职责：是否显式声明「不负责什么」并划到具体层。
- P-F 骨架：是否符合 TEMPLATE.md 节结构。
- P-G 闭环：产出是否命名消费者 + 反馈/蒸馏通道。
