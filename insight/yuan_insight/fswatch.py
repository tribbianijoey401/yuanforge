"""跨平台文件系统事件源。

Insight 优先使用操作系统原生目录通知；无法建立原生监听时由上层显式降级为
hash polling。事件源只负责唤醒，不解释 Yuan 语义，也不写 Project 文件。
"""

from __future__ import annotations

import os
import select
import struct
import sys
import threading
from pathlib import Path
from typing import Iterable


class FileEventSource:
    """原生目录事件的最小接口。"""

    mode = "native"

    def wait(self, timeout: float) -> bool:
        raise NotImplementedError

    def drain(self) -> bool:
        raise NotImplementedError

    @property
    def healthy(self) -> bool:
        raise NotImplementedError

    def close(self) -> None:
        raise NotImplementedError


class _ThreadedEventSource(FileEventSource):
    def __init__(self) -> None:
        self._changed = threading.Event()
        self._stop = threading.Event()
        self._ready = threading.Event()
        self._failure: BaseException | None = None
        self._thread: threading.Thread | None = None

    def _start(self, name: str) -> None:
        self._thread = threading.Thread(target=self._run, name=name, daemon=True)
        self._thread.start()
        if not self._ready.wait(timeout=2.0):
            self.close()
            raise RuntimeError(f"{self.mode} watcher 未能启动")
        if self._failure is not None:
            failure = self._failure
            self.close()
            raise RuntimeError(f"{self.mode} watcher 启动失败") from failure

    def _run(self) -> None:
        raise NotImplementedError

    def _notify(self) -> None:
        self._changed.set()

    def wait(self, timeout: float) -> bool:
        return self._changed.wait(max(0.0, timeout))

    def drain(self) -> bool:
        changed = self._changed.is_set()
        self._changed.clear()
        return changed

    @property
    def healthy(self) -> bool:
        return self._failure is None and not (
            self._thread is not None
            and not self._thread.is_alive()
            and not self._stop.is_set()
        )

    def _join(self) -> None:
        thread = self._thread
        if thread and thread.is_alive() and thread is not threading.current_thread():
            thread.join(timeout=2.0)


class WindowsFileEventSource(_ThreadedEventSource):
    """ReadDirectoryChangesW 事件源。"""

    mode = "native-windows"

    def __init__(self, root: Path, watched: Iterable[str]) -> None:
        if sys.platform != "win32":
            raise OSError("ReadDirectoryChangesW 仅适用于 Windows")
        super().__init__()
        import ctypes
        from ctypes import wintypes

        self._ctypes = ctypes
        self._wintypes = wintypes
        self._watched = {path.replace("\\", "/") for path in watched}
        self._kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
        self._kernel32.CreateFileW.argtypes = (
            wintypes.LPCWSTR,
            wintypes.DWORD,
            wintypes.DWORD,
            wintypes.LPVOID,
            wintypes.DWORD,
            wintypes.DWORD,
            wintypes.HANDLE,
        )
        self._kernel32.CreateFileW.restype = wintypes.HANDLE
        self._kernel32.ReadDirectoryChangesW.argtypes = (
            wintypes.HANDLE,
            wintypes.LPVOID,
            wintypes.DWORD,
            wintypes.BOOL,
            wintypes.DWORD,
            ctypes.POINTER(wintypes.DWORD),
            wintypes.LPVOID,
            wintypes.LPVOID,
        )
        self._kernel32.ReadDirectoryChangesW.restype = wintypes.BOOL
        self._kernel32.CancelIoEx.argtypes = (wintypes.HANDLE, wintypes.LPVOID)
        self._kernel32.CancelIoEx.restype = wintypes.BOOL
        self._kernel32.CloseHandle.argtypes = (wintypes.HANDLE,)
        self._kernel32.CloseHandle.restype = wintypes.BOOL

        file_list_directory = 0x0001
        share = 0x0001 | 0x0002 | 0x0004
        open_existing = 3
        backup_semantics = 0x02000000
        self._handle = self._kernel32.CreateFileW(
            str(root.resolve()),
            file_list_directory,
            share,
            None,
            open_existing,
            backup_semantics,
            None,
        )
        invalid = wintypes.HANDLE(-1).value
        if self._handle == invalid:
            raise ctypes.WinError(ctypes.get_last_error())
        self._closed = False
        self._start("yuan-insight-read-directory-changes")

    def _run(self) -> None:
        ctypes = self._ctypes
        wintypes = self._wintypes
        buffer = ctypes.create_string_buffer(64 * 1024)
        returned = wintypes.DWORD()
        notify_filter = 0x0001 | 0x0002 | 0x0004 | 0x0008 | 0x0010 | 0x0040
        self._ready.set()
        try:
            while not self._stop.is_set():
                ok = self._kernel32.ReadDirectoryChangesW(
                    self._handle,
                    buffer,
                    len(buffer),
                    True,
                    notify_filter,
                    ctypes.byref(returned),
                    None,
                    None,
                )
                if not ok:
                    error = ctypes.get_last_error()
                    if self._stop.is_set() or error in (6, 995):
                        break
                    raise ctypes.WinError(error)
                payload = buffer.raw[: returned.value]
                offset = 0
                while offset + 12 <= len(payload):
                    next_offset, _action, name_length = struct.unpack_from("<III", payload, offset)
                    name_start = offset + 12
                    name = payload[name_start : name_start + name_length].decode(
                        "utf-16-le", errors="replace"
                    )
                    if name.replace("\\", "/") in self._watched:
                        self._notify()
                    if next_offset == 0:
                        break
                    offset += next_offset
        except BaseException as exc:
            if not self._stop.is_set():
                self._failure = exc
                self._notify()
        finally:
            self._ready.set()

    def close(self) -> None:
        if getattr(self, "_closed", True):
            return
        self._closed = True
        self._stop.set()
        self._kernel32.CancelIoEx(self._handle, None)
        self._kernel32.CloseHandle(self._handle)
        self._changed.set()
        self._join()


class LinuxFileEventSource(_ThreadedEventSource):
    """inotify 事件源，只监听 Project docs 目录。"""

    mode = "native-inotify"

    def __init__(self, root: Path, watched: Iterable[str]) -> None:
        if not sys.platform.startswith("linux"):
            raise OSError("inotify 仅适用于 Linux")
        docs = root.resolve() / "docs"
        if not docs.is_dir():
            raise OSError(f"docs 目录不存在：{docs}")
        super().__init__()
        import ctypes

        self._ctypes = ctypes
        self._libc = ctypes.CDLL(None, use_errno=True)
        self._libc.inotify_init1.argtypes = (ctypes.c_int,)
        self._libc.inotify_init1.restype = ctypes.c_int
        self._libc.inotify_add_watch.argtypes = (ctypes.c_int, ctypes.c_char_p, ctypes.c_uint32)
        self._libc.inotify_add_watch.restype = ctypes.c_int
        self._watched_names = {
            Path(path).name for path in watched if path.replace("\\", "/").startswith("docs/")
        }
        self._fd = self._libc.inotify_init1(os.O_NONBLOCK | getattr(os, "O_CLOEXEC", 0))
        if self._fd < 0:
            raise OSError(ctypes.get_errno(), "inotify_init1 failed")
        mask = 0x00000004 | 0x00000008 | 0x00000080 | 0x00000100 | 0x00000200
        self._watch_descriptor = self._libc.inotify_add_watch(
            self._fd, os.fsencode(docs), mask
        )
        if self._watch_descriptor < 0:
            error = ctypes.get_errno()
            os.close(self._fd)
            raise OSError(error, "inotify_add_watch failed")
        self._closed = False
        self._start("yuan-insight-inotify")

    def _run(self) -> None:
        self._ready.set()
        try:
            while not self._stop.is_set():
                readable, _, _ = select.select([self._fd], [], [], 0.25)
                if not readable:
                    continue
                try:
                    payload = os.read(self._fd, 64 * 1024)
                except BlockingIOError:
                    continue
                offset = 0
                while offset + 16 <= len(payload):
                    _wd, _mask, _cookie, name_length = struct.unpack_from(
                        "iIII", payload, offset
                    )
                    name_start = offset + 16
                    raw_name = payload[name_start : name_start + name_length]
                    name = os.fsdecode(raw_name.split(b"\0", 1)[0])
                    if name in self._watched_names:
                        self._notify()
                    offset = name_start + name_length
        except BaseException as exc:
            if not self._stop.is_set():
                self._failure = exc
                self._notify()
        finally:
            self._ready.set()

    def close(self) -> None:
        if getattr(self, "_closed", True):
            return
        self._closed = True
        self._stop.set()
        try:
            os.close(self._fd)
        except OSError:
            pass
        self._changed.set()
        self._join()


def create_event_source(root: Path, watched: Iterable[str]) -> FileEventSource | None:
    """创建当前平台的原生事件源；不支持或启动失败时返回 None。"""
    try:
        if sys.platform == "win32":
            return WindowsFileEventSource(root, watched)
        if sys.platform.startswith("linux"):
            return LinuxFileEventSource(root, watched)
    except Exception:
        return None
    return None
