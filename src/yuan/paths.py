"""可移植的 Repository Relative Path 规则。"""

from __future__ import annotations

import fnmatch
from pathlib import Path, PurePosixPath

from .errors import ValidationError


def normalize_relative(value: str) -> str:
    if not isinstance(value, str) or not value or "\\" in value:
        raise ValidationError("Path 必须是非空 POSIX Relative Path")
    path = PurePosixPath(value)
    if path.is_absolute() or any(part in {"", ".", ".."} for part in path.parts):
        raise ValidationError(f"不安全的 Relative Path：{value}")
    return path.as_posix()


def resolve_inside(root: Path, relative: str) -> Path:
    safe = normalize_relative(relative)
    target = (root / safe).resolve()
    try:
        target.relative_to(root.resolve())
    except ValueError as exc:
        raise ValidationError(f"Path 逃逸 Artifact Root：{relative}") from exc
    return target


def matches_any(path: str, patterns: list[str]) -> bool:
    return any(
        fnmatch.fnmatchcase(path, pattern)
        or (pattern.endswith("/**") and path == pattern[:-3])
        for pattern in patterns
    )


def scope_contains(scope: str, path: str) -> bool:
    scope = normalize_relative(scope)
    path = normalize_relative(path)
    return path == scope or path.startswith(scope.rstrip("/") + "/")
