"""File Watcher + Debounce。

方案 §28：Insight 通过文件变化监听动态观察，不用心跳；Conductor 一次语义更新
可能修改 WORK 和 STATUS 两个文件，debounce 后合并为一个 Snapshot Diff。
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from pathlib import Path

from .loader import Snapshot, build_snapshot, collect_project_files


@dataclass
class WatchEvent:
    snapshot: Snapshot
    changed: list[str] = field(default_factory=list)


class DebouncedWatcher:
    """轮询被观察文件 hash，稳定后生成新 Snapshot。"""

    def __init__(
        self,
        root: Path,
        poll_interval: float = 0.5,
        debounce_window: float = 0.4,
        now: callable | None = None,  # type: ignore[type-arg]
    ) -> None:
        self.root = root
        self.poll_interval = poll_interval
        self.debounce_window = debounce_window
        self._now = now or time.time
        self._last_files: dict[str, str] | None = None
        self._pending_changed: list[str] = []
        self._quiet_since: float | None = None

    def _files_changed(self) -> list[str]:
        current = collect_project_files(self.root)
        changed: list[str] = []
        if self._last_files is not None:
            changed = [
                path for path in sorted(set(current) | set(self._last_files))
                if current.get(path) != self._last_files.get(path)
            ]
        self._last_files = current
        return changed

    def tick(self) -> WatchEvent | None:
        """一次轮询。文件变化后在 debounce 窗口内保持安静则产出 Snapshot；否则继续等待。"""
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
