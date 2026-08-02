"""运行 Yuan Reference Kernel 的完整 Conformance Suite。"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from yuan.adapters import validate_adapter_descriptor  # noqa: E402
from yuan.canonical import canonical_bytes, digest_bytes  # noqa: E402
from yuan.identity import harness_digest  # noqa: E402
from yuan.ledger import atomic_write  # noqa: E402
from yuan.release import build_zipapp, verify_release  # noqa: E402


def run_command(argv: list[str]) -> dict[str, object]:
    environment = dict(os.environ)
    environment["PYTHONPATH"] = str(ROOT / "src")
    completed = subprocess.run(
        argv,
        cwd=ROOT,
        env=environment,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        shell=False,
        check=False,
    )
    receipt = {
        "argv": argv,
        "exit_code": completed.returncode,
        "stdout_digest": digest_bytes(completed.stdout),
        "stderr_digest": digest_bytes(completed.stderr),
    }
    if completed.returncode != 0:
        sys.stderr.buffer.write(completed.stdout)
        sys.stderr.buffer.write(completed.stderr)
        raise RuntimeError(f"Conformance Command 失败：{argv}")
    return receipt


def validate_schemas() -> dict[str, object]:
    files = sorted((ROOT / "schemas").glob("*.json"))
    for path in files:
        value = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(value, dict) or "$schema" not in value or "title" not in value:
            raise RuntimeError(f"Schema 缺少基础元数据：{path.name}")
    return {"status": "PASS", "count": len(files)}


def validate_size_budget() -> dict[str, object]:
    protocol = (ROOT / "src" / "yuan" / "protocol.md").read_text(encoding="utf-8")
    protocol_lines = sum(bool(line.strip()) for line in protocol.splitlines())
    python_lines = sum(
        len(path.read_text(encoding="utf-8").splitlines())
        for path in sorted((ROOT / "src" / "yuan").glob("*.py"))
    )
    if protocol_lines > 500:
        raise RuntimeError(f"Protocol 超出 500 个非空行：{protocol_lines}")
    if python_lines > 3000:
        raise RuntimeError(f"Reference Kernel 超出 3000 行 Design Review 阈值：{python_lines}")
    return {"status": "PASS", "protocol_nonempty_lines": protocol_lines, "kernel_python_lines": python_lines}


def validate_reproducible_release() -> dict[str, object]:
    with tempfile.TemporaryDirectory() as first, tempfile.TemporaryDirectory() as second:
        first_artifact = Path(first) / "yuan.pyz"
        second_artifact = Path(second) / "yuan.pyz"
        first_manifest = build_zipapp(ROOT, first_artifact)
        second_manifest = build_zipapp(ROOT, second_artifact)
        if first_artifact.read_bytes() != second_artifact.read_bytes() or first_manifest != second_manifest:
            raise RuntimeError("两次 Release 构建结果不一致")
        verification = verify_release(first_manifest, first_artifact, repo_root=ROOT)
        zipapp = run_command([sys.executable, "-B", str(first_artifact), "--help"])
        return {
            "status": "PASS",
            "artifact_digest": verification["artifact_digest"],
            "source_count": verification["source_count"],
            "zipapp_receipt": zipapp,
        }


def build_report() -> dict[str, object]:
    tests = run_command([sys.executable, "-B", "-m", "unittest", "discover", "-s", "tests", "-v"])
    descriptor_path = ROOT / "adapters" / "codex-audited.json"
    descriptor = validate_adapter_descriptor(
        json.loads(descriptor_path.read_text(encoding="utf-8")),
        ROOT,
    )
    checks = {
        "unit_tests": {"status": "PASS", "receipt": tests},
        "schemas": validate_schemas(),
        "adapter": {
            "status": "PASS",
            "adapter_id": descriptor["adapter_id"],
            "profile": descriptor["profile"],
        },
        "size_budget": validate_size_budget(),
        "reproducible_release": validate_reproducible_release(),
    }
    return {
        "schema_version": "yuan.conformance-report/v1",
        "status": "PASS",
        "harness_digest": harness_digest(),
        "checks": checks,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="运行 Yuan 完整 Conformance Suite")
    parser.add_argument(
        "--output",
        type=Path,
        default=ROOT / "dist" / "conformance-report.json",
        help="机器可读报告输出路径",
    )
    args = parser.parse_args()
    try:
        report = build_report()
        atomic_write(args.output.resolve(), canonical_bytes(report))
        print(canonical_bytes({"status": "PASS", "report": str(args.output.resolve()), "checks": list(report["checks"])}).decode("utf-8"))
        return 0
    except Exception as exc:  # Conformance 入口必须把任意失败收敛为非零退出。
        print(canonical_bytes({"status": "FAIL", "error": str(exc)}).decode("utf-8"), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
