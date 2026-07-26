import json
import pathlib
import sys

candidate = pathlib.Path(sys.argv[1])
is_bad = "KNOWN_BAD" in (candidate / "protocol.md").read_text(encoding="utf-8")
print(
    json.dumps(
        {
            "schema_version": "yuan.validator-result/v1",
            "status": "FAIL" if is_bad else "PASS",
            "assertions": 1,
            "checks": [
                {
                    "id": "known-bad-marker",
                    "status": "FAIL" if is_bad else "PASS",
                }
            ],
        }
    )
)
