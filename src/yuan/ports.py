"""Yuan 的稳定 Port 边界与标准库参考实现。"""

from __future__ import annotations

import os
import signal
import subprocess
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from .artifacts import build_manifest
from .canonical import canonical_bytes, digest, digest_bytes
from .errors import IntegrityError, ValidationError
from .ledger import atomic_write
from .paths import normalize_relative, resolve_inside


def run_process_tree(
    argv: list[str],
    *,
    cwd: Path,
    timeout_seconds: int,
) -> tuple[subprocess.CompletedProcess[bytes], bool]:
    """Run a process with a timeout and terminate descendants on timeout."""

    kwargs: dict[str, Any] = {
        "cwd": cwd,
        "stdin": subprocess.DEVNULL,
        "stdout": subprocess.PIPE,
        "stderr": subprocess.PIPE,
        "shell": False,
    }
    if os.name == "nt":
        kwargs["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP
    else:
        kwargs["start_new_session"] = True
    process = subprocess.Popen(argv, **kwargs)
    try:
        stdout, stderr = process.communicate(timeout=timeout_seconds)
        return subprocess.CompletedProcess(argv, process.returncode, stdout, stderr), False
    except subprocess.TimeoutExpired:
        _kill_process_tree(process)
        try:
            stdout, stderr = process.communicate(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            stdout, stderr = process.communicate()
        return subprocess.CompletedProcess(argv, None, stdout or b"", stderr or b""), True


def _kill_process_tree(process: subprocess.Popen[bytes]) -> None:
    if os.name == "nt":
        subprocess.run(
            ["taskkill", "/PID", str(process.pid), "/T", "/F"],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
            shell=False,
        )
        return
    try:
        os.killpg(os.getpgid(process.pid), signal.SIGKILL)
    except ProcessLookupError:
        return


@dataclass(frozen=True)
class ExecutableBinding:
    """固定可执行文件及其允许的 argv Prefix。"""

    binding_id: str
    path: Path
    digest: str
    argv_prefix: tuple[str, ...] = ()


class ReferencePort:
    """提供确定性 Receipt 的本地参考 Port；它本身不代表平台隔离。"""

    def __init__(
        self,
        root: Path,
        *,
        executables: list[ExecutableBinding] | None = None,
        proposer: Callable[[dict[str, Any]], dict[str, Any]] | None = None,
    ) -> None:
        self.root = root.resolve()
        self.executables = {item.binding_id: item for item in executables or []}
        self.proposer = proposer

    def enumerate_files(self, include: list[str], exclude: list[str]) -> dict[str, Any]:
        manifest = build_manifest(self.root, include=include, exclude=exclude)
        return {
            "schema_version": "yuan.port-receipt/v1",
            "kind": "enumerate-files",
            "status": "OBSERVED",
            "artifact_digest": manifest["digest"],
            "file_count": manifest["file_count"],
            "manifest": manifest,
        }

    def read_bytes(self, relative: str, *, max_bytes: int = 8_000_000) -> tuple[bytes, dict[str, Any]]:
        target = resolve_inside(self.root, relative)
        if target.is_symlink() or not target.is_file():
            raise ValidationError("Port Read Target 不是安全的 Regular File")
        payload = target.read_bytes()
        if len(payload) > max_bytes:
            raise ValidationError("Port Read 超出 Byte Budget")
        return payload, {
            "schema_version": "yuan.port-receipt/v1",
            "kind": "read-file",
            "status": "OBSERVED",
            "path": normalize_relative(relative),
            "bytes": len(payload),
            "digest": digest_bytes(payload),
        }

    def atomic_write(
        self,
        relative: str,
        payload: bytes,
        *,
        expected_before: str | None,
    ) -> dict[str, Any]:
        if not isinstance(payload, bytes):
            raise TypeError("Port atomic_write 只接受 bytes")
        target = resolve_inside(self.root, relative)
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.is_symlink() or (target.exists() and not target.is_file()):
            raise ValidationError("Port Write Target 不是安全的 Regular File")
        before = digest_bytes(target.read_bytes()) if target.exists() else None
        if before != expected_before:
            raise IntegrityError("Port Write CAS 不匹配")
        atomic_write(target, payload)
        after = digest_bytes(target.read_bytes())
        if after != digest_bytes(payload):
            raise IntegrityError("Port Write 后验证失败")
        return {
            "schema_version": "yuan.port-receipt/v1",
            "kind": "write-file",
            "status": "COMMITTED",
            "path": normalize_relative(relative),
            "before_digest": before,
            "after_digest": after,
            "bytes": len(payload),
        }

    def run_command(
        self,
        binding_id: str,
        args: list[str],
        *,
        timeout_seconds: int,
        max_output_bytes: int = 2_000_000,
    ) -> dict[str, Any]:
        binding = self.executables.get(binding_id)
        if binding is None:
            raise ValidationError("Command Executable 未预绑定")
        executable = binding.path.resolve()
        if not executable.is_file() or digest_bytes(executable.read_bytes()) != binding.digest:
            raise IntegrityError("Command Executable Digest 不匹配")
        if not isinstance(timeout_seconds, int) or timeout_seconds <= 0 or timeout_seconds > 600:
            raise ValidationError("Command Timeout 不合法")
        if not isinstance(args, list) or not all(isinstance(item, str) for item in args):
            raise ValidationError("Command args 必须是 String Array")
        if binding.argv_prefix and tuple(args[: len(binding.argv_prefix)]) != binding.argv_prefix:
            raise ValidationError("Command argv 不符合预绑定 Profile")
        for item in args:
            candidate = Path(item)
            if candidate.is_absolute():
                try:
                    candidate.resolve().relative_to(self.root)
                except ValueError as exc:
                    raise ValidationError("Command argv 包含 Root 外 Absolute Path") from exc
        started = time.monotonic()
        result, timed_out = run_process_tree(
            [str(executable), *args],
            cwd=self.root,
            timeout_seconds=timeout_seconds,
        )
        duration_ms = int((time.monotonic() - started) * 1000)
        stdout = (result.stdout or b"")[:max_output_bytes]
        stderr = (result.stderr or b"")[:max_output_bytes]
        return {
            "schema_version": "yuan.port-receipt/v1",
            "kind": "run-command",
            "status": "TIMEOUT" if timed_out else "OBSERVED",
            "binding_id": binding_id,
            "argv": list(args),
            "exit_code": None if timed_out else result.returncode,
            "duration_ms": duration_ms,
            "stdout_digest": digest_bytes(stdout),
            "stderr_digest": digest_bytes(stderr),
            "stdout_truncated": len(result.stdout or b"") > max_output_bytes,
            "stderr_truncated": len(result.stderr or b"") > max_output_bytes,
        }

    def propose(self, request: dict[str, Any]) -> dict[str, Any]:
        if self.proposer is None:
            raise ValidationError("LLM Proposal Capability 为 UNSUPPORTED")
        proposal = self.proposer(request)
        if not isinstance(proposal, dict):
            raise ValidationError("LLM Provider 必须返回 JSON Object")
        return {
            "schema_version": "yuan.port-receipt/v1",
            "kind": "llm-proposal",
            "status": "PROPOSED",
            "request_digest": digest(request),
            "proposal_digest": digest(proposal),
            "proposal": proposal,
        }


def port_source_digest() -> str:
    return digest_bytes(Path(__file__).read_bytes())
