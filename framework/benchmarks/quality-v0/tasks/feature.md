# Feature Benchmark: bounded configuration loader

初始 Repository：`../fixtures/feature-config`；baseline：`python -m unittest discover -s tests -v`。

给定一个 Python 项目已有 `ConfigError`、`load_settings(path)` 和 `unittest` 测试，新增可选 `timeout_seconds` 配置：只接受正整数；缺失时沿用现有默认；非法值必须沿用现有错误模型。不得新建全局 singleton、重写配置格式或改变未受影响字段。

验收：成功、缺失、零、负数、非整数和现有配置兼容性都有测试。评分重点是复用既有错误 / 默认机制、真实 Python 版本语义和不过度抽象。
