"""确定性 Zipapp 构建与 Release Manifest 验证。"""

from __future__ import annotations

import json
import os
import zipfile
from importlib import resources
from pathlib import Path
from typing import Any

from . import __version__
from .canonical import canonical_bytes, digest, digest_bytes, verify_digest
from .errors import IntegrityError, ValidationError


ZIP_TIME = (1980, 1, 1, 0, 0, 0)
MAIN = b"from yuan.cli import main\nraise SystemExit(main())\n"


def source_entries(repo_root: Path) -> list[dict[str, Any]]:
    package = repo_root.resolve() / "src" / "yuan"
    entries = []
    for path in sorted(package.rglob("*"), key=lambda item: item.as_posix()):
        if path.is_file() and "__pycache__" not in path.parts and path.suffix != ".pyc":
            payload = path.read_bytes()
            entries.append(
                {
                    "source_path": path.relative_to(repo_root).as_posix(),
                    "archive_path": (Path("yuan") / path.relative_to(package)).as_posix(),
                    "digest": digest_bytes(payload),
                    "bytes": len(payload),
                }
            )
    return entries


def _zip_info(name: str) -> zipfile.ZipInfo:
    info = zipfile.ZipInfo(name, ZIP_TIME)
    info.compress_type = zipfile.ZIP_STORED
    info.create_system = 3
    info.external_attr = 0o100644 << 16
    return info


def _write_zipapp(output: Path, entries: list[tuple[str, bytes]]) -> None:
    output = output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_name(f".{output.name}.{os.getpid()}.tmp")
    try:
        with zipfile.ZipFile(temporary, "w") as archive:
            archive.writestr(_zip_info("__main__.py"), MAIN)
            for archive_path, payload in entries:
                archive.writestr(_zip_info(archive_path), payload)
        os.replace(temporary, output)
    finally:
        if temporary.exists():
            temporary.unlink()


def _resource_payloads() -> list[tuple[str, bytes]]:
    payloads: list[tuple[str, bytes]] = []

    def visit(node: Any, relative: Path) -> None:
        for child in sorted(node.iterdir(), key=lambda item: item.name):
            child_relative = relative / child.name
            if child.is_dir():
                if child.name != "__pycache__":
                    visit(child, child_relative)
            elif child.name.endswith(".pyc"):
                continue
            else:
                payloads.append(((Path("yuan") / child_relative).as_posix(), child.read_bytes()))

    visit(resources.files("yuan"), Path())
    return payloads


def _release_manifest(output: Path, entries: list[dict[str, Any]]) -> dict[str, Any]:
    payload = output.resolve().read_bytes()
    manifest = {
        "schema_version": "yuan.release-manifest/v1",
        "version": __version__,
        "format": "deterministic-zipapp-stored/v1",
        "artifact": {"path": output.name, "digest": digest_bytes(payload), "bytes": len(payload)},
        "entrypoint": {"path": "__main__.py", "digest": digest_bytes(MAIN)},
        "sources": entries,
    }
    manifest["digest"] = digest(manifest, ("digest",))
    return manifest


def build_runtime_zipapp(output: Path) -> dict[str, Any]:
    """从当前已安装 Package 构建项目固定的确定性 Runtime。"""

    payloads = _resource_payloads()
    if not payloads:
        raise ValidationError("已安装的 Yuan Package 为空")
    entries = [
        {
            "source_path": f"src/{archive_path}",
            "archive_path": archive_path,
            "digest": digest_bytes(payload),
            "bytes": len(payload),
        }
        for archive_path, payload in payloads
    ]
    _write_zipapp(output, payloads)
    manifest = _release_manifest(output, entries)
    manifest["artifact"]["path"] = "yuan.pyz"
    manifest["digest"] = digest(manifest, ("digest",))
    return {**manifest["artifact"], "manifest": manifest}


def build_zipapp(repo_root: Path, output: Path) -> dict[str, Any]:
    repo_root = repo_root.resolve()
    output = output.resolve()
    entries = source_entries(repo_root)
    if not entries:
        raise ValidationError("Release Source 为空")
    _write_zipapp(
        output,
        [(entry["archive_path"], (repo_root / entry["source_path"]).read_bytes()) for entry in entries],
    )
    return _release_manifest(output, entries)


def write_release(repo_root: Path, output: Path, manifest_path: Path) -> dict[str, Any]:
    from .ledger import atomic_write

    manifest = build_zipapp(repo_root, output)
    atomic_write(manifest_path.resolve(), canonical_bytes(manifest))
    return manifest


def verify_release(
    manifest: dict[str, Any],
    artifact: Path,
    *,
    repo_root: Path | None = None,
) -> dict[str, Any]:
    required = {"schema_version", "version", "format", "artifact", "entrypoint", "sources", "digest"}
    if not isinstance(manifest, dict) or set(manifest) != required:
        raise ValidationError("Release Manifest 字段不合法")
    if manifest["schema_version"] != "yuan.release-manifest/v1" or not verify_digest(manifest):
        raise IntegrityError("Release Manifest Digest 不匹配")
    artifact_record = manifest["artifact"]
    entrypoint = manifest["entrypoint"]
    sources = manifest["sources"]
    if not isinstance(artifact_record, dict) or set(artifact_record) != {"path", "digest", "bytes"}:
        raise ValidationError("Release Artifact Binding 不合法")
    if not isinstance(entrypoint, dict) or set(entrypoint) != {"path", "digest"}:
        raise ValidationError("Release Entrypoint Binding 不合法")
    if not isinstance(sources, list) or not sources or any(
        not isinstance(item, dict)
        or set(item) != {"source_path", "archive_path", "digest", "bytes"}
        for item in sources
    ):
        raise ValidationError("Release Source Binding 不合法")
    try:
        payload = artifact.resolve().read_bytes()
    except OSError as exc:
        raise ValidationError("Release Artifact 不可读") from exc
    if (
        artifact_record.get("digest") != digest_bytes(payload)
        or artifact_record.get("bytes") != len(payload)
    ):
        raise IntegrityError("Release Artifact Digest 或 Size 不匹配")
    try:
        with zipfile.ZipFile(artifact.resolve(), "r") as archive:
            names = archive.namelist()
            expected = ["__main__.py", *[item["archive_path"] for item in sources]]
            if names != expected:
                raise IntegrityError("Zipapp Entry 顺序或集合不匹配")
            if digest_bytes(archive.read("__main__.py")) != entrypoint["digest"]:
                raise IntegrityError("Zipapp Entrypoint Digest 不匹配")
            for item in sources:
                if digest_bytes(archive.read(item["archive_path"])) != item["digest"]:
                    raise IntegrityError(f"Zipapp Source Entry 不匹配: {item['archive_path']}")
    except zipfile.BadZipFile as exc:
        raise IntegrityError("Release Artifact 不是有效 Zipapp") from exc
    if repo_root is not None:
        actual = source_entries(repo_root)
        if actual != manifest["sources"]:
            raise IntegrityError("当前 Source Tree 与 Release Manifest 不匹配")
    return {
        "status": "PASS",
        "version": manifest["version"],
        "artifact_digest": artifact_record["digest"],
        "source_count": len(sources),
    }


def read_manifest(path: Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValidationError("Release Manifest 不是有效 JSON") from exc
    if not isinstance(value, dict):
        raise ValidationError("Release Manifest 必须是 JSON Object")
    return value
