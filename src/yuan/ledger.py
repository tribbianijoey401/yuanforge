"""具有 Atomic Head 更新的不可变内容寻址 JSON Ledger。"""

from __future__ import annotations

import json
import os
import time
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator

from .canonical import canonical_bytes, digest, digest_bytes, verify_digest
from .errors import IntegrityError


_ANY_HEAD = object()


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def atomic_write(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    with temporary.open("xb") as stream:
        stream.write(payload)
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temporary, path)


def _process_alive(pid: int) -> bool:
    if pid <= 0:
        return False
    if pid == os.getpid():
        return True
    if os.name == "nt":
        import ctypes

        kernel32 = ctypes.windll.kernel32
        handle = kernel32.OpenProcess(0x1000, False, pid)
        if not handle:
            return kernel32.GetLastError() != 87
        exit_code = ctypes.c_ulong()
        try:
            return bool(kernel32.GetExitCodeProcess(handle, ctypes.byref(exit_code))) and exit_code.value == 259
        finally:
            kernel32.CloseHandle(handle)
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def _lock_is_stale(path: Path, stale_lock_seconds: float) -> bool:
    try:
        pid = int(path.read_text(encoding="ascii").strip())
    except (OSError, UnicodeError, ValueError):
        try:
            return time.time() - path.stat().st_mtime >= stale_lock_seconds
        except FileNotFoundError:
            return False
    return not _process_alive(pid)


@contextmanager
def exclusive_lock(path: Path, timeout: float = 5.0, stale_lock_seconds: float = 60.0) -> Iterator[None]:
    deadline = time.monotonic() + timeout
    path.parent.mkdir(parents=True, exist_ok=True)
    while True:
        try:
            descriptor = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            break
        except FileExistsError:
            if _lock_is_stale(path, stale_lock_seconds):
                try:
                    path.unlink()
                except FileNotFoundError:
                    pass
                continue
            if time.monotonic() >= deadline:
                raise IntegrityError("Ledger Lock 超时")
            time.sleep(0.02)
    try:
        os.write(descriptor, str(os.getpid()).encode("ascii"))
        os.close(descriptor)
        yield
    finally:
        try:
            path.unlink()
        except FileNotFoundError:
            pass


class Ledger:
    def __init__(self, state_root: Path, run_id: str):
        self.state_root = state_root.resolve()
        self.run_id = run_id
        self.run_root = self.state_root / "runs" / run_id
        self.events_root = self.run_root / "events"
        self.head_path = self.run_root / "head.json"
        self.lock_path = self.run_root / ".append.lock"
        self.blob_root = self.state_root / "blobs" / "sha256"

    def put_blob(self, payload: bytes) -> str:
        value = digest_bytes(payload)
        path = self.blob_root / value[:2] / value[2:]
        if path.exists():
            if path.read_bytes() != payload:
                raise IntegrityError("Blob Digest 冲突或内容损坏")
            return value
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
        try:
            with temporary.open("xb") as stream:
                stream.write(payload)
                stream.flush()
                os.fsync(stream.fileno())
            try:
                os.link(temporary, path)
                temporary.unlink()
            except (FileExistsError, OSError):
                if not path.exists():
                    os.replace(temporary, path)
                elif temporary.exists():
                    temporary.unlink()
        finally:
            if temporary.exists():
                temporary.unlink()
        if path.read_bytes() != payload:
            raise IntegrityError("Blob 写后验证失败")
        return value

    def get_blob(self, value: str) -> bytes:
        path = self.blob_root / value[:2] / value[2:]
        try:
            payload = path.read_bytes()
        except OSError as exc:
            raise IntegrityError(f"Blob 缺失：{value}") from exc
        if digest_bytes(payload) != value:
            raise IntegrityError(f"Blob 损坏：{value}")
        return payload

    def _head(self) -> dict[str, Any] | None:
        if not self.head_path.exists():
            return None
        try:
            value = json.loads(self.head_path.read_text(encoding="utf-8"))
        except (OSError, UnicodeError, json.JSONDecodeError) as exc:
            raise IntegrityError("Ledger Head 不合法") from exc
        if set(value) != {"sequence", "event_digest"}:
            raise IntegrityError("Ledger Head 结构不合法")
        return value

    def append(
        self,
        event_type: str,
        payload: dict[str, Any],
        *,
        expected_head: str | None | object = _ANY_HEAD,
    ) -> dict[str, Any]:
        with exclusive_lock(self.lock_path):
            head = self._head()
            actual_head = None if head is None else head["event_digest"]
            if expected_head is not _ANY_HEAD and expected_head != actual_head:
                raise IntegrityError("Ledger Head CAS 失败，状态已被其他 Transition 推进")
            sequence = 1 if head is None else head["sequence"] + 1
            previous = None if head is None else head["event_digest"]
            event = {
                "schema_version": "yuan.event/v1",
                "run_id": self.run_id,
                "sequence": sequence,
                "previous": previous,
                "type": event_type,
                "created_at": utc_now(),
                "payload": payload,
            }
            event["digest"] = digest(event, ("digest",))
            path = self.events_root / f"{sequence:08d}-{event['digest']}.json"
            if path.exists():
                raise IntegrityError("Event Identity 已存在")
            atomic_write(path, canonical_bytes(event))
            atomic_write(
                self.head_path,
                canonical_bytes({"sequence": sequence, "event_digest": event["digest"]}),
            )
            return event

    def events(self) -> list[dict[str, Any]]:
        if not self.events_root.exists():
            return []
        paths = sorted(self.events_root.glob("*.json"))
        result = []
        previous = None
        for sequence, path in enumerate(paths, start=1):
            try:
                event = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, UnicodeError, json.JSONDecodeError) as exc:
                raise IntegrityError(f"Event 文件不合法：{path.name}") from exc
            expected_name = f"{sequence:08d}-{event.get('digest')}.json"
            if (
                path.name != expected_name
                or set(event) != {"schema_version", "run_id", "sequence", "previous", "type", "created_at", "payload", "digest"}
                or event.get("schema_version") != "yuan.event/v1"
                or event.get("run_id") != self.run_id
                or event.get("sequence") != sequence
                or event.get("previous") != previous
                or not isinstance(event.get("type"), str)
                or not isinstance(event.get("created_at"), str)
                or not isinstance(event.get("payload"), dict)
                or not verify_digest(event)
            ):
                raise IntegrityError(f"Event Chain 在 Sequence {sequence} 不匹配")
            result.append(event)
            previous = event["digest"]
        head = self._head()
        expected = None if not result else {"sequence": len(result), "event_digest": result[-1]["digest"]}
        if head != expected:
            raise IntegrityError("Ledger Head 与 Event Chain 不匹配")
        return result

    def recover_head(self, *, stale_lock_seconds: float = 60.0, force: bool = False) -> dict[str, Any]:
        """恢复写入不可变 Event 后中断的 Head 更新；近期 Lock 默认不破坏。"""
        if self.lock_path.exists():
            age = time.time() - self.lock_path.stat().st_mtime
            if not force and age < stale_lock_seconds:
                raise IntegrityError("Ledger Lock 可能仍处于 Active 状态")
            self.lock_path.unlink()
        paths = sorted(self.events_root.glob("*.json")) if self.events_root.exists() else []
        previous = None
        last = None
        for sequence, path in enumerate(paths, start=1):
            try:
                event = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, UnicodeError, json.JSONDecodeError) as exc:
                raise IntegrityError(f"Event 文件不合法：{path.name}") from exc
            if (
                path.name != f"{sequence:08d}-{event.get('digest')}.json"
                or event.get("sequence") != sequence
                or event.get("run_id") != self.run_id
                or event.get("previous") != previous
                or not verify_digest(event)
            ):
                raise IntegrityError(f"无法恢复 Sequence {sequence} 的非法 Event Chain")
            previous = event["digest"]
            last = event
        expected = None if last is None else {"sequence": last["sequence"], "event_digest": last["digest"]}
        if expected is None:
            if self.head_path.exists():
                raise IntegrityError("没有 Event 时不应存在 Head")
            return {"status": "UNCHANGED", "sequence": 0}
        atomic_write(self.head_path, canonical_bytes(expected))
        self.events()
        return {"status": "RECOVERED", **expected}
