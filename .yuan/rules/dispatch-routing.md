# dispatch-routing.md — 跨 agent 路由表

> 路由表随 Agent 增减 / 职责微调频繁变动，属「协调规则」而非「不变词汇」。
> 本文件与 `iron-rules.md` 同层，单源、独立演进、改动不震荡内核。
> 各 agent 合约在「路由条目」段声明自己提出的类型与去向，须与此表一致。

## 列 schema

| 列 | 说明 |
|----|------|
| 触发源 | 哪个 agent 提出路由请求 |
| 失败/打回类型 | Blocker / Hard Gate / Advisory |
| 路由目标 | 回退给谁 |
| 触发条件 | 何时触发此路由 |

## 路由表

| 触发源 | 失败/打回类型 | 路由目标 | 触发条件 |
|--------|--------------|----------|----------|
| Tester | 仅逻辑错误（单元/局部） | 回对应 Dev | 不触及 API 契约、数据模型、跨模块接口 |
| Tester | 涉接口/契约 | 回 Architect + 相关审查官 | 失败指向契约不一致、seam 断点 |
| Tester | 涉外部依赖（第三方/基础设施） | 回 Architect + Spec Reviewer + Quality Auditor | 由依赖版本/配置/环境导致 |
| Spec Reviewer | Blocker | 回 Product Analyst（需求/AC 缺陷）或 Dev（实现不符 AC） | 按偏离根因判定 |
| Design Reviewer | Blocker | 回 Architect（设计缺陷，最多 2 轮） | 设计态缺陷 |
| Security Auditor | Blocker | 回 Dev（实现态）/ Architect（设计态未声明） | 按实现/设计归属 |
| Quality / UX | Advisory | 回 Dev（可豁免，≥3 升级） | 同类累计阈值 |
