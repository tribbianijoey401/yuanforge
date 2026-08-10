"""Native File Watch + Debounce。

Insight 优先使用操作系统文件事件；Conductor 一次语义更新可能修改 WORK 和
STATUS 两个文件，debounce 后合并为一个 Snapshot Diff。原生监听不可用时才
显式降级为 hash polling。
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from pathlib import Path

from .fswatch import FileEventSource, create_event_source
from .loader import Snapshot, build_snapshot, collect_project_files
from .loader import WATCHED_DOCS


@dataclass
class WatchEvent:
    snapshot: Snapshot
    changed: list[str] = field(default_factory=list)


class DebouncedWatcher:
    """原生事件唤醒、hash 确认、稳定后生成语义 Snapshot。"""

    def __init__(
        self,
        root: Path,
        poll_interval: float = 0.5,
        debounce_window: float = 0.05,
        now: callable | None = None,  # type: ignore[type-arg]
        prefer_native: bool = True,
    ) -> None:
        self.root = root
        self.poll_interval = poll_interval
        self.debounce_window = debounce_window
        self._now = now or time.time
        self._last_files: dict[str, str] | None = None
        self._pending_changed: list[str] = []
        self._quiet_since: float | None = None
        self._source: FileEventSource | None = (
            create_event_source(root, WATCHED_DOCS) if prefer_native else None
        )
        self.mode = self._source.mode if self._source else "polling-fallback"

    def prime(self, files: dict[str, str]) -> None:
        """Use an already-built Snapshot as the hash baseline.

        Native events are intentionally not drained here: a write racing with
        baseline construction must be compared with that Snapshot on the next
        tick instead of being silently discarded.
        """
        if self._last_files is None:
            self._last_files = dict(files)

    def _files_changed(self) -> list[str]:
        # Establish the hash baseline before native events gate file reads.
        # Otherwise the first real transition after startup would only
        # initialise the hashes and its state change would be lost.
        if self._last_files is None:
            self._last_files = collect_project_files(self.root)
            if self._source is not None:
                self._source.drain()
            return []

        if self._source is not None:
            if not self._source.healthy:
                self._source.close()
                self._source = None
                self.mode = "polling-fallback"
            elif not self._source.drain():
                return []
        current = collect_project_files(self.root)
        changed = [
            path for path in sorted(set(current) | set(self._last_files))
            if current.get(path) != self._last_files.get(path)
        ]
        self._last_files = current
        return changed

    @property
    def native(self) -> bool:
        return self._source is not None and self._source.healthy

    def wait(self) -> None:
        """等待原生事件或下一次 debounce/polling 检查。"""
        timeout = self.poll_interval
        if self._pending_changed and self._quiet_since is not None:
            remaining = self.debounce_window - (self._now() - self._quiet_since)
            timeout = max(0.0, min(timeout, remaining))
        if self._source is not None:
            self._source.wait(timeout)
        elif timeout > 0:
            time.sleep(timeout)

    def close(self) -> None:
        if self._source is not None:
            self._source.close()
            self._source = None

    def tick(self) -> WatchEvent | None:
        """处理一次事件。文件稳定超过 debounce 窗口后产出 Snapshot。"""
        changed = self._files_changed()
        now = self._now()
        if changed:
            self._pending_changed.extend(changed)
            self._quiet_since = now
            return None
        if self._pending_changed and self._quiet_since is not None:
            if now - self._quiet_since >= self.debounce_window:
                snapshot = build_snapshot(self.root, f"{now:.6f}")
                event = WatchEvent(snapshot=snapshot, changed=sorted(set(self._pending_changed)))
                self._pending_changed = []
                self._quiet_since = None
                return event
        return None
