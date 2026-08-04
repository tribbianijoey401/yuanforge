"""共享的无依赖 Record 校验原语。"""

from __future__ import annotations

import re
from typing import Any

from .errors import ValidationError


SHA256 = re.compile(r"^[0-9a-f]{64}$")
IDENT = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,127}$")


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValidationError(message)


def identifier(value: Any, label: str) -> str:
    require(isinstance(value, str) and bool(IDENT.fullmatch(value)), f"{label} 不合法")
    return value


def sha256(value: Any, label: str) -> str:
    require(isinstance(value, str) and bool(SHA256.fullmatch(value)), f"{label} 不是合法的 SHA-256")
    return value
