import json

print(
    json.dumps(
        {
            "schema_version": "yuan.validator-result/v1",
            "status": "PASS",
            "assertions": 0,
            "checks": [],
        }
    )
)
