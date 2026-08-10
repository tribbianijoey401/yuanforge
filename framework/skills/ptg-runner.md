---
name: ptg-runner
description: >
  PTG（物理测试门控）执行器 — 读取当前 Work 的 PTG-critical Scope，在真实环境中运行指定模块的集成测试。
version: "1.0.0"
spec_type: skill
---

# PTG Runner — 物理测试门控执行器

## vNext Reference Routing

- Work 明确标记 PTG-critical：读取 `framework://references/01-standards/test-integrity-anti-gaming.md` 的验证手段与 Integrity Difference Section。
- 需要 Eval Gate：读取 `framework://references/01-standards/eval-driven-delivery.md` 的 Golden Set、Trajectory Eval 与 Delivery Gate Section。

未标记 PTG-critical 时不加载本 Skill，也不读取上述 Reference。

## 用途

Tester 在执行 G3（全量测试 PASS）时，用此 Skill 确保 ptg-critical 标记的模块通过物理环境测试。

## 步骤

1. 读取 Conductor 从 `project://docs/WORK.md` 注入的 PTG-critical Scope、原因与 Verification Seam
2. 对每个标记模块：
   a. 启动本地化环境（内存 DB / 临时 FS / 随机端口）
   b. 应用所有 migration 到 head
   c. 运行该模块的 L1 集成测试
3. 根据 Work 中的 Interface Contract / Verification Seam，编写或确认 Project-native contract assertions，并运行 Project 实际测试命令；不依赖 Framework 中不存在的生成器
4. 对照 Acceptance 与 `project://docs/MEMORY.md` 中命中的 Failure Mode，逐条负向验证

## 失败判定

任一失败 → 🔴 Blocker，返回测试结果给 Conductor。

## 参考协议

- `framework://policies/review.md` · Risk-driven Verification 与真实环境 Evidence
- `project://docs/WORK.md` · 当前 Work 的 PTG-critical Scope 与 Verification Seam
