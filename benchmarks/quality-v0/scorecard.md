# Quality v0 Scorecard

| Dimension | Score 1 | Score 3 | Score 5 | Evidence required |
|---|---|---|---|---|
| Correctness | 关键行为或边界错误 | 主路径正确但有未处理边界 | Acceptance 与关键边界均正确 | tests、diff、manual observation |
| Architecture Fit | 破坏已观察的边界 | 基本兼容但有无解释偏移 | 复用现有模式并保持边界 | context evidence、diff |
| Code Quality | 职责混乱或重复 | 可读但抽象浅 / 复杂 | 职责清楚、复杂度与抽象有证据支撑 | diff review |
| Stack Correctness | 使用不存在或版本不符 API | 语义未证实 | API / 生命周期 / 错误语义按真实版本使用 | manifest、types、tests |
| Robustness | 错误 / 状态 / 资源边界缺失 | 覆盖常见错误 | Task-relevant risks 有防线和验证 | tests、review |
| Overengineering Control | 无理由新增层 / runtime / abstraction | 少量可疑抽象 | 新增机制有明确必要性，或复用现有机制 | context、diff |

总分为六维相加（6–30），但 Blocker、未解释的 Contract deviation、测试失败或超出 Scope 时不得以高分抵消。裁判应独立评分；每个分数须引用实际 patch 或验证证据，不得仅复述模型自评。
