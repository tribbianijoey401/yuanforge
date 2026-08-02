"""已安装 Protocol 与 Kernel 的 Identity。"""

from __future__ import annotations

from importlib import resources
import platform
from pathlib import Path
import sys

from . import __version__
from .canonical import digest, digest_bytes
from .errors import IntegrityError


def protocol_bytes() -> bytes:
    try:
        return resources.files("yuan").joinpath("protocol.md").read_bytes()
    except (FileNotFoundError, ModuleNotFoundError, OSError) as exc:
        raise IntegrityError("发行包缺少 Core Protocol") from exc


def harness_digest() -> str:
    files = []
    try:
        children = sorted(resources.files("yuan").iterdir(), key=lambda item: item.name)
        for item in children:
            if item.name.endswith(".py"):
                files.append({"path": item.name, "digest": digest_bytes(item.read_bytes())})
    except (FileNotFoundError, ModuleNotFoundError, OSError) as exc:
        raise IntegrityError("已安装 Kernel 文件不可读") from exc
    return digest({"version": __version__, "files": files})


def environment_binding() -> dict[str, str]:
    details = {
        "implementation": platform.python_implementation(),
        "python": platform.python_version(),
        "platform": platform.platform(),
        "executable": str(Path(sys.executable).resolve()),
    }
    return {
        "id": "yuan.local-python",
        "revision": f"{sys.version_info.major}.{sys.version_info.minor}",
        "digest": digest(details),
    }
