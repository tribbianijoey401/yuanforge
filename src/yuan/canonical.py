"""Canonical JSON 与内容寻址。"""

from __future__ import annotations

import hashlib
import json
from typing import Any, Iterable

from .errors import ValidationError


def canonical_bytes(value: Any) -> bytes:
    try:
        text = json.dumps(
            value,
            ensure_ascii=False,
            allow_nan=False,
            separators=(",", ":"),
            sort_keys=True,
        )
    except (TypeError, ValueError) as exc:
        raise ValidationError(f"Value 无法编码为 Canonical JSON：{exc}") from exc
    return text.encode("utf-8")


def digest_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def digest(value: Any, omit: Iterable[str] = ()) -> str:
    if not isinstance(value, dict):
        return digest_bytes(canonical_bytes(value))
    clone = dict(value)
    for key in omit:
        clone.pop(key, None)
    return digest_bytes(canonical_bytes(clone))


def verify_digest(value: dict[str, Any], field: str = "digest") -> bool:
    claimed = value.get(field)
    return isinstance(claimed, str) and claimed == digest(value, (field,))
