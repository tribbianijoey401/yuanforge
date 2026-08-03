---
name: test-driven-development
description: 对缺陷修复和稳定行为实现执行 Red、Green、Refactor 闭环。
---

# 测试驱动开发

1. 在稳定行为 Seam 上增加最小失败测试并实际运行，保存 FAIL Evidence。
2. 确认失败原因与目标缺陷一致，而非环境或语法错误。
3. 编写使该测试通过的最小实现，运行相关测试。
4. 在绿色保护下重构，随后运行合理范围回归。
5. Evidence 同时保留失败前提、PASS 断言和 Artifact Binding。
