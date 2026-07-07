# YuanForge 架构文档

> YuanForge 自身的架构设计。

---

## 设计理念

YuanForge 是纯规则体系（Markdown），不是代码。核心思想：

1. **平台无关** — 不绑定任何 Agent 平台
2. **语言无关** — 不绑定任何编程语言
3. **分层解耦** — 规则层 / 合约层 / 协议层 / 适配层 各司其职

---

## 分层架构

```
┌──────────────────────────────────────────┐
│ 入口层                                     │
│ ├── AGENTS.md     平台自动读取的入口         │
│ └── README.md     人类阅读的入口            │
├──────────────────────────────────────────┤
│ 规则层（.yuan/rules/）                     │
│ ├── iron-rules.md     九条铁律             │
│ ├── plan-format.md    Plan 工程化格式       │
│ └── docs-framework.md 说明书规范            │
├──────────────────────────────────────────┤
│ 角色层（.yuan/agents/ + contracts/）       │
│ ├── Architect/Coder/Reviewer/Tester/DevOps  │
│ └── Conductor（调度中枢）                   │
├──────────────────────────────────────────┤
│ 技能层（.yuan/skills/）                    │
│ ├── vibecoding-workflow 核心引擎            │
│ ├── project-bootstrap   项目初始化          │
│ ├── project-audit      项目审计            │
│ └── 6 个专项 Skill                         │
├──────────────────────────────────────────┤
│ 协议层（protocols/）                       │
│ ├── dispatch-table.md  Agent 调度协议       │
│ └── task-output.md     Task 产出格式        │
├──────────────────────────────────────────┤
│ 适配层（.yuan/platforms/）                 │
│ ├── hermes.md   Hermes 平台适配            │
│ └── manual.md   通用/人工模式              │
├──────────────────────────────────────────┤
│ 记忆层                                     │
│ ├── docs/        项目说明书（生长层）        │
│ └── .yuan/docs/  框架自身记忆              │
└──────────────────────────────────────────┘
```

---

## 数据流

```
用户需求
  ↓
AGENTS.md → Agent 加载 .yuan/rules/ → 读 docs/PROGRESS.md
  ↓
Phase 0: project-audit（审计现有项目，仅首次）
Phase 1: Architect 产出 Plan（含 Dispatch Table）
Phase 2: Conductor 解析 DAG → 派发 Coder/Reviewer
Phase 3: Tester + DevOps 收尾
Phase 4: 回顾归档 → 提炼 Skill / 改进铁律
```

---

## 目录结构

```
yuanforge/
├── AGENTS.md              入口（平台自动读取）
├── README.md               人类入口
├── docs/                   本项目说明书（生长层）
├── .yuan/                  框架内核（不可变）
│   ├── rules/              铁律 + 格式规范
│   ├── agents/             角色定义
│   ├── skills/             Skill 定义
│   ├── platforms/          平台适配器
│   ├── templates/          项目模板（复制用）
│   └── plans/              Plan 存档
├── contracts/              角色合约（短契约）
├── protocols/              Agent 间协议
└── templates/              Plan 模板
```

---

## 关键设计决策

| 决策 | 原因 |
|------|------|
| 纯 Markdown，无代码 | 最大化跨平台兼容 |
| .yuan/ 而非 .hermes/ | 平台无关命名 |
| contracts/ + agents/ 双层 | 合约是外部接口，agent 是内部实现 |
| platforms/ 适配层 | 让不同平台的能力差异透明化 |
| docs/ 生长层设计 | 项目知识随开发自然生长，不腐烂 |
