---
id: python-unittest
title: Python standard-library unittest 工程语义（Yuan Quality v0 首个 Stack Reference）
domain: stack
category: stacks
last_updated: 2026-09-01
---

# Python 与 unittest

## Applicability and Version Anchor

本 Reference 只在**目标 Repository** Evidence 证明项目使用 Python 与 standard-library `unittest` 时按需读取。它分两层适用：

1. **generic**：目标 Repository 的 manifest、source import 或现有测试证明 Python + `unittest`，但未确认解释器版本时，只使用跨版本稳定的 unittest 生命周期、异常断言与资源清理语义。
2. **version-specific**：只有目标 Repository 的 `requires-python`、lock / runtime metadata、CI runtime 或实际解释器证实版本时，才使用相应版本的 Python 语义；例如 `Python >=3.10` 只能由目标 Evidence 启用。

Yuan 源仓库、调用 Agent 的运行环境或模型记忆都不能证明被修改的目标 Repository 的 Python 版本。第三方 Framework、ORM、async runtime 或 test runner 的语义必须从目标项目真实 manifest、lock file、类型定义或安装元数据补证；不能从本 Reference 推断它们存在。版本未知或会影响结论时写入 Engineering Context 的 `unknowns`。

## Generic unittest lifecycle

- `setUp` / `tearDown` 围绕每个 test method 执行；共享可变 state 应在每个 test 初始化，避免 case 间耦合。
- 临时文件、线程、socket、server 等资源在 test 结束前关闭；异常路径同样需要清理。
- 子测试或参数化不足以替代独立的边界 / 失败断言：失败信息应能指向行为差异。
- 对预期失败使用最窄的异常断言（例如 `assertRaises`），并断言失败后的可观察状态；不要吞掉宽泛 `Exception` 来让测试变绿。
- 不要以 test discovery、import 副作用或运行顺序作为业务行为；入口测试显式调用目标函数或 CLI。

## Context Compiler Signals

当 Task 修改已证实的 Python / `unittest` 代码时，packet 记录：目标项目的 Python / unittest Evidence、已确认版本（若有）、目标 module 的 import / 生命周期边界、现有 assertion 风格、资源清理方式，以及会受影响的实际 discovery command。没有 async / transaction / concurrency Evidence 时不要虚构对应限制。
