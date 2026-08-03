"""构建可复现的单文件 `yuan.pyz` 与 Release Manifest。"""

from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from yuan.release import write_release  # noqa: E402
from yuan.ledger import atomic_write  # noqa: E402


def main() -> None:
    output = ROOT / "dist" / "yuan.pyz"
    manifest_path = ROOT / "dist" / "release-manifest.json"
    manifest = write_release(ROOT, output, manifest_path)
    checksum_path = ROOT / "dist" / "yuan.pyz.sha256"
    atomic_write(checksum_path, f"{manifest['artifact']['digest']}  yuan.pyz\n".encode("ascii"))
    print(json.dumps({
        "status": "BUILT",
        "artifact": str(output),
        "manifest": str(manifest_path),
        "checksum": str(checksum_path),
        "digest": manifest["artifact"]["digest"],
    }, ensure_ascii=False, separators=(",", ":")))


if __name__ == "__main__":
    main()
