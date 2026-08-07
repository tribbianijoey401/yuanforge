---
name: ptg-runner
description: >
  PTG（物理测试门控）执行器 — 读取 docs/ptg-critical.md 清单，在真实环境中运行指定模块的集成测试。
  与 CAL 配合：PTG 指定"在哪跑"，CAL 生成"验证什么"。
version: "1.0.0"
spec_type: skill
---

# PTG Runner — 物理测试门控执行器

## vNext Reference Routing

- Work 明确标记 PTG-critical：读取 `references/01-standards/test-integrity-anti-gaming.md` 的验证手段与 Integrity Difference Section。
- 需要 Eval Gate：读取 `references/01-standards/eval-driven-delivery.md` 的 Golden Set、Trajectory Eval 与 Delivery Gate Section。

未标记 PTG-critical 时不加载本 Skill，也不读取上述 Reference。

## 用途

Tester 在执行 G3（全量测试 PASS）时，用此 Skill 确保 ptg-critical 标记的模块通过物理环境测试。

## 步骤

1. 读取 Conductor 注入的 `docs/ptg-critical.md`（任务行中的原因指针列指向此文件）
2. 对每个标记模块：
   a. 启动本地化环境（内存 DB / 临时 FS / 随机端口）
   b. 应用所有 migration 到 head
   c. 运行该模块的 L1 集成测试
3. 执行 CAL 断言生成 + 执行：
   ```bash
   python scripts/ptg-cal-gen.py -i docs/seam-agreement.md -o tests/test_contract_assertions.py
   python -m pytest tests/test_contract_assertions.py
   ```
4. 对抗模式匹配：读取 `docs/anti-patterns.md`，逐条验证

## 失败判定

任一失败 → 🔴 Blocker，返回测试结果给 Conductor。

## 参考协议

- `policies/review.md` · Risk-driven Verification 与真实环境 Evidence
- seam-agreement.md §6 · @ptg 字段注解
