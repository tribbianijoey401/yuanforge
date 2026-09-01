# Bug Benchmark: temporary resource cleanup

初始 Repository：`../fixtures/bug-cleanup`；baseline：`python -m unittest discover -s tests -v`。

给定一个 Python `unittest` CLI 测试在异常路径遗留临时目录，修复资源生命周期而不吞掉原始异常、放宽断言或改变 CLI 行为。现有项目使用 `TemporaryDirectory` 和 `pathlib.Path`。

验收：异常路径后临时目录被清理、原异常仍可观察、成功路径不回归。评分重点是生命周期、错误模型和最小 Diff。
