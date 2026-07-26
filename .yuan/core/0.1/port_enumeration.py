"""Bounded, stable, content-bound filesystem enumeration."""

from __future__ import annotations

import hashlib
import os
import pathlib
import uuid
from datetime import datetime, timezone

from port_types import (
    EnumeratedFile,
    EnumerationLimitExceeded,
    FileEnumerationReceipt,
    ScopeViolation,
)


def configured_limits(max_files: object, max_depth: object) -> tuple[int, int]:
    valid_files = (
        isinstance(max_files, int)
        and not isinstance(max_files, bool)
        and max_files > 0
    )
    valid_depth = (
        isinstance(max_depth, int)
        and not isinstance(max_depth, bool)
        and max_depth >= 0
    )
    if not valid_files or not valid_depth:
        raise ValueError("enumeration bounds must be non-negative integers")
    return max_files, max_depth


def bounded_limits(
    *,
    max_files: int | None,
    max_depth: int | None,
    configured_files: int,
    configured_depth: int,
) -> tuple[int, int]:
    files = configured_files if max_files is None else max_files
    depth = configured_depth if max_depth is None else max_depth
    valid_files = (
        isinstance(files, int)
        and not isinstance(files, bool)
        and 0 < files <= configured_files
    )
    valid_depth = (
        isinstance(depth, int)
        and not isinstance(depth, bool)
        and 0 <= depth <= configured_depth
    )
    if not valid_files or not valid_depth:
        raise EnumerationLimitExceeded("invalid or expanded enumeration bound")
    return files, depth


def _is_link_or_junction(path: pathlib.Path) -> bool:
    return path.is_symlink() or (
        hasattr(os.path, "isjunction") and os.path.isjunction(path)
    )


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def enumerate_bounded(
    *,
    root: pathlib.Path,
    scope: pathlib.Path,
    max_files: int,
    max_depth: int,
) -> FileEnumerationReceipt:
    if not scope.is_dir() or _is_link_or_junction(scope):
        raise ScopeViolation("enumeration scope must be a real directory")
    entries: list[EnumeratedFile] = []
    pending: list[tuple[pathlib.Path, int]] = [(scope, 0)]
    while pending:
        directory, depth = pending.pop()
        try:
            children = sorted(directory.iterdir(), key=lambda item: item.name)
        except OSError as error:
            raise ScopeViolation("enumeration scope cannot be inspected") from error
        for child in children:
            if _is_link_or_junction(child):
                raise ScopeViolation("enumeration rejects links and junctions")
            try:
                child.resolve(strict=True).relative_to(root)
            except (OSError, ValueError) as error:
                raise ScopeViolation("enumerated path escapes the Port root") from error
            if child.is_dir():
                if depth >= max_depth:
                    raise EnumerationLimitExceeded(
                        "enumeration exceeded the maximum depth"
                    )
                pending.append((child, depth + 1))
                continue
            if not child.is_file():
                raise ScopeViolation("enumeration encountered a non-regular file")
            if len(entries) >= max_files:
                raise EnumerationLimitExceeded(
                    "enumeration exceeded the maximum file count"
                )
            data = child.read_bytes()
            if _is_link_or_junction(child) or not child.is_file():
                raise ScopeViolation("enumerated file changed during observation")
            entries.append(
                EnumeratedFile(
                    path=child.relative_to(root).as_posix(),
                    sha256=hashlib.sha256(data).hexdigest(),
                    size_bytes=len(data),
                )
            )
    entries.sort(key=lambda item: item.path)
    return FileEnumerationReceipt(
        schema_version="yuan.tool-receipt/v1",
        kind="file-enumeration",
        operation_id=str(uuid.uuid4()),
        status="OBSERVED",
        scope=scope.relative_to(root).as_posix() or ".",
        entries=tuple(entries),
        max_files=max_files,
        max_depth=max_depth,
        observed_at=_utc_now(),
    )
