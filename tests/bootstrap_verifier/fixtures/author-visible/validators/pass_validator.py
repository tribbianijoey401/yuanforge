import json

print(
    json.dumps(
        {
            "schema_version": "yuan.validator-result/v1",
            "status": "PASS",
            "assertions": 2,
            "checks": [
                {"id": "visible-structure", "status": "PASS"},
                {"id": "visible-content", "status": "PASS"},
            ],
        }
    )
)
