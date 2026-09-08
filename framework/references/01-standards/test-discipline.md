---<!-- Adapted from UmaDev knowledge base (MIT License). Original: knowledge/agentic-delivery/01-standards/test-discipline-for-generated-code.md -->

id: test-discipline-for-generated-code
title: 生成式代码的测试纪律（回归率作为一等指标 + 风险定向选测，商业级必读）
domain: agentic-delivery
category: 01-standards
difficulty: advanced
tags: [generated-code, test-discipline, regression-rate, impact-map, independent-test-authoring, mutation-guided, tdd-pitfall, blast-radius, 生成式代码, 测试纪律, 回归率, 影响图, 独立测试, 变异加固, 风险定向, 商业级]
quality_score: 95
last_updated: 2026-09-08
---
# 生成式代码的测试纪律（商业级必读）

> 给生成式代码套上"先写测试"这句口号，往往**适得其反**：模型会写出贴着自己实现写的同义测试，绿灯一片却放过真正的回归。把改动测好，靠的不是把 TDD 当流程喊口号，而是**定向**——先算清这次改动会波及哪些行为，再把测试火力压在**最可能被打坏的旧行为**上。
> 这份规范把"测生成式代码"从"多写点测试"升级成**可判定的纪律**：用代码↔测试影响图锁定风险面、把**回归率**和"解决率"并列为一等交付指标、让测试作者与代码作者**解耦**去偏、用**变异定向加固**逼出真正能杀掉缺陷的断言。怎么分层、怎么进 CI 门见 `testing/01-standards/test-strategy-and-layering` 与 `testing/01-standards/ci-test-gates-and-coverage`；本规范回答的是"生成式改动到底要测什么、测到什么程度才算把回归挡住"。

## 1. 为什么"无脑先写测试"会抬高回归

生成式改动有三个固有偏差，单纯喊"先写测试"不仅治不了、还会放大：

- **同义测试**：让同一个上下文既写实现又写测试，测试会复述实现的内部假设，实现错了测试也跟着错，绿灯毫无信息量。
- **只测自己改的**：模型天然只给**新增/改动**的代码配测试，而回归恰恰发生在**没被这次改动直接触碰、却共享了状态或契约**的旧行为上。
- **覆盖率幻觉**：补一堆走 happy path 的断言把覆盖率拉绿，行被执行了但关键分支的断言是空的（见 §5 变异加固）。

结论：测试的价值不取决于**数量**，取决于是否压在**这次改动的风险面**上。先定向，再写测试。

## 2. 代码↔测试影响图（先算风险面，再决定测什么）

每次会影响可执行行为的改动先回答"**这次改了什么、会波及哪些行为、哪些旧行为最可能被打坏**"，产出一张定向清单而不是泛泛补测试。纯文档、纯注释等没有可执行行为风险的修改不为了仪式制造影响图。

| 改动类型 | 风险面（最可能被打坏的旧行为） | 测试火力优先级 |
|---|---|---|
| 改公共函数/方法签名或语义 | 所有调用点、依赖其返回形状的下游 | 为受影响调用路径补/查回归断言 |
| 改共享数据模型/DTO/Schema | 序列化、持久化、跨端契约、缓存键 | 契约测试 + 往返序列化测试 |
| 改条件/边界/校验逻辑 | 边界值、错误分支、权限分支 | 边界与错误路径定向用例 |
| 改共享状态/全局配置/单例 | 并发、隔离、其它读该状态的功能 | 并发与隔离回归用例 |
| 改依赖版本/外部接口适配 | 所有经过该依赖的路径 | 集成测试 + 契约对照 |
| 纯新增、无共享面 | 仅新增行为本身 | 新增行为的 happy + 边界 + 错误 |

定向规则：**改动的 blast radius（波及半径）越大，回归火力越要往旧行为压**；波及半径靠"谁调用了我、谁和我共享状态/契约"来确定，而不是靠"我这次新增了几个函数"。

### Baseline Scope：risk-scoped，不等于 full suite

Baseline 的目的，是给“改动前”和“改动后”建立可比较的旧行为证据。**它的最小充分范围由 blast radius 决定，而不是默认全仓库。**

```text
Affected behavior / boundary
+ shared state / contract
+ blast radius
+ test cost / project policy
→ smallest sufficient regression baseline
```

- 局部 refactor：受影响模块、调用链和共享契约的现有测试先绿即可；行为不变的目标要求 baseline，但不自动要求 full suite。
- 共享 schema / public API / global state / dependency upgrade：blast radius 大，应扩大 baseline；必要时全量。
- Bug / Feature：除了目标 Red / Acceptance，还要为可能被打坏的旧行为建立 baseline；不要只测新增行为。
- Doc / mechanical / static config：若没有可执行行为风险，使用 lint / parser / build / diff / manual check，不为了“有 baseline”跑无关测试。
- Full suite：当成本合理、风险高、或项目 CI / release policy 明确要求时运行。**Full suite 是一种验证范围，不是 baseline 的定义。**

报告 `Baseline: N tests passed` 时，N 只是实际运行数量，不是质量阈值；必须避免把 focused baseline 冒充 full-suite green。若未覆盖全量，记录 scope、未覆盖范围与选择理由。

## 3. 回归率：和解决率并列的一等交付指标

只看"这次需求是否解决（解决率）"会奖励"改好一个、悄悄打坏两个"。商业级交付必须把**回归率**抬到同等地位：

- **定义**：一次改动引入的、**此前可用而现在失效**的行为占比（按本次 baseline 覆盖的受影响行为/用例计），与"解决率=本次目标达成的占比"并列上报。
- **判定**：所选 regression baseline 中出现由绿转红的旧行为 → **不算完成**，必须先消回归。一次"解决一个、回归一个"的改动是**净零甚至负收益**。
- **度量来源**：改动前对**受影响面**建立绿色 baseline，改动后重跑同一 scope；任何由绿转红的旧行为即计入回归。若风险在实现中扩大，必须同步扩大 regression scope，而不是拘泥于最初 baseline。
- **声明边界**：`regression rate = 0` 只对实际验证 scope 成立；未跑全量时不得声称“整个项目无回归”。
- **趋势**：回归结果随交付批次留痕、可审计；持续出现同类回归说明影响图没做或火力压错了面。

## 4. 独立（去偏）测试作者：测试作者 ≠ 代码作者

去掉"自己测自己"的同义偏差，让验证有独立性：

- **解耦上下文**：写实现的上下文与写/审测试的上下文分离，测试只看**需求与验收标准**、不看实现内部，避免复述实现假设。
- **从需求反推用例**：测试用例来自结构化需求与契约，而不是来自"代码现在是怎么写的"。
- **黑盒优先**：对外部行为按输入→可观测输出断言，不绑定私有实现细节，这样重构不误伤、实现错了能被抓到。
- **独立复核**：测试本身也要被一个不写该实现的视角复核"这些断言真能区分对错吗"，与 verifier / critic 解耦一脉相承。

## 5. 变异定向加固：注入你最怕的那个缺陷，逼出能杀掉它的测试

行覆盖只证明"代码被执行过"，不证明"断言真的会在缺陷出现时变红"。对**核心/高风险**逻辑做定向加固：

- **注入畏惧缺陷**：针对这段逻辑你最担心出错的具体方式（边界写成 `<` 还是 `<=`、漏一个错误分支、权限判断取反、单位/符号错），**手动制造**这个缺陷。
- **要求杀手测试**：必须存在一个测试在该缺陷注入后**变红**；若注入了缺陷而全测试仍绿，说明断言是空的——补到能杀掉为止。
- **聚焦而非全量**：这是对**关键改动面**的定向手段（每次改动针对其畏惧缺陷做），不是把全量变异测试搬进每次 PR；全量慢扫归夜间，见 `testing/01-standards/ci-test-gates-and-coverage`。
- **沉淀**：被加固挡住的缺陷类型记入项目级回归集与经验库，避免同类缺陷重现。

## 6. 接入交付流程

- **改动前**：对会影响可执行行为的 Work 先确定 blast radius，选择 smallest sufficient regression baseline；Refactor 必须先证明受影响旧行为为绿，Bug / Feature 建立目标行为验证并按风险补旧行为 baseline。Doc / mechanical Work 用匹配改动的 check，不机械跑无关 suite。
- **实现中**：实现与测试上下文解耦；测试从需求/契约反推。
- **风险扩大时**：如果实现过程中发现影响面比预期更大，立即扩大 baseline / regression scope；Baseline 不是开工时一次性冻结的测试清单。
- **加固**：对核心逻辑做变异定向加固，逼出杀手测试。
- **验收门**：目标 Acceptance 通过，且实际 regression scope 内没有由本次改动引入的绿转红，才算完成；对未覆盖范围诚实报告 Residual Risk。
- **回归保护**：每个抓到的回归与畏惧缺陷沉淀为持久用例，进自动化回归。

## 7. 反模式（出现即不合格）

1. **同一上下文自写自测**：实现与测试共享假设，绿灯零信息量。
2. **只给新增代码配测试**：放任共享契约/状态上的旧行为被悄悄打坏。
3. **用 happy-path 断言堆覆盖率**：行被执行、关键分支断言为空，覆盖率绿而缺陷漏网。
4. **把 focused baseline 冒充 full-suite green**：验证声明大于实际 Evidence。
5. **无条件先跑全量测试**：不看 blast radius、成本与任务性质，把 baseline 做成流程仪式。
6. **把"先写测试"当免罪符**：写了测试就签字，不看测试是否压在风险面上。
7. **断言绑实现细节**：贴着私有实现写，重构必红、实现错却不红。
8. **核心/高风险逻辑零定向加固**：风险很高却从不验证畏惧缺陷，无法证明断言会变红。

## 8. 最低交付 checklist

以下 checklist 同样遵循 applicability；不是每个 Work 都必须产生每一项：

- [ ] 对会影响可执行行为的改动，按 blast radius 明确受影响面与 baseline scope；纯 Doc / mechanical Work 使用匹配的 check。
- [ ] Baseline 是 smallest sufficient scope；扩大到 full suite 时有风险、成本或项目 policy 的理由。
- [ ] Bug / Feature 的目标验证与受影响旧行为 regression 都得到覆盖；Refactor 的受影响旧行为 baseline 在改动前为绿。
- [ ] Verification claim 与实际运行 scope 一致；未跑全量时不声称“全项目无回归”。
- [ ] 核心/高风险逻辑按需做定向加固；不为低风险改动机械执行 mutation ritual。
- [ ] 每个抓到的真实回归与可复用畏惧缺陷，在有长期价值时沉淀为项目级回归用例。
