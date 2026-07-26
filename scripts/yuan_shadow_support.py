"""Fail-closed helpers for the Yuan legacy-to-Core shadow projection.

This module never selects runtime authority.  It reads legacy documents and
writes only to an explicitly separate shadow root.
"""

from __future__ import annotations

import hashlib
import json
import os
import pathlib
import re
import shutil
import sys
import tempfile
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Iterable


TOOL_REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
CORE_ROOT = TOOL_REPO_ROOT / ".yuan" / "core" / "0.1"
MIGRATOR_REVISION = "yuan.shadow-migrator/1"
EMPTY_SHA256 = hashlib.sha256(b"").hexdigest()
ENVIRONMENT_ID = "shadow-filesystem-v1"
ENVIRONMENT_FINGERPRINT = hashlib.sha256(
    b"yuan-shadow-filesystem-environment/v1"
).hexdigest()
LEGACY_NAMES = ("FEATURE.md", "PLAN.md", "TASK_BOARD.md", "SESSION_LOG.md", "SESSION.md")


class MigrationError(RuntimeError):
    """Raised when conversion cannot proceed without risking legacy state."""


class GuardError(MigrationError):
    """Raised when a writer crosses its declared authority lane or CAS fails."""


@dataclass
class LegacyWorkspace:
    workspace_id: str
    kind: str
    root: pathlib.Path
    documents: dict[str, pathlib.Path] = field(default_factory=dict)
    event_files: list[pathlib.Path] = field(default_factory=list)
    unresolved: list[dict[str, str]] = field(default_factory=list)


@dataclass
class LegacyScan:
    active_workspace_id: str | None
    workspaces: list[LegacyWorkspace]
    unresolved: list[dict[str, str]]


def canonical_json(value: Any) -> bytes:
    return (
        json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
        + "\n"
    ).encode("utf-8")


def canonical_digest(value: Any, *, omit: tuple[str, ...] = ()) -> str:
    if omit:
        value = json.loads(json.dumps(value, ensure_ascii=False))
        cursor = value
        for key in omit[:-1]:
            cursor = cursor[key]
        cursor.pop(omit[-1], None)
    return hashlib.sha256(canonical_json(value).rstrip(b"\n")).hexdigest()


def file_sha256(path: pathlib.Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _relative(path: pathlib.Path, root: pathlib.Path) -> str:
    return path.resolve().relative_to(root.resolve()).as_posix()


def _ensure_no_symlink_path(path: pathlib.Path, stop: pathlib.Path) -> None:
    current = path
    stop = stop.resolve()
    while True:
        if current.exists() and current.is_symlink():
            raise MigrationError(f"symlink path is not allowed: {current}")
        if current.resolve() == stop:
            break
        if current.parent == current:
            raise MigrationError(f"path escapes repository: {path}")
        current = current.parent


def safe_shadow_root(repo_root: pathlib.Path, shadow_root: pathlib.Path) -> pathlib.Path:
    repo = repo_root.resolve()
    shadow = shadow_root.resolve()
    try:
        relative = shadow.relative_to(repo)
    except ValueError as error:
        raise MigrationError("shadow root must be inside repository") from error
    if relative == pathlib.Path(".") or relative.parts[0].lower() in {
        "docs",
        ".git",
        ".yuan",
    }:
        raise MigrationError("shadow root overlaps repository authority or framework")
    _ensure_no_symlink_path(shadow, repo)
    return shadow


def _active_workspace_id(progress: pathlib.Path) -> str | None:
    if not progress.is_file():
        return None
    text = progress.read_text(encoding="utf-8")
    patterns = (
        r"\*\*当前会话\*\*[^\n]*\]\(\./([^/]+)/?\)",
        r"当前会话[^\n]*\]\(\./([^/]+)/?\)",
    )
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return match.group(1)
    return None


def _event_sessions(path: pathlib.Path) -> tuple[set[str], list[dict[str, str]]]:
    sessions: set[str] = set()
    unresolved: list[dict[str, str]] = []
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeError) as error:
        return sessions, [{"code": "EVENT_UNREADABLE", "source": str(path), "detail": str(error)}]
    for number, line in enumerate(lines, start=1):
        if not line.strip():
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError as error:
            unresolved.append(
                {
                    "code": "EVENT_INVALID_JSON",
                    "source": str(path),
                    "detail": f"line {number}: {error.msg}",
                }
            )
            continue
        session = record.get("session")
        if isinstance(session, str) and session:
            sessions.add(session)
        else:
            unresolved.append(
                {
                    "code": "EVENT_SESSION_MISSING",
                    "source": str(path),
                    "detail": f"line {number}",
                }
            )
    return sessions, unresolved


def discover_legacy(repo_root: pathlib.Path) -> LegacyScan:
    repo = repo_root.resolve()
    docs = repo / "docs"
    if not docs.is_dir():
        raise MigrationError("legacy docs root does not exist")
    active_id = _active_workspace_id(docs / "PROGRESS.md")
    candidates: dict[str, tuple[str, pathlib.Path]] = {}
    for child in sorted(docs.iterdir(), key=lambda item: item.name):
        if (
            child.is_dir()
            and child.name not in {"archive", "events", "knowledge", "workspace", "graph", "policies", "proposals", "decisions"}
            and any((child / name).is_file() for name in LEGACY_NAMES)
        ):
            candidates[child.name] = (
                "active" if child.name == active_id else "historical",
                child,
            )
    archive = docs / "archive"
    if archive.is_dir():
        for child in sorted(archive.iterdir(), key=lambda item: item.name):
            if child.is_dir() and any((child / name).is_file() for name in LEGACY_NAMES):
                candidates[child.name] = ("archive", child)

    event_index: dict[str, list[pathlib.Path]] = {}
    global_unresolved: list[dict[str, str]] = []
    if active_id is None:
        global_unresolved.append(
            {
                "code": "ACTIVE_POINTER_MISSING",
                "source": "docs/PROGRESS.md",
                "detail": "no active Workspace pointer could be parsed",
            }
        )
    events_root = docs / "events"
    if events_root.is_dir():
        for event_file in sorted(events_root.rglob("*.jsonl")):
            sessions, errors = _event_sessions(event_file)
            global_unresolved.extend(errors)
            for session in sessions:
                event_index.setdefault(session, []).append(event_file)

    workspaces: list[LegacyWorkspace] = []
    for workspace_id, (kind, root) in sorted(candidates.items()):
        documents = {
            name: root / name for name in LEGACY_NAMES if (root / name).is_file()
        }
        unresolved: list[dict[str, str]] = []
        for name, code in (
            ("FEATURE.md", "MISSING_FEATURE"),
            ("PLAN.md", "MISSING_PLAN"),
            ("TASK_BOARD.md", "MISSING_TASK_BOARD"),
        ):
            if name not in documents:
                unresolved.append(
                    {
                        "code": code,
                        "source": _relative(root, repo),
                        "detail": f"{name} is absent",
                    }
                )
        if not ({"SESSION_LOG.md", "SESSION.md"} & set(documents)):
            unresolved.append(
                {
                    "code": "MISSING_SESSION",
                    "source": _relative(root, repo),
                    "detail": "SESSION_LOG.md and SESSION.md are absent",
                }
            )
        event_files = sorted(event_index.get(workspace_id, []))
        if not event_files:
            unresolved.append(
                {
                    "code": "MISSING_EVENTS",
                    "source": _relative(root, repo),
                    "detail": "no session-bound JSONL events found",
                }
            )
        workspaces.append(
            LegacyWorkspace(
                workspace_id=workspace_id,
                kind=kind,
                root=root,
                documents=documents,
                event_files=event_files,
                unresolved=unresolved,
            )
        )
    if active_id and active_id not in candidates:
        global_unresolved.append(
            {
                "code": "ACTIVE_WORKSPACE_UNRECOGNIZED",
                "source": "docs/PROGRESS.md",
                "detail": active_id,
            }
        )
    return LegacyScan(active_id, workspaces, global_unresolved)


def source_manifest(repo_root: pathlib.Path, workspace: LegacyWorkspace) -> dict[str, Any]:
    repo = repo_root.resolve()
    paths = sorted(
        {*workspace.documents.values(), *workspace.event_files},
        key=lambda item: _relative(item, repo),
    )
    files = [
        {
            "path": _relative(path, repo),
            "sha256": file_sha256(path),
            "bytes": path.stat().st_size,
        }
        for path in paths
    ]
    manifest = {
        "schema_version": "yuan.legacy-source-manifest/v1",
        "workspace_id": workspace.workspace_id,
        "workspace_kind": workspace.kind,
        "workspace_root": _relative(workspace.root, repo),
        "files": files,
    }
    manifest["digest"] = canonical_digest(manifest)
    return manifest


def snapshot_digest(manifests: Iterable[dict[str, Any]]) -> str:
    return canonical_digest(
        [
            {"workspace_id": item["workspace_id"], "digest": item["digest"]}
            for item in sorted(manifests, key=lambda value: value["workspace_id"])
        ]
    )


def verify_source_manifests(repo_root: pathlib.Path, manifests: Iterable[dict[str, Any]]) -> None:
    repo = repo_root.resolve()
    for manifest in manifests:
        expected_manifest = dict(manifest)
        expected_digest = expected_manifest.pop("digest", None)
        if canonical_digest(expected_manifest) != expected_digest:
            raise MigrationError(
                f"source manifest digest mismatch: {manifest.get('workspace_id')}"
            )
        for item in manifest["files"]:
            path = repo / pathlib.PurePosixPath(item["path"])
            try:
                path.resolve().relative_to(repo)
            except ValueError as error:
                raise MigrationError(f"source path escapes repository: {item['path']}") from error
            if not path.is_file() or file_sha256(path) != item["sha256"]:
                raise MigrationError(f"legacy source changed: {item['path']}")


def _extract_section(text: str, heading: str) -> str | None:
    match = re.search(
        rf"^##\s+{re.escape(heading)}\s*$\n+(.*?)(?=^##\s+|\Z)",
        text,
        re.MULTILINE | re.DOTALL,
    )
    if not match:
        return None
    paragraphs = [
        item.strip()
        for item in re.split(r"\n\s*\n", match.group(1))
        if item.strip() and not item.lstrip().startswith("|")
    ]
    return paragraphs[0] if paragraphs else None


def _extract_goal(workspace: LegacyWorkspace) -> tuple[str, list[dict[str, str]]]:
    unresolved: list[dict[str, str]] = []
    feature = workspace.documents.get("FEATURE.md")
    if feature:
        text = feature.read_text(encoding="utf-8")
        goal = _extract_section(text, "用户意图")
        if goal:
            return goal, unresolved
    plan = workspace.documents.get("PLAN.md")
    if plan:
        text = plan.read_text(encoding="utf-8")
        match = re.search(
            r"^-\s+\*\*目标:?\*\*\s*:?\s*(.+)$", text, re.MULTILINE
        )
        if match:
            return match.group(1).strip(), unresolved
    unresolved.append(
        {
            "code": "GOAL_UNRESOLVED",
            "source": workspace.workspace_id,
            "detail": "no verbatim user intent or Plan goal found",
        }
    )
    return f"Unresolved legacy intent for workspace {workspace.workspace_id}", unresolved


def _extract_legacy_acs(workspace: LegacyWorkspace) -> list[dict[str, str]]:
    feature = workspace.documents.get("FEATURE.md")
    if not feature:
        return []
    rows: list[dict[str, str]] = []
    for line in feature.read_text(encoding="utf-8").splitlines():
        cells = [item.strip() for item in line.strip().strip("|").split("|")]
        if (
            len(cells) >= 3
            and re.fullmatch(r"AC-[A-Za-z0-9._-]+", cells[0])
        ):
            rows.append(
                {
                    "legacy_ac_id": cells[0],
                    "predicate": cells[1],
                    "required_evidence": cells[2],
                }
            )
    return rows


def extract_legacy_records(
    repo_root: pathlib.Path, workspace: LegacyWorkspace
) -> list[dict[str, Any]]:
    """Extract task/event observations without treating status text as truth."""

    repo = repo_root.resolve()
    records: list[dict[str, Any]] = []
    board = workspace.documents.get("TASK_BOARD.md")
    if board:
        lines = board.read_text(encoding="utf-8").splitlines()
        for index, line in enumerate(lines):
            if not line.lstrip().startswith("|"):
                continue
            headers = [item.strip() for item in line.strip().strip("|").split("|")]
            id_column = next(
                (
                    position
                    for position, header in enumerate(headers)
                    if header in {"ID", "Task ID", "Task"}
                ),
                None,
            )
            status_column = next(
                (
                    position
                    for position, header in enumerate(headers)
                    if "状态" in header
                ),
                None,
            )
            if id_column is None or status_column is None or index + 1 >= len(lines):
                continue
            separator = lines[index + 1]
            if not separator.lstrip().startswith("|") or "---" not in separator:
                continue
            for line_number in range(index + 2, len(lines)):
                row_line = lines[line_number]
                if not row_line.lstrip().startswith("|"):
                    break
                cells = [
                    item.strip() for item in row_line.strip().strip("|").split("|")
                ]
                if max(id_column, status_column) >= len(cells):
                    continue
                task_id = cells[id_column]
                if not re.fullmatch(r"(?:task-\d+|T\d+)", task_id, re.IGNORECASE):
                    continue
                records.append(
                    {
                        "kind": "task-snapshot",
                        "source": _relative(board, repo),
                        "line": line_number + 1,
                        "task_id": task_id,
                        "observed_status": cells[status_column],
                        "cells": {
                            headers[position]: value
                            for position, value in enumerate(cells)
                            if position < len(headers)
                        },
                    }
                )
            break
    for event_file in workspace.event_files:
        for line_number, line in enumerate(
            event_file.read_text(encoding="utf-8").splitlines(), start=1
        ):
            if not line.strip():
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                continue
            if record.get("session") != workspace.workspace_id:
                continue
            records.append(
                {
                    "kind": "event-observation",
                    "source": _relative(event_file, repo),
                    "line": line_number,
                    "event": record,
                }
            )
    return sorted(
        records,
        key=lambda item: (
            item["source"],
            item["line"],
            item["kind"],
        ),
    )


def _binding(binding_id: str, revision: str, digest: str) -> dict[str, str]:
    return {"id": binding_id, "revision": revision, "sha256": digest}


def _core_bindings() -> tuple[dict[str, str], dict[str, str]]:
    protocol = CORE_ROOT / "protocol.md"
    protocol_binding = _binding(
        "yuan.core.protocol", "0.1.0-candidate", file_sha256(protocol)
    )
    harness_files = (
        pathlib.Path(__file__).resolve(),
        TOOL_REPO_ROOT / "scripts" / "yuan_shadow_migrate.py",
        TOOL_REPO_ROOT / ".yuan" / "migration" / "authority-pointer.schema.json",
    )
    harness_digest = canonical_digest(
        [
            {"path": path.name, "sha256": file_sha256(path)}
            for path in harness_files
            if path.is_file()
        ]
    )
    return protocol_binding, _binding(
        "yuan.shadow-migrator", MIGRATOR_REVISION, harness_digest
    )


def _work_id(workspace_id: str) -> str:
    date = re.match(r"(\d{8})", workspace_id)
    prefix = date.group(1) if date else "legacy"
    suffix = hashlib.sha256(workspace_id.encode("utf-8")).hexdigest()[:12]
    return f"legacy-{prefix}-{suffix}"


def build_work_contract(
    workspace: LegacyWorkspace,
    manifest: dict[str, Any],
    unresolved: list[dict[str, str]],
    *,
    replay_record_count: int = 0,
) -> dict[str, Any]:
    protocol_binding, harness_binding = _core_bindings()
    goal, goal_unresolved = _extract_goal(workspace)
    unresolved.extend(goal_unresolved)
    legacy_acs = _extract_legacy_acs(workspace)
    for ac in legacy_acs:
        unresolved.append(
            {
                "code": "AC_BINDING_UNRESOLVED",
                "source": workspace.workspace_id,
                "detail": (
                    f"{ac['legacy_ac_id']} preserved in replay report; "
                    "typed verifier binding absent from legacy source"
                ),
            }
        )
    verifier = {
        **harness_binding,
        "trust_root_id": "yuan-core-0.1-m3-approved",
        "environment_ids": [ENVIRONMENT_ID],
        "environment_fingerprints": {
            ENVIRONMENT_ID: ENVIRONMENT_FINGERPRINT
        },
        "minimum_assertions": 1,
    }
    work_id = _work_id(workspace.workspace_id)
    work: dict[str, Any] = {
        "schema_version": "yuan.work-contract/v1",
        "work_id": work_id,
        "revision": _binding(work_id, "shadow-1", "0" * 64),
        "protocol_binding": protocol_binding,
        "harness_binding": harness_binding,
        "intent": {
            "goal": goal,
            "non_goals": [
                "Do not claim legacy task completion from status text alone.",
                "Do not select shadow runtime authority.",
            ],
            "constraints": [
                "Legacy source is read-only.",
                "Unmapped semantics remain structured unresolved items.",
            ],
        },
        "scope": {
            "allowed_paths": [
                item["path"] for item in manifest["files"]
            ]
            or [manifest["workspace_root"]],
            "denied_paths": [".git"],
            "side_effect_classes": ["none"],
        },
        "authorization": {"default": "deny", "grants": []},
        "budget": {
            "ticks": max(3, len(manifest["files"]) + replay_record_count + 2),
            "tool_calls": max(3, len(manifest["files"]) + replay_record_count + 2),
            "strategies": max(3, len(manifest["files"]) + replay_record_count + 2),
            "command_seconds": 1.0,
        },
        "acceptance_criteria": [
            {
                "id": "AC-SOURCE-INTEGRITY",
                "type": "structure",
                "required": True,
                "predicate": "All recognized legacy documents are content-addressed and unchanged during conversion.",
                "artifact_scope": manifest["workspace_root"],
                "verifier_binding": verifier,
            },
            {
                "id": "AC-SEMANTIC-MAPPING",
                "type": "structure",
                "required": True,
                "predicate": "Every legacy semantic is preserved verbatim or explicitly recorded as unresolved.",
                "artifact_scope": manifest["workspace_root"],
                "verifier_binding": verifier,
            },
        ],
        "safety_invariants": [
            {
                "id": "SAFE-LEGACY-READ-ONLY",
                "predicate": "No legacy source byte changes during shadow conversion.",
            }
        ],
    }
    work["revision"]["sha256"] = canonical_digest(work, omit=("revision", "sha256"))
    return work


def _timestamp_for_workspace(workspace_id: str) -> str:
    match = re.match(r"(\d{4})(\d{2})(\d{2})", workspace_id)
    if not match:
        return "1970-01-01T00:00:00+00:00"
    try:
        value = datetime(
            int(match.group(1)),
            int(match.group(2)),
            int(match.group(3)),
            tzinfo=timezone.utc,
        )
    except ValueError:
        return "1970-01-01T00:00:00+00:00"
    return value.isoformat()


def _evidence(
    *,
    evidence_id: str,
    sequence: int,
    work: dict[str, Any],
    ac_id: str,
    attempt_id: str,
    status: str,
    checks: list[dict[str, str]],
    artifact_scope: str,
    artifact_sha256: str,
    receipt_sha256: str,
    created_at: str,
) -> dict[str, Any]:
    verifier = work["acceptance_criteria"][0]["verifier_binding"]
    item: dict[str, Any] = {
        "schema_version": "yuan.evidence/v1",
        "evidence_id": evidence_id,
        "sequence": sequence,
        "work_binding": work["revision"],
        "ac_id": ac_id,
        "kind": "structure",
        "created_at": created_at,
        "source_attempt_id": attempt_id,
        "status": status,
        "assertions": len(checks),
        "checks": checks,
        "artifact_binding": {
            "scope": artifact_scope,
            "sha256": artifact_sha256,
        },
        "environment_binding": {
            "id": ENVIRONMENT_ID,
            "fingerprint": ENVIRONMENT_FINGERPRINT,
        },
        "verifier_binding": {
            key: verifier[key]
            for key in ("id", "revision", "sha256", "trust_root_id")
        },
        "harness_binding": work["harness_binding"],
        "logs": {
            "stdout_sha256": EMPTY_SHA256,
            "stderr_sha256": EMPTY_SHA256,
            "receipt_sha256": receipt_sha256,
        },
        "freshness": {
            "observed_artifact_sha256": artifact_sha256,
            "not_after": None,
        },
        "independence": {
            "method": "old-trust-root",
            "author_identity": "legacy-workspace",
            "verifier_identity": "yuan-shadow-migrator",
            "independent": True,
        },
        "immutable_digest": "0" * 64,
    }
    item["immutable_digest"] = canonical_digest(item, omit=("immutable_digest",))
    return item


def _attempt(
    *,
    attempt_id: str,
    sequence: int,
    work: dict[str, Any],
    source: dict[str, Any],
    evidence_id: str,
    artifact_sha256: str,
) -> dict[str, Any]:
    receipt = {
        "schema_version": "yuan.tool-receipt/v1",
        "kind": "file-read",
        "operation_id": f"OP-{attempt_id}",
        "status": "READ",
        "after_sha256": source["sha256"],
    }
    relevant = [{"scope": source["path"], "sha256": source["sha256"]}]
    return {
        "schema_version": "yuan.attempt/v1",
        "attempt_id": attempt_id,
        "work_binding": work["revision"],
        "protocol_binding": work["protocol_binding"],
        "harness_binding": work["harness_binding"],
        "sequence": sequence,
        "strategy_fingerprint": canonical_digest(
            {"kind": "legacy-source-read", "source": source["path"]}
        ),
        "relevant_inputs": relevant,
        "hypothesis": {
            "claim": f"Legacy source {source['path']} is captured byte-for-byte.",
            "falsification": "A before/after SHA-256 mismatch disproves capture.",
        },
        "action": {
            "type": "file-read",
            "mutating": False,
            "side_effect_class": "none",
            "scope": source["path"],
            "authorization_grant_id": None,
            "high_impact": False,
            "self_modification": None,
        },
        "budget_charge": {
            "ticks": 1,
            "tool_calls": 1,
            "strategies": 1,
            "command_seconds": 0,
        },
        "journal": [],
        "side_effect_state": "NOT_APPLICABLE",
        "tool_receipt": receipt,
        "postcondition": None,
        "evidence_ids": [evidence_id],
        "outcome": "SUCCEEDED",
    }


def build_history(
    workspace: LegacyWorkspace,
    manifest: dict[str, Any],
    work: dict[str, Any],
    unresolved: list[dict[str, str]],
    legacy_records: list[dict[str, Any]] | None = None,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    attempts: list[dict[str, Any]] = []
    evidence_items: list[dict[str, Any]] = []
    created_at = _timestamp_for_workspace(workspace.workspace_id)
    artifact_scope = work["acceptance_criteria"][0]["artifact_scope"]
    artifact_sha256 = manifest["digest"]
    for index, source in enumerate(manifest["files"], start=1):
        attempt_id = f"ATT-{work['work_id']}-{index:04d}"
        evidence_id = f"EVD-{work['work_id']}-{index:04d}"
        attempt = _attempt(
            attempt_id=attempt_id,
            sequence=index,
            work=work,
            source=source,
            evidence_id=evidence_id,
            artifact_sha256=artifact_sha256,
        )
        checks = [
            {
                "id": f"SOURCE-{index:04d}",
                "status": "PASS",
                "observation": f"{source['path']} sha256={source['sha256']}",
            }
        ]
        if index == 1:
            checks.append(
                {
                    "id": "SAFE-LEGACY-READ-ONLY",
                    "status": "PASS",
                    "observation": "source hash was stable across conversion",
                }
            )
        evidence = _evidence(
            evidence_id=evidence_id,
            sequence=index,
            work=work,
            ac_id="AC-SOURCE-INTEGRITY",
            attempt_id=attempt_id,
            status="PASS",
            checks=checks,
            artifact_scope=artifact_scope,
            artifact_sha256=artifact_sha256,
            receipt_sha256=canonical_digest(attempt["tool_receipt"]),
            created_at=created_at,
        )
        attempts.append(attempt)
        evidence_items.append(evidence)

    source_by_path = {item["path"]: item for item in manifest["files"]}
    for record in legacy_records or []:
        index = len(attempts) + 1
        source = source_by_path[record["source"]]
        attempt_id = f"ATT-{work['work_id']}-{index:04d}"
        evidence_id = f"EVD-{work['work_id']}-{index:04d}"
        attempt = _attempt(
            attempt_id=attempt_id,
            sequence=index,
            work=work,
            source=source,
            evidence_id=evidence_id,
            artifact_sha256=artifact_sha256,
        )
        attempt["action"]["type"] = "verify"
        identity = (
            record.get("task_id")
            or record.get("event", {}).get("payload", {}).get("task_id")
            or f"line-{record['line']}"
        )
        attempt["hypothesis"] = {
            "claim": (
                f"Legacy record {identity} is replayed as an observation, "
                "not as completion truth."
            ),
            "falsification": "A source hash or verbatim record mismatch disproves replay.",
        }
        observation = json.dumps(
            record, ensure_ascii=False, sort_keys=True, separators=(",", ":")
        )
        evidence = _evidence(
            evidence_id=evidence_id,
            sequence=index,
            work=work,
            ac_id="AC-SOURCE-INTEGRITY",
            attempt_id=attempt_id,
            status="PASS",
            checks=[
                {
                    "id": f"RECORD-{index:04d}",
                    "status": "PASS",
                    "observation": observation,
                }
            ],
            artifact_scope=artifact_scope,
            artifact_sha256=artifact_sha256,
            receipt_sha256=canonical_digest(attempt["tool_receipt"]),
            created_at=created_at,
        )
        attempts.append(attempt)
        evidence_items.append(evidence)

    index = len(attempts) + 1
    semantic_attempt_id = f"ATT-{work['work_id']}-{index:04d}"
    semantic_evidence_id = f"EVD-{work['work_id']}-{index:04d}"
    synthetic_source = {
        "path": artifact_scope,
        "sha256": artifact_sha256,
    }
    semantic_attempt = _attempt(
        attempt_id=semantic_attempt_id,
        sequence=index,
        work=work,
        source=synthetic_source,
        evidence_id=semantic_evidence_id,
        artifact_sha256=artifact_sha256,
    )
    semantic_attempt["action"]["type"] = "verify"
    semantic_attempt["hypothesis"] = {
        "claim": "Legacy semantics can be represented without inference.",
        "falsification": "Any missing typed verifier or source document makes mapping unresolved.",
    }
    if unresolved:
        checks = [
            {
                "id": f"UNRESOLVED-{position:04d}",
                "status": "FAIL",
                "observation": f"{item['code']}: {item['detail']}",
            }
            for position, item in enumerate(unresolved, start=1)
        ]
        status = "FAIL"
        semantic_attempt["outcome"] = "FAILED"
    else:
        checks = [
            {
                "id": "SEMANTIC-MAPPING",
                "status": "PASS",
                "observation": "all recognized semantics were mapped without inference",
            }
        ]
        status = "PASS"
    semantic_evidence = _evidence(
        evidence_id=semantic_evidence_id,
        sequence=index,
        work=work,
        ac_id="AC-SEMANTIC-MAPPING",
        attempt_id=semantic_attempt_id,
        status=status,
        checks=checks,
        artifact_scope=artifact_scope,
        artifact_sha256=artifact_sha256,
        receipt_sha256=canonical_digest(semantic_attempt["tool_receipt"]),
        created_at=created_at,
    )
    attempts.append(semantic_attempt)
    evidence_items.append(semantic_evidence)
    return attempts, evidence_items


def _load_core_modules():
    core_path = str(CORE_ROOT)
    if core_path not in sys.path:
        sys.path.insert(0, core_path)
    import conformance  # type: ignore
    import document_validation  # type: ignore

    return conformance, document_validation


def rebuild_projection(
    work: dict[str, Any],
    attempts: list[dict[str, Any]],
    evidence_items: list[dict[str, Any]],
    unresolved: list[dict[str, str]],
    artifact_sha256: str,
) -> tuple[dict[str, Any], str]:
    conformance, _ = _load_core_modules()
    trusted_now = datetime(2100, 1, 1, tzinfo=timezone.utc)
    memory = conformance.rebuild_run_memory(
        work,
        attempts,
        evidence_items,
        current_artifact_sha256=artifact_sha256,
        environment_id=ENVIRONMENT_ID,
        environment_fingerprint=ENVIRONMENT_FINGERPRINT,
        trusted_now=trusted_now,
    )
    core_result = memory["last_result"]
    if unresolved:
        memory["last_result"] = "BLOCKED"
        memory["legal_next_steps"] = []
        memory["rebuild"]["errors"] = sorted(
            set(
                memory["rebuild"]["errors"]
                + [f"LEGACY_UNRESOLVED:{item['code']}" for item in unresolved]
            )
        )
    return memory, core_result


def validate_projection(
    work: dict[str, Any],
    attempts: list[dict[str, Any]],
    evidence_items: list[dict[str, Any]],
    memory: dict[str, Any],
) -> list[str]:
    _, validation = _load_core_modules()
    errors: list[str] = []
    if not validation.work_revision_valid(work):
        errors.append("work-contract:WORK_REVISION_INVALID")
    for kind, items in (
        ("work-contract", [work]),
        ("attempt", attempts),
        ("evidence", evidence_items),
        ("run-memory", [memory]),
    ):
        for index, item in enumerate(items, start=1):
            for error in validation.validate_document(kind, item).errors:
                errors.append(f"{kind}[{index}]:{error}")
    return sorted(set(errors))


def authority_pointer(
    repo_root: pathlib.Path,
    shadow_root: pathlib.Path,
    legacy_snapshot_sha256: str,
) -> dict[str, Any]:
    return {
        "schema_version": "yuan.authority-pointer/v1",
        "revision": 1,
        "authority": "legacy",
        "legacy_root": "docs",
        "shadow_root": _relative(shadow_root, repo_root),
        "legacy_snapshot_sha256": legacy_snapshot_sha256,
    }


def validate_authority_pointer(pointer: dict[str, Any]) -> None:
    required = {
        "schema_version",
        "revision",
        "authority",
        "legacy_root",
        "shadow_root",
        "legacy_snapshot_sha256",
    }
    if set(pointer) != required:
        raise GuardError("authority pointer fields are invalid")
    if pointer["schema_version"] != "yuan.authority-pointer/v1":
        raise GuardError("authority pointer version is unsupported")
    if pointer["authority"] not in {"legacy", "shadow"}:
        raise GuardError("authority pointer value is invalid")
    if not isinstance(pointer["revision"], int) or pointer["revision"] < 1:
        raise GuardError("authority pointer revision is invalid")
    if not re.fullmatch(r"[0-9a-f]{64}", pointer["legacy_snapshot_sha256"]):
        raise GuardError("authority snapshot digest is invalid")


def _is_within(path: pathlib.Path, root: pathlib.Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except ValueError:
        return False


def assert_write_allowed(
    repo_root: pathlib.Path,
    pointer: dict[str, Any],
    writer_lane: str,
    target: str | pathlib.Path,
    expected_before_sha256: str | None,
) -> pathlib.Path:
    validate_authority_pointer(pointer)
    repo = repo_root.resolve()
    target_path = (repo / target).resolve() if not pathlib.Path(target).is_absolute() else pathlib.Path(target).resolve()
    if not _is_within(target_path, repo):
        raise GuardError("write target escapes repository")
    legacy = (repo / pointer["legacy_root"]).resolve()
    shadow = (repo / pointer["shadow_root"]).resolve()
    if writer_lane == "shadow":
        allowed = _is_within(target_path, shadow) and not _is_within(target_path, legacy)
    elif writer_lane == "legacy":
        allowed = _is_within(target_path, legacy) and not _is_within(target_path, shadow)
    else:
        raise GuardError("unknown writer lane")
    if not allowed:
        raise GuardError(f"{writer_lane} writer cannot write {target_path}")
    if target_path.exists():
        if not target_path.is_file():
            raise GuardError("CAS target is not a file")
        actual = file_sha256(target_path)
        if expected_before_sha256 is None or actual != expected_before_sha256:
            raise GuardError("compare-and-swap mismatch")
    elif expected_before_sha256 is not None:
        raise GuardError("compare-and-swap expected an existing file")
    return target_path


def atomic_write(
    path: pathlib.Path,
    payload: bytes,
    *,
    expected_before_sha256: str | None = None,
) -> None:
    if path.exists():
        if not path.is_file():
            raise MigrationError(f"write target is not a file: {path}")
        actual = file_sha256(path)
        if expected_before_sha256 is None or actual != expected_before_sha256:
            raise GuardError(f"compare-and-swap mismatch: {path}")
    elif expected_before_sha256 is not None:
        raise GuardError(f"compare-and-swap target missing: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    temporary = pathlib.Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


def generated_tree_files(root: pathlib.Path) -> dict[str, str]:
    return {
        path.relative_to(root).as_posix(): file_sha256(path)
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


def write_new_shadow(
    repo_root: pathlib.Path,
    shadow_root: pathlib.Path,
    files: dict[str, bytes],
    source_manifests: list[dict[str, Any]],
    projection_digest: str,
) -> None:
    shadow = safe_shadow_root(repo_root, shadow_root)
    if shadow.exists():
        if not shadow.is_dir():
            raise MigrationError("shadow target exists and is not a directory")
        marker = verify_owned_shadow(shadow)
        if marker.get("projection_digest") != projection_digest:
            raise GuardError("existing shadow projection differs; immutable CAS refused")
        for relative, payload in files.items():
            path = shadow / pathlib.PurePosixPath(relative)
            if not path.is_file() or file_sha256(path) != hashlib.sha256(payload).hexdigest():
                raise GuardError("existing shadow content differs; immutable CAS refused")
        return

    shadow.parent.mkdir(parents=True, exist_ok=True)
    stage = pathlib.Path(
        tempfile.mkdtemp(prefix=f".{shadow.name}.stage-", dir=shadow.parent)
    )
    try:
        for relative, payload in sorted(files.items()):
            target = stage / pathlib.PurePosixPath(relative)
            try:
                target.resolve().relative_to(stage.resolve())
            except ValueError as error:
                raise MigrationError(f"generated path escapes shadow: {relative}") from error
            atomic_write(target, payload)
        generated = generated_tree_files(stage)
        marker = {
            "schema_version": "yuan.shadow-root/v1",
            "projection_digest": projection_digest,
            "legacy_snapshot_sha256": snapshot_digest(source_manifests),
            "source_manifests": source_manifests,
            "generated_files": generated,
            "immutable_digest": "0" * 64,
        }
        marker["immutable_digest"] = canonical_digest(
            marker, omit=("immutable_digest",)
        )
        atomic_write(stage / ".yuan-shadow.json", canonical_json(marker))
        verify_source_manifests(repo_root, source_manifests)
        os.replace(stage, shadow)
    finally:
        if stage.exists():
            shutil.rmtree(stage)


def verify_owned_shadow(shadow_root: pathlib.Path) -> dict[str, Any]:
    marker_path = shadow_root / ".yuan-shadow.json"
    if not marker_path.is_file():
        raise MigrationError("shadow ownership marker missing")
    try:
        marker = json.loads(marker_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise MigrationError("shadow ownership marker is invalid") from error
    expected = marker.get("generated_files")
    if not isinstance(expected, dict):
        raise MigrationError("shadow generated-file manifest missing")
    if marker.get("immutable_digest") != canonical_digest(
        marker, omit=("immutable_digest",)
    ):
        raise MigrationError("shadow ownership marker digest mismatch")
    actual = generated_tree_files(shadow_root)
    expected_paths = set(expected) | {".yuan-shadow.json"}
    if set(actual) != expected_paths:
        raise MigrationError("shadow contains unknown or missing files")
    for relative, digest in expected.items():
        if actual.get(relative) != digest:
            raise MigrationError(f"shadow file changed: {relative}")
    return marker


def rollback_shadow(
    repo_root: pathlib.Path,
    shadow_root: pathlib.Path,
    receipt_path: pathlib.Path | None,
) -> dict[str, Any]:
    repo = repo_root.resolve()
    shadow = safe_shadow_root(repo, shadow_root)
    if not shadow.is_dir():
        raise MigrationError("shadow root does not exist")
    marker = verify_owned_shadow(shadow)
    manifests = marker.get("source_manifests", [])
    verify_source_manifests(repo, manifests)
    before = snapshot_digest(manifests)
    if before != marker.get("legacy_snapshot_sha256"):
        raise MigrationError("legacy snapshot does not match shadow marker")
    shutil.rmtree(shadow)
    verify_source_manifests(repo, manifests)
    after = snapshot_digest(manifests)
    receipt_document = {
        "schema_version": "yuan.shadow-rollback-receipt/v1",
        "status": "ROLLED_BACK",
        "shadow_root": _relative(shadow, repo),
        "projection_digest": marker.get("projection_digest"),
        "legacy_before_sha256": before,
        "legacy_after_sha256": after,
        "legacy_unchanged": before == after,
    }
    if not receipt_document["legacy_unchanged"]:
        raise MigrationError("legacy state changed during rollback")
    if receipt_path is not None:
        resolved_receipt = pathlib.Path(receipt_path).resolve()
        if _is_within(resolved_receipt, shadow):
            raise MigrationError("rollback receipt cannot be inside removed shadow")
        try:
            resolved_receipt.relative_to(repo)
        except ValueError as error:
            raise MigrationError("rollback receipt must be inside repository") from error
        atomic_write(resolved_receipt, canonical_json(receipt_document))
    return receipt_document


def verify_shadow_projection(
    repo_root: pathlib.Path, shadow_root: pathlib.Path
) -> dict[str, Any]:
    repo = repo_root.resolve()
    shadow = safe_shadow_root(repo, shadow_root)
    marker = verify_owned_shadow(shadow)
    manifests = marker.get("source_manifests", [])
    verify_source_manifests(repo, manifests)
    checks: list[dict[str, str]] = []
    for manifest in sorted(manifests, key=lambda item: item["workspace_id"]):
        workspace_root = shadow / "workspaces" / manifest["workspace_id"]
        try:
            work = json.loads(
                (workspace_root / "work-contract.json").read_text(encoding="utf-8")
            )
            attempts = [
                json.loads(path.read_text(encoding="utf-8"))
                for path in sorted((workspace_root / "attempts").glob("*.json"))
            ]
            evidence_items = [
                json.loads(path.read_text(encoding="utf-8"))
                for path in sorted((workspace_root / "evidence").glob("*.json"))
            ]
            stored_memory = json.loads(
                (workspace_root / "run-memory.json").read_text(encoding="utf-8")
            )
            replay_report = json.loads(
                (workspace_root / "replay-report.json").read_text(encoding="utf-8")
            )
            rebuilt, _ = rebuild_projection(
                work,
                attempts,
                evidence_items,
                replay_report["unresolved"],
                manifest["digest"],
            )
            validation_errors = validate_projection(
                work, attempts, evidence_items, stored_memory
            )
            status = (
                "PASS"
                if not validation_errors and rebuilt == stored_memory
                else "FAIL"
            )
            observation = (
                "schema valid and byte-equivalent deterministic rebuild"
                if status == "PASS"
                else f"errors={validation_errors}; rebuild_equal={rebuilt == stored_memory}"
            )
        except (OSError, UnicodeError, json.JSONDecodeError, KeyError) as error:
            status = "FAIL"
            observation = str(error)
        checks.append(
            {
                "id": f"WORKSPACE-{manifest['workspace_id']}",
                "status": status,
                "observation": observation,
            }
        )
    status = (
        "PASS"
        if checks and all(item["status"] == "PASS" for item in checks)
        else "FAIL"
    )
    return {
        "schema_version": "yuan.shadow-verification-receipt/v1",
        "status": status,
        "assertions": len(checks),
        "checks": checks,
        "projection_digest": marker["projection_digest"],
        "legacy_snapshot_sha256": marker["legacy_snapshot_sha256"],
        "authority": "legacy",
    }
