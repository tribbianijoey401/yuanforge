"""Public receipt, cancellation, and error types for the reference Port."""

from __future__ import annotations

import threading
from dataclasses import dataclass
from typing import Any, Protocol


class PortError(RuntimeError):
    pass


class ScopeViolation(PortError):
    pass


class CASMismatch(PortError):
    pass


class CommandRejected(PortError):
    pass


class UnsupportedCapability(PortError):
    pass


class ProposalProvider(Protocol):
    def propose(self, request: dict[str, Any]) -> dict[str, Any]: ...


class CancellationToken:
    def __init__(self) -> None:
        self._event = threading.Event()

    def cancel(self) -> None:
        self._event.set()

    @property
    def cancelled(self) -> bool:
        return self._event.is_set()


@dataclass(frozen=True)
class FileReadReceipt:
    schema_version: str
    kind: str
    operation_id: str
    status: str
    path: str
    sha256: str
    size_bytes: int
    data: bytes
    observed_at: str


@dataclass(frozen=True)
class FileWriteReceipt:
    schema_version: str
    kind: str
    operation_id: str
    status: str
    path: str
    before_sha256: str | None
    after_sha256: str
    size_bytes: int
    committed_at: str


@dataclass(frozen=True)
class CommandReceipt:
    schema_version: str
    kind: str
    operation_id: str
    status: str
    argv: tuple[str, ...]
    cwd: str
    started_at: str
    duration_seconds: float
    exit_code: int | None
    stdout: str
    stderr: str
    stdout_sha256: str
    stderr_sha256: str
    stdout_truncated: bool
    stderr_truncated: bool
