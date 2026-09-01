# Refactor Benchmark: parser boundary extraction

初始 Repository：`../fixtures/refactor-parser`；baseline：`python -m unittest discover -s tests -v`。

给定一个已有 Python module，其中多个内部职责混在同一实现中。保持现有 public API 与全部测试；如新增或改变内部边界，应使其职责清楚且可独立测试。

验收：行为与 public API 不变，新增或改变的内部边界有清楚职责并可测试，现有测试全绿。
