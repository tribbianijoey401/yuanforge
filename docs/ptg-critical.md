# Framework PTG Critical Modules

> 框架本身的关键模块，任何修改必须通过物理测试门控验证。
> Tester 在执行内核 Goal 时读取此清单。

## 格式
每行一个模块/路径，可选注释。

## 模块清单

### 协议层
yuanforge-init          # 初始化脚本 — 必须验证能正确创建骨架 + 同步
.yuan/specs/runtime-protocol.md  # Runtime Protocol — 状态转换错误会导致 Loop 失能
.yuan/specs/workflow-protocol.md  # Workflow Protocol — Gate 逻辑在此
.yuan/specs/state-protocol.md  # State Protocol — Task/Workspace 状态机定义

### 规则层
.yuan/rules/iron-rules.md  # 铁律文件 — 锚点断裂会导致 Agent 加载失败
.yuan/rules/seam-agreement.md  # Seam Agreement 模板 — 字段变更影响 CAL 解析

### 合约层（框架自身运行时验证）
contracts/tester.md  # Tester 合约 — 包含 PTG/CAL/Anti-patterns 验证步骤
contracts/quality-auditor.md  # Quality Auditor — 含 Advisory 升级规则

### 脚本层
scripts/ptg-cal-gen.py  # CAL 断言生成器 — 解析错误导致契约断裂逃逸
.yuan/skills/ptg-runner.md  # PTG Runner Skill — 框架标准执行能力

## 说明

框架修改的 PTG 验证不同于产品代码：
- 不需要内存数据库，因为框架操作的是 Markdown 文件和 Python 脚本
- PTG 的核心是"变更后的框架仍能正常驱动 Conductor Loop"
- 每次内核变更跑 `ptg-cal-gen.py` 验证 schema 完整性 + `framework-self-test` 验证结构一致性
- 真正的 L1 集成测试 = 用新框架在一个临时项目中完整跑一个 Goal
