#!/usr/bin/env python3
"""Independent, deterministic validator for the M5 Yuan Core canary artifact.

The validator is content-addressed by the Work Contract before the canary runs.
It has no write capability and emits one machine-readable result on stdout.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
from typing import Any


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _check(checks: list[dict[str, str]], check_id: str, passed: bool, detail: str) -> None:
    checks.append(
        {
            "id": check_id,
            "status": "PASS" if passed else "FAIL",
            "observation": detail,
        }
    )


def validate(
    artifact: pathlib.Path,
    *,
    expected_payload_hex: str,
    authority_pointer: pathlib.Path,
    expected_authority_sha256: str,
) -> dict[str, Any]:
    checks: list[dict[str, str]] = []
    try:
        expected_payload = bytes.fromhex(expected_payload_hex)
        artifact_bytes = artifact.read_bytes()
        authority_bytes = authority_pointer.read_bytes()
        authority = json.loads(authority_bytes.decode("utf-8"))
        _check(
            checks,
            "CANARY-EXACT-BYTES",
            artifact_bytes == expected_payload,
            "artifact bytes equal the Work-bound deterministic payload",
        )
        _check(
            checks,
            "CANARY-ARTIFACT-DIGEST",
            _sha256(artifact_bytes) == _sha256(expected_payload),
            "artifact digest equals the expected payload digest",
        )
        _check(
            checks,
            "SAFE-LEGACY-AUTHORITY",
            _sha256(authority_bytes) == expected_authority_sha256
            and authority.get("authority") == "legacy",
            "M4 authority pointer is byte-identical and still selects legacy",
        )
    except Exception as error:
        checks.append(
            {
                "id": "CANARY-VALIDATOR-EXECUTION",
                "status": "ERROR",
                "observation": f"{type(error).__name__}: {error}",
            }
        )
    status = "PASS" if checks and all(item["status"] == "PASS" for item in checks) else "FAIL"
    return {
        "schema_version": "yuan.validator-result/v1",
        "status": status,
        "assertions": len(checks),
        "checks": checks,
        "producer": "task-008-independent-canary-validator",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("artifact", type=pathlib.Path)
    parser.add_argument("expected_payload_hex")
    parser.add_argument("authority_pointer", type=pathlib.Path)
    parser.add_argument("expected_authority_sha256")
    args = parser.parse_args()
    result = validate(
        args.artifact,
        expected_payload_hex=args.expected_payload_hex,
        authority_pointer=args.authority_pointer,
        expected_authority_sha256=args.expected_authority_sha256,
    )
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    return 0 if result["status"] == "PASS" and result["assertions"] > 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
