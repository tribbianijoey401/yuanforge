"""确定性 Artifact 枚举与 Diff。"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from .canonical import digest_bytes, digest
from .errors import IntegrityError, ValidationError
from .paths import matches_any, normalize_relative


DEFAULT_EXCLUDES = [".git/**", ".yuan-run/**", "__pycache__/**", "*.pyc"]


def build_manifest(
    root: Path,
    *,
    include: list[str] | None = None,
    exclude: list[str] | None = None,
    max_files: int = 100_000,
    max_bytes: int = 2_000_000_000,
) -> dict[str, Any]:
    root = root.resolve()
    includes = include or ["**"]
    excludes = DEFAULT_EXCLUDES + (exclude or [])
    entries: list[dict[str, Any]] = []
    total = 0
    for current, dirs, files in os.walk(root, topdown=True, followlinks=False):
        base = Path(current)
        kept_dirs = []
        for name in sorted(dirs):
            path = base / name
            relative = path.relative_to(root).as_posix()
            if path.is_symlink():
                raise IntegrityError(f"Artifact 包含 Directory Link：{relative}")
            if not matches_any(relative, excludes) and not matches_any(relative + "/x", excludes):
                kept_dirs.append(name)
        dirs[:] = kept_dirs
        for name in sorted(files):
            path = base / name
            relative = path.relative_to(root).as_posix()
            normalize_relative(relative)
            if matches_any(relative, excludes) or not matches_any(relative, includes):
                continue
            if path.is_symlink() or not path.is_file():
                raise IntegrityError(f"Artifact 包含 Link 或非文件对象：{relative}")
            payload = path.read_bytes()
            total += len(payload)
            entries.append({"path": relative, "size": len(payload), "digest": digest_bytes(payload)})
            if len(entries) > max_files or total > max_bytes:
                raise ValidationError("Artifact 枚举超出 Budget")
    entries.sort(key=lambda item: item["path"])
    manifest = {
        "schema_version": "yuan.artifact-manifest/v1",
        "root": ".",
        "files": entries,
        "file_count": len(entries),
        "byte_count": total,
    }
    manifest["digest"] = digest(manifest, ("digest",))
    return manifest


def diff_manifests(before: dict[str, Any], after: dict[str, Any]) -> dict[str, list[str]]:
    left = {item["path"]: item["digest"] for item in before["files"]}
    right = {item["path"]: item["digest"] for item in after["files"]}
    return {
        "added": sorted(right.keys() - left.keys()),
        "modified": sorted(path for path in left.keys() & right.keys() if left[path] != right[path]),
        "deleted": sorted(left.keys() - right.keys()),
    }


def changed_paths(value: dict[str, list[str]]) -> list[str]:
    return sorted(value["added"] + value["modified"] + value["deleted"])
