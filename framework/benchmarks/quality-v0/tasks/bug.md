# Bug Benchmark: temporary resource cleanup

初始 Repository：`../fixtures/bug-cleanup`；baseline：`python -m unittest discover -s tests -v`。

给定一个 Python CLI 测试在 callback 异常路径遗留临时资源，修复异常路径的清理，同时保持原始异常可观察且成功路径行为不变。

验收：异常路径后临时资源被清理、原异常仍可观察、成功路径不回归。
