# Feature Benchmark: bounded configuration loader

初始 Repository：`../fixtures/feature-config`；baseline：`python -m unittest discover -s tests -v`。

给定一个已有配置加载行为和测试的 Python 项目，新增可选 `timeout_seconds` 配置：只接受正整数；缺失时保持当前可观察的默认行为；非法值保持当前可观察的公开错误行为；未受影响字段保持兼容。

验收：成功、缺失、零、负数、非整数和现有配置兼容性都有测试。
