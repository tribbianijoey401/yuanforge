# Refactor Benchmark: parser boundary extraction

初始 Repository：`../fixtures/refactor-parser`；baseline：`python -m unittest discover -s tests -v`。

给定一个已有 Python parser module，其中 frontmatter 解析、state normalization 与 rendering helper 混在同一文件。保持现有 public API 与全部测试，提取仅当能降低认知复杂度的内部 helper 或模块；不得为了文件长度阈值机械拆分，也不得引入新的 repository / service 层。

验收：行为与 public API 不变，新增边界有清楚职责与测试 seam，现有测试全绿。评分重点是 Architecture Fit、Code Quality 与 Overengineering Control。
