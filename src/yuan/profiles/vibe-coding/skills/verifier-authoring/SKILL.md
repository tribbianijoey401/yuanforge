---
name: verifier-authoring
description: 在首个 Work 接受前，于非 Artifact 草稿区创建并绑定确定性只读 Python Verifier。
---

# Verifier 编写

1. Verifier 草稿只能写入 `.yuan/drafts/verifiers/`；该目录不属于 Artifact，也不属于托管 Profile。
2. 每个 Criterion 使用独立入口，例如 `.yuan/drafts/verifiers/AC-001.py`，并在 Work 中同时填写 `entrypoint` 与 `files`。
3. 脚本从 `sys.argv[1]` 读取项目根目录，只读检查 Artifact；不得写文件、启动进程、访问网络或依赖 Shell。
4. stdout 只能输出一个 JSON Object：`{"status":"PASS|FAIL","assertions":[{"id":"...","passed":true|false}]}`。
5. PASS 必须至少包含 `min_assertions` 个通过断言；断言应直接对应 Criterion，而不是只检查文件存在。
6. 用 `work bind-verifier` 固定全部文件 Digest，再执行 `work accept`。接受后修改 Verifier 会使校验失败，必须通过 Successor Work 重新绑定。

最小骨架：

```python
import json
import sys
from pathlib import Path

root = Path(sys.argv[1])
passed = (root / "替换为目标文件").is_file()
print(json.dumps({"status": "PASS" if passed else "FAIL", "assertions": [{"id": "AC-001", "passed": passed}]}))
```
