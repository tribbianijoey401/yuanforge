"""Small offline validator for the JSON-compatible Yuan Core schemas."""

from __future__ import annotations

import json
import re
from datetime import datetime
from typing import Any


def _resolve_ref(root: dict[str, Any], ref: str) -> dict[str, Any]:
    if not ref.startswith("#/"):
        raise ValueError("only local schema references are supported")
    value: Any = root
    for token in ref[2:].split("/"):
        value = value[token.replace("~1", "/").replace("~0", "~")]
    if not isinstance(value, dict):
        raise ValueError("schema reference does not resolve to an object")
    return value


def _matches_type(value: Any, expected: str) -> bool:
    return {
        "object": isinstance(value, dict),
        "array": isinstance(value, list),
        "string": isinstance(value, str),
        "integer": isinstance(value, int) and not isinstance(value, bool),
        "number": isinstance(value, (int, float)) and not isinstance(value, bool),
        "boolean": isinstance(value, bool),
        "null": value is None,
    }.get(expected, False)


def validate_schema(
    value: Any,
    schema: dict[str, Any],
    root: dict[str, Any],
    path: str,
    errors: list[str],
) -> int:
    checks = 1
    if "$ref" in schema:
        return checks + validate_schema(
            value, _resolve_ref(root, schema["$ref"]), root, path, errors
        )
    for branch in schema.get("allOf", []):
        checks += validate_schema(value, branch, root, path, errors)
    expected = schema.get("type")
    if expected is not None:
        variants = expected if isinstance(expected, list) else [expected]
        if not any(_matches_type(value, item) for item in variants):
            errors.append(f"SCHEMA_TYPE:{path}")
            return checks
    if "const" in schema and value != schema["const"]:
        errors.append(f"SCHEMA_CONST:{path}")
    if "enum" in schema and value not in schema["enum"]:
        errors.append(f"SCHEMA_ENUM:{path}")
    if isinstance(value, str):
        if len(value) < schema.get("minLength", 0):
            errors.append(f"SCHEMA_MIN_LENGTH:{path}")
        if "pattern" in schema and re.search(schema["pattern"], value) is None:
            errors.append(f"SCHEMA_PATTERN:{path}")
        if schema.get("format") == "date-time":
            try:
                datetime.fromisoformat(value.replace("Z", "+00:00"))
            except ValueError:
                errors.append(f"SCHEMA_DATE_TIME:{path}")
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        if "minimum" in schema and value < schema["minimum"]:
            errors.append(f"SCHEMA_MINIMUM:{path}")
        if "exclusiveMinimum" in schema and value <= schema["exclusiveMinimum"]:
            errors.append(f"SCHEMA_EXCLUSIVE_MINIMUM:{path}")
    if isinstance(value, list):
        if len(value) < schema.get("minItems", 0):
            errors.append(f"SCHEMA_MIN_ITEMS:{path}")
        if len(value) > schema.get("maxItems", len(value)):
            errors.append(f"SCHEMA_MAX_ITEMS:{path}")
        if schema.get("uniqueItems"):
            canonical = [
                json.dumps(item, sort_keys=True, ensure_ascii=False) for item in value
            ]
            if len(canonical) != len(set(canonical)):
                errors.append(f"SCHEMA_UNIQUE_ITEMS:{path}")
        if isinstance(schema.get("items"), dict):
            for index, item in enumerate(value):
                checks += validate_schema(
                    item, schema["items"], root, f"{path}/{index}", errors
                )
    if isinstance(value, dict):
        properties = schema.get("properties", {})
        for required in schema.get("required", []):
            checks += 1
            if required not in value:
                errors.append(f"SCHEMA_REQUIRED:{path}/{required}")
        additional = schema.get("additionalProperties", True)
        for key, item in value.items():
            if key in properties:
                checks += validate_schema(
                    item, properties[key], root, f"{path}/{key}", errors
                )
            elif additional is False:
                errors.append(f"SCHEMA_ADDITIONAL:{path}/{key}")
            elif isinstance(additional, dict):
                checks += validate_schema(
                    item, additional, root, f"{path}/{key}", errors
                )
    return checks
