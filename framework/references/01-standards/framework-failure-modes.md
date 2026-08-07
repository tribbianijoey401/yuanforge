# 反模式清单（Anti-Patterns）

> **维护者**：框架维护者 | **审计者**：Tester（内核 Goal 审查时强制匹配）

本项目（YuanForge 框架自身）记录的已知破坏性场景。Tester 在执行对抗式审查时必须逐一验证，覆盖率 100%。

## 格式

    ### AP-<CATEGORY>-<NNN>: <标题>
    
    - **描述**: 发生了什么、为什么坏
    - **重现条件**: 触发此反模式的上下文
    - **修复方式**: 当时采用的修复方案
    - **验证方式**: 如何确保不再复发
    - **@ptg**: true/false — 标记是否在 PTG 中自动化验证（推荐全部为 true）

## 分类代码

| 前缀 | 类别 |
|------|------|
| SCHEMA | 数据库/Schema 偏离 |
| ENV | 环境不一致 |
| MIGRATE | 迁移缺失/错误 |
| CONCURRENT | 时序/并发问题 |
| RESOURCE | 资源边界/性能 |
| CONTRACT | 契约断裂 |
| FRAMEWORK | 框架内核变更引入的回归 |

## 条目

### AP-CONTRACT-001: 合约缺门禁定义段

- **描述**: Arch Agent 产出合约文件时只写职责和规则，但遗漏 `## 门禁定义` 段落。导致 Role-Scorecard P-D 评分无法判定，Gate 机制失效。
- **重现条件**: 创建新角色合约时，仅参照旧合约的 `工作依据/产出/行为规则` 部分，忽略了模板中的门禁定义段。
- **修复方式**: 在 contract-conventions.md 中声明硬性段要求，conductor 派发 Architect 时注入模板链接。
- **验证方式**: `pre-commit` 脚本扫描 agents/*.md 是否包含 `## 门禁定义` 标题；Role-Scorecard P-D 检查扣 0.5 分。
- **@ptg**: true

### AP-FRAMEWORK-002: 铁律注释锚点与实际内容不匹配

- **描述**: `policies/iron-rules.md` 中 `<SECTION-END:N>` 标记或铁律编号（Ⅰ→Ⅻ）与实际标题不对应。Conductor 注入铁律摘要时跳过错误或注入错误的段落。
- **重现条件**: 新增/删除铁律时忘记更新锚点编号或 `<SECTION-END>` 标签。
- **修复方式**: `yuanforge-self-test` Skill 执行锚点闭合检查。
- **验证方式**: 脚本提取所有 `### 铁律` 标题数与 Section-End 数量对比，不等则 Fail。
- **@ptg**: true

### AP-SCHEMA-003: 42703 — 持久化状态与模型不一致

- **描述**: 数据库表结构变更后（加列/改类型/删字段），API schema 和 seam-agreement 未同步更新。运行时访问已不存在的列或在 mock 测试中看似正常，上线后因列不存在而 42703。
- **重现条件**: Dev 修改 DB migration → 修改 Model → 但未在 seam-agreement.md 中更新对应字段 → Tester 跑的是 mock 而非真实 DB。
- **修复方式**: 引入 CAL（合同断言层），seam-agreement.md 字段定义带 @ptg 注解 → ptg-cal-gen.py 生成 pytest 断言 → PTG 环境执行。
- **验证方式**: PTG 运行真实 DB + CAL 断言。表结构与 seam-agreement 字段不匹配时阻塞合并。
- **@ptg**: true

### AP-FRAMEWORK-004: Seam Agreement 模板缺失结构化注解格式

- **描述**: seam-agreement.md 仅有空白字段列表（"命名规范:"后面无内容），没有约定数据结构化的方式，导致开发者自由发挥、不同项目格式完全不同。后续任何自动化工具（CAL）都无法解析。
- **重现条件**: 首次使用 seam-agreement.md 时没有明确的结构约定，开发者填得随意。
- **修复方式**: 在模板中追加 §6 @ptg 字段注解章节，定义统一格式。
- **验证方式**: ptg-cal-gen.py 解析 seam-agreement.md 必须能输出非空断言；Role-Scorecard P-B 检查扣 0.3 分。
- **@ptg**: true

### AP-FRAMEWORK-005: 框架目录变更后 init 脚本未同步配置常量

- **描述**: 修改框架目录结构后（如新增/重命名/删除目录），init 脚本中的 `FRAMEWORK_SUBDIRS` / `FRAMEWORK_TOP_DIRS` / `KNOWN_STALE_PATHS` / `PROTECTED_DIRS` 未同步更新。结果增量同步时遗漏新文件或污染了用户文件。
- **重现条件**: 框架结构调整但未更新配置常量 → `--sync` 时漏复制或误覆盖。
- **修复方式**: 框架结构调整后，先跑 `--sync --dry-run` 验证新旧项目对比，再实际同步。
- **验证方式**: 对临时项目执行 `--sync` 并验证 `git diff --stat` 含预期变更。
- **@ptg**: false  — 框架结构变更属于纯文本操作，不涉及真实环境，无法通过 PTG 自动化验证。可通过 self-test 的引用完整性检查间接覆盖。

### AP-CONCURRENT-006: 合约结构不一致导致模板渲染失败

- **描述**: 13 个合约有 10 种结构（v2.6 审计发现，v3.0 仍未统一）。Architect 参照旧合约模板创建新合约时，结构差异导致 Conductor 解析失败或 Key Auditor 无法标准化检查。
- **重现条件**: 新角色合约创建时未引用 role-contract.md 模板结构。
- **修复方式**: 以 TEMPLATE.md 为权威结构，所有合约引用而非重抄。
- **验证方式**: Role-Scorecard P-F 骨架检查 + pre-commit 脚本验证。
- **@ptg**: false  — 这是文档结构性问题，通过 self-test 和 Scorecard 覆盖即可。

### AP-MIGRATE-007: 框架版本同步时 VERSION 文件漂移

- **描述**: 多个位置声明框架版本号（`.yuan/VERSION`、SKILL.md frontmatter、init 脚本常量），不同步导致 `--sync` 报告"无需更新"但实际上内核已有变化。
- **重现条件**: 修改版本时只更新了某一个位置的版本号。
- **修复方式**: 统一以 `.yuan/VERSION` 为唯一真相源，init 脚本中同步更新。
- **验证方式**: SKILL.md frontmatter version == `cat .yuan/VERSION` == `FRAMEWORK_VERSION` 变量值。
- **@ptg**: false

### AP-ENV-008: Agent 启动 Checklist 缺少 PTG/CAL 项

- **描述**: Agent 进入新会话时读 checklist，但 checklist 不包含 PTG/CAL 相关文件（ptg-critical.md, anti-patterns.md），导致 Agent 可能遗漏关键验证步骤直接开始开发。
- **重现条件**: 更新 Agent Checklist 时未同步更新到 PTG 相关文件的引用。
- **修复方式**: AGENTS.md Checklist 第 5-8 条后追加 PTG/CAL 相关文件的读取要求。
- **验证方式**: 检查 AGENTS.md 的 Agent 启动 Checklist 是否包含 `policies/role-scorecard.md` 等新增引用。
- **@ptg**: false
