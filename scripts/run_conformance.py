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
from yuan.capabilities import available_profiles, capability_manifest, capability_payloads  # noqa: E402
from yuan.identity import harness_digest  # noqa: E402
from yuan.ledger import atomic_write  # noqa: E402
from yuan.project import BOOTSTRAP_END, BOOTSTRAP_START, bootstrap_bytes  # noqa: E402
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
    core_names = {
        "artifacts.py", "canonical.py", "errors.py", "identity.py", "ledger.py",
        "paths.py", "primitives.py", "reducer.py", "runtime.py", "validate.py", "workflow.py",
    }
    port_names = {"ports.py"}
    memory_names = {"memory.py", "memory_views.py"}
    deployment_names = {"project.py", "release.py"}
    interface_names = {"__init__.py", "__main__.py", "adapters.py", "capabilities.py", "cli.py"}
    counts = {
        path.name: sum(bool(line.strip()) for line in path.read_text(encoding="utf-8").splitlines())
        for path in sorted((ROOT / "src" / "yuan").glob("*.py"))
    }
    core_lines = sum(count for name, count in counts.items() if name in core_names)
    port_lines = sum(count for name, count in counts.items() if name in port_names)
    memory_lines = sum(count for name, count in counts.items() if name in memory_names)
    deployment_lines = sum(count for name, count in counts.items() if name in deployment_names)
    interface_lines = sum(count for name, count in counts.items() if name in interface_names)
    classified = core_names | port_names | memory_names | deployment_names | interface_names
    unclassified = sorted(set(counts) - classified)
    if protocol_lines > 500:
        raise RuntimeError(f"Protocol 超出 500 个非空行：{protocol_lines}")
    if core_lines > 2000:
        raise RuntimeError(f"Core Kernel 超出 2000 个非空 Python 行 Design Review 阈值：{core_lines}")
    if unclassified:
        raise RuntimeError("Python 模块尚未分配 Design Review 预算：" + ", ".join(unclassified))
    if deployment_lines > 1000:
        raise RuntimeError(f"Deployment/Release 层超出 1000 个非空 Python 行 Design Review 阈值：{deployment_lines}")
    if interface_lines > 1200:
        raise RuntimeError(f"Capability/CLI 层超出 1200 个非空 Python 行 Design Review 阈值：{interface_lines}")
    if port_lines > 250:
        raise RuntimeError(f"Platform Port 边界超出 250 个非空 Python 行 Design Review 阈值：{port_lines}")
    if memory_lines > 600:
        raise RuntimeError(f"Long-term Memory 层超出 600 个非空 Python 行 Design Review 阈值：{memory_lines}")
    return {
        "status": "PASS",
        "protocol_nonempty_lines": protocol_lines,
        "core_python_nonempty_lines": core_lines,
        "support_python_nonempty_lines": deployment_lines + interface_lines,
        "deployment_python_nonempty_lines": deployment_lines,
        "interface_python_nonempty_lines": interface_lines,
        "port_python_nonempty_lines": port_lines,
        "memory_python_nonempty_lines": memory_lines,
    }


def validate_bootstrap() -> dict[str, object]:
    root_bootstrap = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
    if root_bootstrap.count(BOOTSTRAP_START) != 1 or root_bootstrap.count(BOOTSTRAP_END) != 1:
        raise RuntimeError("根 AGENTS.md 的 Yuan Managed Block 不唯一")
    managed = root_bootstrap.split(BOOTSTRAP_START, 1)[1].split(BOOTSTRAP_END, 1)[0].strip()
    packaged = bootstrap_bytes().decode("utf-8").strip()
    if managed != packaged:
        raise RuntimeError("根 AGENTS.md 与发行包 Agent Bootstrap 不一致")
    return {"status": "PASS", "bootstrap_digest": digest_bytes(bootstrap_bytes())}


def validate_capability_profile() -> dict[str, object]:
    summaries = []
    for profile_id in available_profiles():
        manifest = capability_manifest(profile_id)
        payloads = capability_payloads(profile_id)
        kinds = {item["kind"] for item in manifest["files"]}
        paths = {path for path, _ in payloads}
        if not {"rules", "agents", "skills"} <= kinds:
            raise RuntimeError(f"能力 Profile 缺少 Rules、Agents 或 Skills：{profile_id}")
        if len(paths) != len(payloads) or len(paths) != len(manifest["files"]):
            raise RuntimeError(f"能力 Profile 路径重复或 Manifest 不完整：{profile_id}")
        catalog_paths = set(manifest["required_rules"]) | {
            item["path"] for item in manifest["agents"] + manifest["skills"]
        }
        if not catalog_paths <= paths:
            raise RuntimeError(f"能力 Catalog 引用了未打包文件：{profile_id}")
        summaries.append({
            "profile_id": profile_id,
            "profile_version": manifest["profile_version"],
            "manifest_digest": manifest["digest"],
            "file_count": len(paths),
            "agent_count": len(manifest["agents"]),
            "skill_count": len(manifest["skills"]),
        })
    bootstrap = bootstrap_bytes().decode("utf-8")
    required_flow_terms = [
        "capability list", "capability route", "intake template", "intake confirm",
        "work confirm", "handoff record", "run supersede", "没有 Active Work",
    ]
    missing = [item for item in required_flow_terms if item not in bootstrap]
    if missing:
        raise RuntimeError("Agent Bootstrap 缺少闭环入口：" + ", ".join(missing))
    return {
        "status": "PASS",
        "profiles": summaries,
    }


def validate_automation() -> dict[str, object]:
    conformance = ROOT / ".github" / "workflows" / "conformance.yml"
    release = ROOT / ".github" / "workflows" / "release.yml"
    if not conformance.is_file() or not release.is_file():
        raise RuntimeError("GitHub Conformance/Release Workflow 缺失")
    conformance_text = conformance.read_text(encoding="utf-8")
    release_text = release.read_text(encoding="utf-8")
    if "scripts/run_conformance.py" not in conformance_text or "scripts/build_zipapp.py" not in release_text:
        raise RuntimeError("GitHub Workflow 没有绑定 Yuan 验证与发行入口")
    return {"status": "PASS", "workflows": [conformance.name, release.name]}


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
        "bootstrap": validate_bootstrap(),
        "capability_profile": validate_capability_profile(),
        "automation": validate_automation(),
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
