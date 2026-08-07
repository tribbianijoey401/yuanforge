# References Index

本目录为 Skill 提供工程纪律、Architecture Pattern、Platform、Cost Model 和 Design System 等专业基线。References 是被动知识源，只在 Skill 的 `Reference Routing` 命中 Retrieval Signal 时读取相关 Section；Agent 和 Conductor 不直接加载本目录。

## 目录结构

```
references/
├── README.md                    # 本索引文件
├── 01-standards/                # 工程纪律标准（UmaDev 融合 — 11 篇商业级必读）
│   ├── spec-as-contract.md             # 规格即契约 8 要素
│   ├── eval-driven-delivery.md         # 评测驱动交付
│   ├── verifier-critic-pattern.md      # 验证者/评审者模式
│   ├── test-discipline.md              # 生成式代码测试纪律
│   ├── test-integrity-anti-gaming.md   # 测试完整性反作弊
│   ├── generated-code-failure-modes.md # 生成式代码失效模式（6 类）
│   ├── production-readiness-scorecard.md # 生产就绪记分卡（7×3 矩阵）
│   ├── self-improving-memory.md        # 自学习记忆与回归集
│   ├── open-decisions-register.md      # 悬而未决登记册
│   ├── context-engineering.md          # 上下文工程
│   ├── code-organization.md            # 代码组织规范（分层·分包·不堆单文件）
│   ├── framework-failure-modes.md      # Yuan 历史 Anti-pattern 与防回归方法
│   └── mvp-expert-team-benchmark.md    # 专家团能力对标与已吸收实践
├── industries/                  # 行业设计规范
│   ├── saas-b2b.md             # SaaS / B2B 工具
│   ├── ecommerce.md            # 电商 / 消费
│   ├── content-platform.md     # 内容 / 社区平台
│   ├── ai-native.md            # AI 原生产品
│   └── enterprise.md           # 企业管理 / ERP
├── platforms/                   # 平台开发规范
│   ├── wechat-miniprogram.md   # 微信小程序
│   └── harmonyos.md            # 鸿蒙 HarmonyOS NEXT
├── architecture/                # 架构模式参考
│   ├── mvp-stack.md            # MVP 技术选型矩阵
│   ├── rag-knowledge-base.md   # RAG / 企业知识库
│   ├── multi-tenant-saas.md    # 多租户 SaaS
│   └── ai-agent-patterns.md    # AI Agent 工程化模式
├── cost-models/                 # 成本模型
│   └── development-costs.md    # 开发成本参考
└── design-systems/              # 设计系统参考（7 篇商业级）
    ├── token-standard.md            # 四层 Token + DESIGN.md 9节 + Master+Overrides
    ├── design-commands.md           # 设计动作命令库（23 命令 + 寄存器 + 平台轴 + denylist）
    ├── ui-styles-library.md         # UI 风格库（40 套 + 决策树）
    ├── industry-design-systems.md   # 行业推荐（30 行业推理规则）
    ├── color-palettes.md            # 配色库（30 套 × 17 语义色 + Tailwind）
    ├── typography-pairings.md       # 字体配对（25 套 + Google Fonts）
    └── landing-patterns.md          # 落地页模式（24 种 + section 顺序）
```

## vNext 引用机制：Skill → References

Agent 不直接读取本目录。Agent 只加载 Routing 分配的 Skill，Skill 根据 Work Signal 读取下表中相关 Reference Section。

| Skill | Candidate References | Retrieval Signal |
|---|---|---|
| `grilling` | `spec-as-contract`、`open-decisions-register`、匹配的 `industries/` | Scope / Acceptance 不完整、存在未决 Product Choice、Industry 已明确 |
| `writing-plans` | `spec-as-contract`、`open-decisions-register`、`context-engineering`、`code-organization` | Complex Plan、Interface / Module Boundary、未决 Design |
| `knowledge-injection` | 本 Index 与任意匹配 Reference | Agent 需要历史之外的专业基线时，作为通用 JIT Router |
| `test-driven-development` | `test-discipline`、`test-integrity-anti-gaming`、`generated-code-failure-modes`、`verifier-critic-pattern` | Behavior Change、Regression、Test Modification、Generated Code Risk |
| `systematic-debugging` | `generated-code-failure-modes`、`test-discipline`、`self-improving-memory`、`context-engineering` | Complex Bug、重复失败、Context Loss、需要长期 Regression |
| `requesting-code-review` | `verifier-critic-pattern`、`test-integrity-anti-gaming`、`production-readiness-scorecard` | Material Review、Test Change、Production Acceptance |
| `project-audit` | `code-organization`、`generated-code-failure-modes`、`production-readiness-scorecard` | Existing Project Audit 与对应 Risk Dimension |
| `project-bootstrap` | `mvp-stack`、`code-organization`、匹配的 `platforms/` | New Project Stack、Module Boundary、特定 Platform |
| `query-ux-pro-max` | Skill 内 CSV、`design-systems/`、匹配的 `industries/` | UI、Design System、Industry Experience |
| `project-memory` / `distill-workspace` / `promotion` | `self-improving-memory`、`context-engineering` | Session Recovery、Memory Distillation、Knowledge Promotion |
| `subagent-driven-development` | `context-engineering`、`verifier-critic-pattern` | Context Isolation 与 Independent Review |
| `ptg-runner` | `test-integrity-anti-gaming`、`eval-driven-delivery` | Work 明确标记 PTG-critical 或 Eval Gate |

## 使用规则

1. Conductor 只选择 Agent，不读取 Reference。
2. Agent 只加载自己 Contract 声明的 Skill。
3. Skill 先判断 Retrieval Signal，再读取匹配 Reference 的相关 Section，不默认读取全文。
4. 未命中 Signal 的 Reference 不进入当前 Context。
5. Reference 是专业基线；涉及最新 Version、Price、Law、Platform Rule 时仍需使用可信最新来源验证。

## 01-standards/ 文件来源

`01-standards/` 下 11 篇文档中，10 篇改编自 [UmaDev](https://github.com/umacloud/umadev) 知识库（MIT License，原文件位于 `knowledge/agentic-delivery/01-standards/`，每篇顶部有来源标注），`code-organization.md` 为本专家团自有的代码组织规范（分层·分包·单文件≤300行·单一职责）。
