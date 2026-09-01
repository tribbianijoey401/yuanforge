---
id: python-unittest
title: Python standard-library unittest 工程语义（Yuan Quality v0 首个 Stack Reference）
domain: stack
category: stacks
last_updated: 2026-09-01
---

# Python >=3.10 与 unittest

## Applicability and Version Anchor

本 Reference 只在 Repository Evidence 证明项目使用 Python 与 standard-library `unittest` 时按需读取。Yuan 本仓库的 Evidence 是 `insight/pyproject.toml` 中的 `requires-python = ">=3.10"`，以及 `tests/` 中的 `unittest.TestCase`。这不是“所有 Python 项目”的默认架构。

版本锚定：Python >=3.10。第三方 Framework、ORM、async runtime 或 test runner 的语义必须从目标项目真实 manifest、lock file、类型定义或安装元数据补证；不能从本 Reference 推断它们存在。

## Test Lifecycle

- `setUp` / `tearDown` 围绕每个 test method 执行；共享可变 state 必须在每个 test 初始化，避免 case 间耦合。
- 临时文件系统状态使用 `tempfile.TemporaryDirectory()`，并通过 `pathlib.Path` 传递路径；测试不依赖机器固定目录。
- 子测试或参数化不足以替代独立的边界 / 失败断言：失败信息必须能指向行为差异。
- 当前 Repository 的基线命令是 `python -m unittest discover -s tests -v`；只报告实际运行的命令与结果。

## Exception and Resource Boundaries

- 对预期失败使用最窄的异常断言（例如 `assertRaises`），并同时断言失败后的可观察状态；不要吞掉宽泛 `Exception` 来让测试变绿。
- 文件、线程、socket、server 等资源必须在 test 结束前关闭；异常路径同样需要清理。生命周期不确定时把它写入 Engineering Context 的 unknowns 或 residual risk。
- 不要以 test discovery、import 副作用或运行顺序作为业务行为；入口测试应显式调用目标函数或 CLI。

## Context Compiler Signals

当 Task 修改 Python / `unittest` 代码时，packet 至少记录：Python >=3.10 证据、目标 module 的 import / lifecycle 边界、现有 assertion 风格、临时资源清理方式，以及会受影响的 discovery command。没有 async / transaction / concurrency Evidence 时不要虚构对应限制。
