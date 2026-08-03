"""Yuan 可选能力 Profile 的确定性打包、安装与校验。"""

from __future__ import annotations

from importlib import resources
from pathlib import Path
from typing import Any

from .canonical import digest, digest_bytes
from .errors import IntegrityError


DEFAULT_PROFILE = "vibe-coding"
PROFILE_VERSION = "1.0.0"
RESOURCE_ROOT = Path("profiles") / DEFAULT_PROFILE
INSTALL_ROOT = Path(".yuan") / "extensions" / DEFAULT_PROFILE
MANIFEST_PATH = ".yuan/extensions/manifest.json"


def _resource_files() -> list[tuple[str, bytes]]:
    root = resources.files("yuan").joinpath(*RESOURCE_ROOT.parts)
    files: list[tuple[str, bytes]] = []

    def visit(node: Any, relative: Path) -> None:
        for child in sorted(node.iterdir(), key=lambda item: item.name):
            child_relative = relative / child.name
            if child.is_dir():
                visit(child, child_relative)
            elif not child.name.endswith(".pyc"):
                files.append((child_relative.as_posix(), child.read_bytes()))

    visit(root, Path())
    if not files:
        raise IntegrityError("默认能力 Profile 为空")
    return files


def capability_payloads() -> list[tuple[str, bytes]]:
    """返回项目相对路径与发行包内的固定内容。"""

    return [((INSTALL_ROOT / relative).as_posix(), payload) for relative, payload in _resource_files()]


def capability_manifest() -> dict[str, Any]:
    files = [
        {
            "path": path,
            "digest": digest_bytes(payload),
            "bytes": len(payload),
            "kind": Path(path).parts[3],
        }
        for path, payload in capability_payloads()
    ]
    value = {
        "schema_version": "yuan.capability-profile/v1",
        "profile_id": DEFAULT_PROFILE,
        "profile_version": PROFILE_VERSION,
        "boundary": "advisory-and-evidence-only",
        "files": files,
        "custom_root": ".yuan/extensions/custom",
    }
    value["digest"] = digest(value, ("digest",))
    return value


def capability_paths() -> tuple[str, ...]:
    return tuple(path for path, _ in capability_payloads()) + (MANIFEST_PATH,)
