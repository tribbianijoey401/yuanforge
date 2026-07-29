"""Minimal controlled filesystem/command/LLM proposal port for Yuan Core 0.1."""

from __future__ import annotations

import hashlib
import os
import pathlib
import subprocess
import tempfile
import threading
import time
import uuid
from datetime import datetime, timezone
from typing import Any, Sequence

from command_sandbox import PYTHON_PROFILE, prepare_command
from port_enumeration import bounded_limits, configured_limits, enumerate_bounded
from port_proposal import build_proposal_receipt
from port_types import (
    CASMismatch,
    CancellationToken,
    CommandReceipt,
    CommandRejected,
    FileEnumerationReceipt,
    FileReadReceipt,
    FileWriteReceipt,
    ProposalProvider,
    ScopeViolation,
    UnsupportedCapability,
)


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _is_link_or_junction(path: pathlib.Path) -> bool:
    return path.is_symlink() or (
        hasattr(os.path, "isjunction") and os.path.isjunction(path)
    )


class ReferencePort:
    """Reference Port with deny-by-default scope and command execution."""

    def __init__(
        self,
        root: pathlib.Path | str,
        *,
        allowed_executables: Sequence[pathlib.Path | str],
        max_command_seconds: float,
        max_output_bytes: int,
        proposal_provider: ProposalProvider | None = None,
        command_profiles: dict[str, str] | None = None,
        max_enumeration_files: int = 10_000,
        max_enumeration_depth: int = 32,
    ) -> None:
        self.root = pathlib.Path(root).resolve(strict=True)
        if not self.root.is_dir() or _is_link_or_junction(self.root):
            raise ScopeViolation("root must be a real directory")
        if max_command_seconds <= 0 or max_output_bytes <= 0:
            raise ValueError("command and output bounds must be positive")
        enumeration_bounds = configured_limits(
            max_enumeration_files, max_enumeration_depth
        )
        self.allowed_executables = {
            os.path.normcase(str(pathlib.Path(item).resolve(strict=True)))
            for item in allowed_executables
        }
        explicit_profiles = command_profiles or {}
        self.command_profiles = {
            os.path.normcase(str(pathlib.Path(path).resolve(strict=True))): profile
            for path, profile in explicit_profiles.items()
        }
        for executable in self.allowed_executables:
            if pathlib.Path(executable).name.lower().startswith("python"):
                self.command_profiles.setdefault(executable, PYTHON_PROFILE)
        self.max_command_seconds = float(max_command_seconds)
        self.max_output_bytes = int(max_output_bytes)
        self.max_enumeration_files, self.max_enumeration_depth = enumeration_bounds
        self.proposal_provider = proposal_provider
        self._write_lock = threading.Lock()

    def _resolve(self, relative: str, *, allow_missing: bool) -> pathlib.Path:
        if not isinstance(relative, str) or not relative or "\x00" in relative:
            raise ScopeViolation("path must be a non-empty relative string")
        raw = pathlib.Path(relative)
        if raw.is_absolute() or any(part == ".." for part in raw.parts):
            raise ScopeViolation("path escapes the Port root")
        target = self.root.joinpath(raw)
        current = self.root
        for part in raw.parts:
            current = current / part
            if current.exists() and _is_link_or_junction(current):
                raise ScopeViolation("links and junctions are outside the controlled scope")
        resolved = target.resolve(strict=not allow_missing)
        try:
            resolved.relative_to(self.root)
        except ValueError as error:
            raise ScopeViolation("resolved path escapes the Port root") from error
        return resolved

    def read(self, relative: str, *, expected_sha256: str | None = None) -> FileReadReceipt:
        path = self._resolve(relative, allow_missing=False)
        if not path.is_file():
            raise ScopeViolation("read target is not a regular file")
        data = path.read_bytes()
        sha256 = _digest(data)
        if expected_sha256 is not None and sha256 != expected_sha256:
            raise CASMismatch("read hash does not match expected content")
        return FileReadReceipt(
            schema_version="yuan.tool-receipt/v1",
            kind="file-read",
            operation_id=str(uuid.uuid4()),
            status="OBSERVED",
            path=path.relative_to(self.root).as_posix(),
            sha256=sha256,
            size_bytes=len(data),
            data=data,
            observed_at=_utc_now(),
        )

    def enumerate_files(
        self,
        relative: str,
        *,
        max_files: int | None = None,
        max_depth: int | None = None,
    ) -> FileEnumerationReceipt:
        files, depth = bounded_limits(
            max_files=max_files,
            max_depth=max_depth,
            configured_files=self.max_enumeration_files,
            configured_depth=self.max_enumeration_depth,
        )
        return enumerate_bounded(
            root=self.root,
            scope=self._resolve(relative, allow_missing=False),
            max_files=files,
            max_depth=depth,
        )

    def atomic_write(
        self,
        relative: str,
        data: bytes,
        *,
        expected_sha256: str | None,
    ) -> FileWriteReceipt:
        if not isinstance(data, bytes):
            raise TypeError("atomic_write accepts bytes only")
        path = self._resolve(relative, allow_missing=True)
        path.parent.mkdir(parents=True, exist_ok=True)
        self._resolve(path.parent.relative_to(self.root).as_posix(), allow_missing=False)
        temporary: str | None = None
        with self._write_lock:
            exists = path.exists()
            before = _digest(path.read_bytes()) if exists and path.is_file() else None
            if exists and not path.is_file():
                raise ScopeViolation("write target is not a regular file")
            if exists and expected_sha256 is None:
                raise CASMismatch("existing content requires an expected SHA-256")
            if not exists and expected_sha256 is not None:
                raise CASMismatch("create requires expected_sha256=None")
            if exists and before != expected_sha256:
                raise CASMismatch("write compare-and-swap hash mismatch")
            try:
                with tempfile.NamedTemporaryFile(
                    "wb",
                    dir=path.parent,
                    prefix=f".{path.name}.",
                    suffix=".tmp",
                    delete=False,
                ) as stream:
                    stream.write(data)
                    stream.flush()
                    os.fsync(stream.fileno())
                    temporary = stream.name
                current = _digest(path.read_bytes()) if path.exists() else None
                if current != before:
                    raise CASMismatch("target changed during compare-and-swap")
                os.replace(temporary, path)
                temporary = None
            finally:
                if temporary and os.path.exists(temporary):
                    os.unlink(temporary)
        return FileWriteReceipt(
            schema_version="yuan.tool-receipt/v1",
            kind="file-write",
            operation_id=str(uuid.uuid4()),
            status="REPLACED" if exists else "CREATED",
            path=path.relative_to(self.root).as_posix(),
            before_sha256=before,
            after_sha256=_digest(data),
            size_bytes=len(data),
            committed_at=_utc_now(),
        )

    def _bounded_text(self, value: str) -> tuple[str, bool]:
        encoded = value.encode("utf-8", errors="replace")
        truncated = len(encoded) > self.max_output_bytes
        if truncated:
            encoded = encoded[: self.max_output_bytes]
            while True:
                try:
                    value = encoded.decode("utf-8")
                    break
                except UnicodeDecodeError:
                    encoded = encoded[:-1]
        else:
            value = encoded.decode("utf-8")
        return value, truncated

    @staticmethod
    def _stop(process: subprocess.Popen[str]) -> None:
        if process.poll() is not None:
            return
        process.terminate()
        try:
            process.wait(timeout=0.5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=0.5)

    def run_command(
        self,
        argv: Sequence[str],
        *,
        timeout_seconds: float,
        cwd: str = ".",
        cancellation: CancellationToken | None = None,
    ) -> CommandReceipt:
        if isinstance(argv, (str, bytes)) or not argv or not all(
            isinstance(item, str) and item and "\x00" not in item for item in argv
        ):
            raise CommandRejected("argv must be a non-empty token sequence; shell strings are forbidden")
        if timeout_seconds <= 0 or timeout_seconds > self.max_command_seconds:
            raise CommandRejected("timeout exceeds the Work/Port bound")
        try:
            executable = pathlib.Path(argv[0]).resolve(strict=True)
        except OSError as error:
            raise CommandRejected("executable does not exist") from error
        if os.path.normcase(str(executable)) not in self.allowed_executables:
            raise CommandRejected("executable is not explicitly bound")
        profile = self.command_profiles.get(os.path.normcase(str(executable)))
        if profile is None:
            raise CommandRejected("executable has no bound invocation profile")
        try:
            effective_argv = prepare_command(executable, argv, self.root, profile)
        except ValueError as error:
            raise CommandRejected(str(error)) from error
        command_cwd = self._resolve(cwd, allow_missing=False)
        if not command_cwd.is_dir():
            raise CommandRejected("command cwd is not a directory")
        started_at = _utc_now()
        started = time.monotonic()
        process = subprocess.Popen(
            effective_argv,
            cwd=command_cwd,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            errors="replace",
            shell=False,
        )
        status = "EXITED"
        stdout = ""
        stderr = ""
        exit_code: int | None = None
        deadline = started + timeout_seconds
        while True:
            if cancellation is not None and cancellation.cancelled:
                status = "CANCELLED"
                self._stop(process)
                stdout, stderr = process.communicate()
                break
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                status = "TIMED_OUT"
                self._stop(process)
                stdout, stderr = process.communicate()
                break
            try:
                stdout, stderr = process.communicate(timeout=min(remaining, 0.05))
                exit_code = process.returncode
                break
            except subprocess.TimeoutExpired:
                continue
        bounded_stdout, stdout_truncated = self._bounded_text(stdout)
        bounded_stderr, stderr_truncated = self._bounded_text(stderr)
        return CommandReceipt(
            schema_version="yuan.tool-receipt/v1",
            kind="command",
            operation_id=str(uuid.uuid4()),
            status=status,
            profile=profile,
            sandboxed=True,
            argv=tuple(argv),
            cwd=command_cwd.relative_to(self.root).as_posix() or ".",
            started_at=started_at,
            duration_seconds=round(time.monotonic() - started, 6),
            exit_code=exit_code,
            stdout=bounded_stdout,
            stderr=bounded_stderr,
            stdout_sha256=_digest(stdout.encode("utf-8", errors="replace")),
            stderr_sha256=_digest(stderr.encode("utf-8", errors="replace")),
            stdout_truncated=stdout_truncated,
            stderr_truncated=stderr_truncated,
        )

    def propose(self, request: dict[str, Any]) -> dict[str, Any]:
        if self.proposal_provider is None:
            raise UnsupportedCapability("no LLM proposal provider is bound")
        return build_proposal_receipt(self.proposal_provider, request)
