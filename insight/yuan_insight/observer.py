"""Yuan Insight Observation Service。

这是可选 Sidecar 的唯一观察生命周期：CLI watch 与 Dashboard 共用同一
Service，避免 Coverage、Trace、Gap 和 History 各自实现一套。
"""

from __future__ import annotations

import json
import threading
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from .diff import diff_snapshots, to_transition
from .loader import Snapshot, build_snapshot
from .trace import (
    append_transition,
    archive_trace,
    ensure_insight_dir,
    prune_traces,
    record_gap,
    start_session,
    update_session,
)
from .watcher import DebouncedWatcher


def _utc_now() -> str:
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _read_json(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        return {}
    return value if isinstance(value, dict) else {}


def read_transitions(path: Path) -> list[dict[str, Any]]:
    transitions: list[dict[str, Any]] = []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeError):
        return transitions
    for line in lines:
        if not line.strip():
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict):
            transitions.append(value)
    return transitions


@dataclass
class ObservationEvidence:
    coverage: str
    transitions: list[dict[str, Any]]
    current_work_id: str | None
    session_id: str | None
    gaps: list[dict[str, Any]]


@dataclass
class ObservationUpdate:
    snapshot: Snapshot
    transition: dict[str, Any] | None = None
    trace_path: Path | None = None
    archived_path: Path | None = None
    pruned: list[str] | None = None


def load_observation_evidence(root: Path) -> ObservationEvidence:
    insight_dir = root / ".yuan" / "insight"
    cache = _read_json(insight_dir / "cache" / "current.json")
    transitions = read_transitions(insight_dir / "traces" / "current.jsonl")
    session_id = cache.get("session_id")
    gaps: list[dict[str, Any]] = []
    if session_id:
        gaps = read_transitions(insight_dir / "gaps" / f"{session_id}.jsonl")
    return ObservationEvidence(
        coverage=str(cache.get("coverage") or "UNKNOWN"),
        transitions=transitions,
        current_work_id=cache.get("current_work_id"),
        session_id=session_id,
        gaps=gaps,
    )


class ObservationService:
    """Polling + debounce + semantic diff + durable observation lifecycle。"""

    def __init__(
        self,
        root: Path,
        poll_interval: float = 0.5,
        debounce_window: float = 0.4,
    ) -> None:
        self.root = root.resolve()
        self.poll_interval = poll_interval
        self.debounce_window = debounce_window
        self.insight_dir = ensure_insight_dir(self.root)
        self.cache_path = self.insight_dir / "cache" / "current.json"
        self.session_id: str | None = None
        self.coverage = "UNKNOWN"
        self.current_work_id: str | None = None
        self.previous: Snapshot | None = None
        self.latest_snapshot: Snapshot | None = None
        self.transition_index = 0
        self.watcher: DebouncedWatcher | None = None
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self._lock = threading.RLock()

    def start(self) -> Snapshot:
        with self._lock:
            if self.previous is not None:
                return self.previous
            baseline = build_snapshot(self.root, _utc_now())
            previous_cache = _read_json(self.cache_path)
            self.insight_dir, self.session_id = start_session(self.root, baseline)
            self.current_work_id = baseline.status.get("work")
            self.coverage = "PARTIAL" if self.current_work_id else "FULL"

            gap_start = previous_cache.get("last_observed_at")
            if gap_start and gap_start != baseline.observed_at:
                record_gap(
                    self.insight_dir,
                    self.session_id,
                    str(gap_start),
                    baseline.observed_at,
                )
                if self.current_work_id:
                    self.coverage = "PARTIAL"

            stale_work = previous_cache.get("current_work_id")
            if stale_work and not self.current_work_id:
                archive_trace(
                    self.insight_dir,
                    str(stale_work),
                    coverage="PARTIAL",
                    gaps=self._current_gaps(),
                )

            self.previous = baseline
            self.latest_snapshot = baseline
            self.transition_index = len(
                read_transitions(self.insight_dir / "traces" / "current.jsonl")
            )
            self.watcher = DebouncedWatcher(
                self.root,
                poll_interval=self.poll_interval,
                debounce_window=self.debounce_window,
            )
            self.watcher.tick()  # 建立 file hash baseline
            self._write_cache(baseline.observed_at, status="active")
            update_session(
                self.insight_dir,
                self.session_id,
                coverage=self.coverage,
                baseline_work_id=self.current_work_id,
                last_observed_at=baseline.observed_at,
            )
            return baseline

    def poll_once(self) -> ObservationUpdate | None:
        with self._lock:
            if self.previous is None or self.watcher is None:
                self.start()
            assert self.previous is not None
            assert self.watcher is not None
            event = self.watcher.tick()
            if event is None:
                return None

            before = self.previous
            after = event.snapshot
            before_work = self.current_work_id or before.status.get("work")
            after_work = after.status.get("work")
            facts = diff_snapshots(before, after)
            transition: dict[str, Any] | None = None
            trace_path: Path | None = None
            archived: Path | None = None
            pruned: list[str] = []

            if facts:
                self.transition_index += 1
                transition = to_transition(
                    transition_id=f"T-{self.transition_index:04d}",
                    session_id=self.session_id or "UNKNOWN",
                    observed_at=after.observed_at,
                    before=before,
                    after=after,
                    facts=facts,
                )
                transition["work_id"] = before_work or after_work
                trace_path = append_transition(self.insight_dir, transition)

            if before_work and after_work != before_work:
                archived = archive_trace(
                    self.insight_dir,
                    str(before_work),
                    coverage=self.coverage,
                    gaps=self._current_gaps(),
                )
                pruned = prune_traces(self.insight_dir, keep=50)

            if after_work and after_work != before_work:
                # 在 Observer 活跃期间观察到新 Work 起点，其 Coverage 为 FULL。
                self.coverage = "FULL"
            elif not after_work:
                self.coverage = "FULL"

            self.current_work_id = str(after_work) if after_work else None
            self.previous = after
            self.latest_snapshot = after
            self._write_cache(after.observed_at, status="active")
            if self.session_id:
                update_session(
                    self.insight_dir,
                    self.session_id,
                    coverage=self.coverage,
                    current_work_id=self.current_work_id,
                    last_observed_at=after.observed_at,
                )
            return ObservationUpdate(
                snapshot=after,
                transition=transition,
                trace_path=trace_path,
                archived_path=archived,
                pruned=pruned,
            )

    def evidence(self) -> ObservationEvidence:
        with self._lock:
            transitions = read_transitions(
                self.insight_dir / "traces" / "current.jsonl"
            )
            gaps = self._current_gaps()
            return ObservationEvidence(
                coverage=self.coverage,
                transitions=transitions,
                current_work_id=self.current_work_id,
                session_id=self.session_id,
                gaps=gaps,
            )

    def _current_gaps(self) -> list[dict[str, Any]]:
        return (
            read_transitions(
                self.insight_dir / "gaps" / f"{self.session_id}.jsonl"
            )
            if self.session_id
            else []
        )

    def start_background(self) -> Snapshot:
        baseline = self.start()
        if self._thread and self._thread.is_alive():
            return baseline
        self._stop.clear()
        self._thread = threading.Thread(
            target=self._background_loop,
            name="yuan-insight-observer",
            daemon=True,
        )
        self._thread.start()
        return baseline

    def _background_loop(self) -> None:
        while not self._stop.wait(self.poll_interval):
            self.poll_once()

    def run_forever(
        self,
        on_update: Callable[[ObservationUpdate], None] | None = None,
    ) -> None:
        self.start()
        try:
            while not self._stop.is_set():
                update = self.poll_once()
                if update and on_update:
                    on_update(update)
                time.sleep(self.poll_interval)
        finally:
            self.stop()

    def stop(self) -> None:
        self._stop.set()
        thread = self._thread
        if thread and thread.is_alive() and thread is not threading.current_thread():
            thread.join(timeout=max(2.0, self.poll_interval * 4))
        with self._lock:
            observed_at = _utc_now()
            self._write_cache(observed_at, status="stopped")
            if self.session_id:
                update_session(
                    self.insight_dir,
                    self.session_id,
                    status="stopped",
                    ended_at=observed_at,
                    last_observed_at=observed_at,
                    coverage=self.coverage,
                    current_work_id=self.current_work_id,
                )

    def _write_cache(self, observed_at: str, status: str) -> None:
        self.cache_path.parent.mkdir(parents=True, exist_ok=True)
        self.cache_path.write_text(
            json.dumps(
                {
                    "session_id": self.session_id,
                    "coverage": self.coverage,
                    "current_work_id": self.current_work_id,
                    "last_observed_at": observed_at,
                    "status": status,
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
