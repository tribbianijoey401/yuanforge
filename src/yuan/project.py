"""把固定版本 Yuan Runtime 安装或同步到 Vibe Coding 项目。"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from importlib import resources
from pathlib import Path
from typing import Any

from . import __version__
from .canonical import canonical_bytes, digest_bytes, verify_digest
from .capabilities import (
    DEFAULT_PROFILE,
    MANIFEST_PATH as CAPABILITY_MANIFEST_PATH,
    capability_manifest,
    capability_paths,
    capability_payloads,
)
from .errors import IntegrityError, ValidationError, YuanError
from .identity import environment_binding, harness_digest, protocol_bytes
from .ledger import Ledger, atomic_write, exclusive_lock
from .release import build_runtime_zipapp, verify_release
from .validate import identifier, with_digest


BOOTSTRAP_START = "<!-- yuan:bootstrap:start -->"
BOOTSTRAP_END = "<!-- yuan:bootstrap:end -->"
GITIGNORE_START = "# yuan:managed:start"
GITIGNORE_END = "# yuan:managed:end"
SAFE_UPDATE_RESULTS = {"COMPLETE"}
DEPLOYMENT_LOCK_TIMEOUT = 10.0
CORE_DEPLOYMENT_FILES = (
    ".yuan/bin/yuan.pyz",
    ".yuan/config.json",
    ".yuan/protocol.md",
    ".yuan/install.json",
    ".yuan/adapters/codex-audited.json",
    ".yuan/release-manifest.json",
    ".yuan/conformance-report.json",
)
DEPLOYMENT_FILES = CORE_DEPLOYMENT_FILES + capability_paths()
INSTALL_TRANSACTION_FILES = DEPLOYMENT_FILES + ("AGENTS.md", ".gitignore", ".yuan-run/current.json")
GITIGNORE_CONTENT = ".yuan-run/\n.yuan/drafts/\n.yuan/candidates/\n.yuan/releases/"
REQUIRED_CONFORMANCE_CHECKS = {
    "unit_tests", "schemas", "adapter", "bootstrap", "capability_profile", "automation", "size_budget", "reproducible_release"
}


def agent_guidance(root: Path) -> dict[str, str]:
    """返回安装后可直接交给 Agent 的开始与继续提示。"""

    return {
        "project_root": str(root.resolve()),
        "status_command": "python -B .yuan/bin/yuan.pyz --root . status",
        "capability_profile": DEFAULT_PROFILE,
        "start_prompt": (
            "请读取项目根目录 AGENTS.md，并按照 Yuan Agent Bootstrap 开始一个新的 Work。"
            "我的需求是：<在这里描述需求>"
        ),
        "continue_prompt": (
            "请读取项目根目录 AGENTS.md，检查 Yuan 当前状态，并按照 Yuan Agent Bootstrap "
            "继续未完成的 Work；只有 Reducer 返回 COMPLETE 时才报告完成。"
        ),
    }


def bootstrap_bytes() -> bytes:
    try:
        return resources.files("yuan").joinpath("bootstrap.md").read_bytes()
    except (FileNotFoundError, ModuleNotFoundError, OSError) as exc:
        raise IntegrityError("发行包缺少 Agent Bootstrap") from exc


def load_release_context(source_root: Path, report_path: Path) -> dict[str, Any]:
    """读取 Conformance Evidence，并绑定当前 Git/Package 来源。"""

    try:
        report = json.loads(report_path.resolve().read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ValidationError("Conformance Report 不存在或不是合法 JSON") from exc
    source_root = source_root.resolve()
    revision = __version__
    kind = "package"
    dirty = False
    try:
        completed = subprocess.run(
            ["git", "-C", str(source_root), "rev-parse", "HEAD"],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            check=False,
            shell=False,
        )
    except OSError:
        completed = None
    if completed is not None and completed.returncode == 0:
        kind = "git"
        revision = completed.stdout.decode("ascii").strip()
        status = subprocess.run(
            ["git", "-C", str(source_root), "status", "--porcelain", "--untracked-files=normal"],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            check=False,
            shell=False,
        )
        if status.returncode != 0:
            raise IntegrityError("不能确定 Yuan Source Worktree 状态")
        dirty = bool(status.stdout.strip())
    source = with_digest({
        "schema_version": "yuan.release-source/v1",
        "kind": kind,
        "revision": revision,
        "dirty": dirty,
    })
    return {"report": report, "source": source}


def codex_descriptor() -> dict[str, Any]:
    return with_digest({
        "schema_version": "yuan.adapter/v1",
        "adapter_id": "codex-audited",
        "platform": "codex",
        "profile": "AUDITED",
        "capabilities": {
            "artifact_audit": {"status": "SUPPORTED", "reason": "Yuan 在 Attempt 前后计算并验证 Artifact Manifest。"},
            "scoped_file_cas": {"status": "UNSUPPORTED", "reason": "Codex 原生文件工具无法被 Yuan 物理撤销。"},
            "bounded_command": {"status": "UNSUPPORTED", "reason": "Codex 原生 Shell 不能由 Yuan 强制替换。"},
            "llm_proposal": {"status": "UNSUPPORTED", "reason": "Codex 未向项目内 Harness 暴露独立模型调用接口。"},
            "physical_effect_mediation": {"status": "UNSUPPORTED", "reason": "开放 Codex 会话存在 Yuan Port 之外的原生副作用通道。"},
        },
        "port": None,
        "notes": "该 Descriptor 只声明可验证的 AUDITED 保证，不宣称 ENFORCED。",
    })


def _resolved_run_id(run_id: str | None) -> str:
    if run_id is None:
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        run_id = f"RUN-{stamp}-{os.getpid()}"
    return identifier(run_id, "run_id")


def initialize_repository(root: Path, profile: str, run_id: str | None) -> dict[str, Any]:
    root = root.resolve()
    config_path = root / ".yuan" / "config.json"
    if config_path.exists():
        raise YuanError("仓库已经初始化")
    if profile == "ENFORCED":
        raise YuanError("ENFORCED 需要另行安装符合规范的 Action Port Adapter")
    run_id = _resolved_run_id(run_id)
    state_root = root / ".yuan-run"
    ledger = Ledger(state_root, run_id)
    if ledger.run_root.exists():
        raise YuanError("Run id 已存在")
    protocol = protocol_bytes()
    atomic_write(root / ".yuan" / "protocol.md", protocol)
    config = with_digest({
        "schema_version": "yuan.config/v1",
        "profile": profile,
        "protocol": {"id": "yuan.core", "revision": "0.2", "digest": digest_bytes(protocol)},
        "harness": {"id": "yuan.python", "revision": __version__, "digest": harness_digest()},
        "state_root": ".yuan-run",
        "artifact_exclude": [".yuan-run/**", ".git/**", "__pycache__/**", "*.pyc"],
        "environment": environment_binding(),
    })
    atomic_write(config_path, canonical_bytes(config))
    ledger.run_root.mkdir(parents=True, exist_ok=False)
    atomic_write(state_root / "current.json", canonical_bytes({"run_id": run_id}))
    return {"status": "INITIALIZED", "run_id": run_id, "profile": profile, "protocol": config["protocol"], "harness": config["harness"]}


def _merged_marked(path: Path, content: str, start: str, end: str) -> bytes:
    block = f"{start}\n{content.strip()}\n{end}\n"
    if not path.exists():
        return block.encode("utf-8")
    try:
        current = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        raise ValidationError(f"不能读取 UTF-8 文件：{path}") from exc
    starts = current.count(start)
    ends = current.count(end)
    if starts == 0 and ends == 0:
        merged = current.rstrip() + "\n\n" + block
    elif starts == 1 and ends == 1 and current.index(start) < current.index(end):
        before, remainder = current.split(start, 1)
        _, after = remainder.split(end, 1)
        merged = before + block + after.lstrip("\r\n")
    else:
        raise ValidationError(f"Managed Block 缺失、重复或顺序错误：{path}")
    return merged.encode("utf-8")


def _merge_marked(path: Path, content: str, start: str, end: str) -> None:
    atomic_write(path, _merged_marked(path, content, start, end))


def _managed_bytes(path: Path, start: str, end: str) -> bytes:
    try:
        current = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        raise IntegrityError(f"不能读取 Managed Block：{path}") from exc
    if current.count(start) != 1 or current.count(end) != 1 or current.index(start) >= current.index(end):
        raise IntegrityError(f"Managed Block 缺失、重复或顺序错误：{path}")
    content = current.split(start, 1)[1].split(end, 1)[0].strip()
    return (content + "\n").encode("utf-8")


def _install_bootstrap(root: Path) -> None:
    _merge_marked(
        root / "AGENTS.md",
        bootstrap_bytes().decode("utf-8"),
        BOOTSTRAP_START,
        BOOTSTRAP_END,
    )
    _merge_marked(
        root / ".gitignore",
        GITIGNORE_CONTENT,
        GITIGNORE_START,
        GITIGNORE_END,
    )


def _validated_release(
    candidate: Path,
    artifact: dict[str, Any],
    context: dict[str, Any],
) -> dict[str, Any]:
    manifest = artifact.get("manifest")
    if not isinstance(manifest, dict):
        raise IntegrityError("Candidate 缺少 Release Manifest")
    verify_release(manifest, candidate)
    report = context.get("report")
    source = context.get("source")
    if (
        not isinstance(report, dict)
        or report.get("schema_version") != "yuan.conformance-report/v1"
        or report.get("status") != "PASS"
        or report.get("harness_digest") != harness_digest()
    ):
        raise IntegrityError("Conformance Report 没有证明当前 Harness")
    checks = report.get("checks")
    if not isinstance(checks, dict):
        raise IntegrityError("Conformance Report Checks 不合法")
    if not REQUIRED_CONFORMANCE_CHECKS <= set(checks) or any(
        not isinstance(checks[name], dict) or checks[name].get("status") != "PASS"
        for name in REQUIRED_CONFORMANCE_CHECKS
    ):
        raise IntegrityError("Conformance Report 没有通过全部 Required Check")
    release_check = checks.get("reproducible_release", {})
    if not isinstance(release_check, dict):
        raise IntegrityError("Conformance Release Check 不合法")
    if release_check.get("status") != "PASS" or release_check.get("artifact_digest") != artifact["digest"]:
        raise IntegrityError("Conformance Report 没有绑定 Candidate Artifact")
    if not isinstance(source, dict) or source.get("schema_version") != "yuan.release-source/v1" or not verify_digest(source):
        raise IntegrityError("Release Source Binding 不合法")
    return with_digest({
        "schema_version": "yuan.deployment-proof/v1",
        "manifest_digest": manifest["digest"],
        "conformance_digest": digest_bytes(canonical_bytes(report)),
        "conformance_harness_digest": report["harness_digest"],
        "source": source,
    })


def _write_release_evidence(root: Path, artifact: dict[str, Any], context: dict[str, Any]) -> None:
    atomic_write(root / ".yuan" / "release-manifest.json", canonical_bytes(artifact["manifest"]))
    atomic_write(root / ".yuan" / "conformance-report.json", canonical_bytes(context["report"]))


def _install_record(root: Path, artifact: dict[str, Any], proof: dict[str, Any]) -> dict[str, Any]:
    protocol = root / ".yuan" / "protocol.md"
    adapter = root / ".yuan" / "adapters" / "codex-audited.json"
    capability = _read_object(root / CAPABILITY_MANIFEST_PATH, "Capability Profile Manifest")
    record = with_digest({
        "schema_version": "yuan.project-install/v3",
        "framework_version": __version__,
        "runtime": {"path": ".yuan/bin/yuan.pyz", "digest": artifact["digest"], "bytes": artifact["bytes"]},
        "protocol_digest": digest_bytes(protocol.read_bytes()),
        "bootstrap_digest": digest_bytes(bootstrap_bytes()),
        "adapter_digest": digest_bytes(adapter.read_bytes()),
        "capability_profile": {
            "id": capability["profile_id"],
            "version": capability["profile_version"],
            "manifest_digest": capability["digest"],
            "files": capability["files"],
        },
        "release": proof,
    })
    atomic_write(root / ".yuan" / "install.json", canonical_bytes(record))
    return record


def _write_adapter(root: Path) -> None:
    atomic_write(
        root / ".yuan" / "adapters" / "codex-audited.json",
        canonical_bytes(codex_descriptor()),
    )


def _write_capabilities(root: Path) -> dict[str, Any]:
    """安装发行包托管的能力文件；项目自定义能力位于独立目录。"""

    for relative, payload in capability_payloads():
        atomic_write(root / relative, payload)
    manifest = with_digest(capability_manifest())
    atomic_write(root / CAPABILITY_MANIFEST_PATH, canonical_bytes(manifest))
    (root / ".yuan" / "extensions" / "custom").mkdir(parents=True, exist_ok=True)
    return manifest


def _read_object(path: Path, label: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise IntegrityError(f"{label} 不存在或不是合法 JSON") from exc
    if not isinstance(value, dict):
        raise IntegrityError(f"{label} 必须是 JSON Object")
    return value


def _verify_installation(root: Path) -> dict[str, Any]:
    record = _read_object(root / ".yuan" / "install.json", "Install Record")
    if record.get("schema_version") not in {"yuan.project-install/v1", "yuan.project-install/v2", "yuan.project-install/v3"} or not verify_digest(record):
        raise IntegrityError("Install Record Digest 或版本不合法")
    runtime = root / ".yuan" / "bin" / "yuan.pyz"
    if not runtime.is_file():
        raise IntegrityError("安装 Runtime 不存在")
    expected = record.get("runtime", {})
    if not isinstance(expected, dict):
        raise IntegrityError("Install Record Runtime Binding 不合法")
    if digest_bytes(runtime.read_bytes()) != expected.get("digest") or runtime.stat().st_size != expected.get("bytes"):
        raise IntegrityError("安装 Runtime 与 Install Record 不匹配")
    checks = {
        root / ".yuan" / "protocol.md": record.get("protocol_digest"),
        root / ".yuan" / "adapters" / "codex-audited.json": record.get("adapter_digest"),
    }
    for path, expected_digest in checks.items():
        if not path.is_file() or digest_bytes(path.read_bytes()) != expected_digest:
            raise IntegrityError(f"安装文件与 Install Record 不匹配：{path.name}")
    if digest_bytes(_managed_bytes(root / "AGENTS.md", BOOTSTRAP_START, BOOTSTRAP_END)) != record.get("bootstrap_digest"):
        raise IntegrityError("Agent Bootstrap 与 Install Record 不匹配")
    if record["schema_version"] == "yuan.project-install/v3":
        profile = record.get("capability_profile")
        manifest = _read_object(root / CAPABILITY_MANIFEST_PATH, "Capability Profile Manifest")
        if (
            not isinstance(profile, dict)
            or manifest.get("schema_version") != "yuan.capability-profile/v1"
            or not verify_digest(manifest)
            or manifest.get("digest") != profile.get("manifest_digest")
            or manifest.get("profile_id") != profile.get("id")
            or manifest.get("profile_version") != profile.get("version")
            or manifest.get("files") != profile.get("files")
        ):
            raise IntegrityError("Capability Profile 与 Install Record 不匹配")
        for item in manifest["files"]:
            path = root / item["path"]
            if (
                not path.is_file()
                or digest_bytes(path.read_bytes()) != item.get("digest")
                or path.stat().st_size != item.get("bytes")
            ):
                raise IntegrityError(f"Capability 文件缺失或损坏：{item.get('path')}")
    if record["schema_version"] in {"yuan.project-install/v2", "yuan.project-install/v3"}:
        proof = record.get("release")
        if not isinstance(proof, dict) or not verify_digest(proof):
            raise IntegrityError("Deployment Proof 不合法")
        manifest_path = root / ".yuan" / "release-manifest.json"
        report_path = root / ".yuan" / "conformance-report.json"
        manifest = _read_object(manifest_path, "Release Manifest")
        report = _read_object(report_path, "Conformance Report")
        if manifest.get("digest") != proof.get("manifest_digest") or digest_bytes(canonical_bytes(report)) != proof.get("conformance_digest"):
            raise IntegrityError("部署 Evidence 与 Install Record 不匹配")
        if report.get("harness_digest") != proof.get("conformance_harness_digest"):
            raise IntegrityError("Conformance Harness Binding 不匹配")
        source = proof.get("source")
        if not isinstance(source, dict) or not verify_digest(source):
            raise IntegrityError("Release Source Binding 不合法")
        verify_release(manifest, runtime)
    return record


def _capture(root: Path, relatives: tuple[str, ...]) -> dict[str, bytes | None]:
    return {relative: (root / relative).read_bytes() if (root / relative).is_file() else None for relative in relatives}


def _restore(root: Path, captured: dict[str, bytes | None]) -> None:
    for relative, payload in captured.items():
        path = root / relative
        if payload is None:
            if path.is_file():
                path.unlink()
        else:
            atomic_write(path, payload)


def _snapshot_deployment(root: Path) -> dict[str, Any]:
    record = _verify_installation(root)
    runtime_digest = record["runtime"]["digest"]
    target = root / ".yuan" / "releases" / runtime_digest
    manifest_path = target / "snapshot.json"
    if manifest_path.is_file():
        return _load_snapshot(root, runtime_digest)
    files = []
    for relative in DEPLOYMENT_FILES:
        source = root / relative
        if source.is_file():
            payload = source.read_bytes()
            atomic_write(target / "files" / relative, payload)
            files.append({"path": relative, "digest": digest_bytes(payload), "bytes": len(payload)})
    blocks = {
        "bootstrap": _managed_bytes(root / "AGENTS.md", BOOTSTRAP_START, BOOTSTRAP_END),
        "gitignore": _managed_bytes(root / ".gitignore", GITIGNORE_START, GITIGNORE_END),
    }
    for name, payload in blocks.items():
        atomic_write(target / f"{name}.txt", payload)
    manifest = with_digest({
        "schema_version": "yuan.deployment-snapshot/v1",
        "runtime_digest": runtime_digest,
        "framework_version": record["framework_version"],
        "files": files,
        "blocks": {name: digest_bytes(payload) for name, payload in blocks.items()},
    })
    atomic_write(manifest_path, canonical_bytes(manifest))
    return manifest


def _load_snapshot(root: Path, runtime_digest: str) -> dict[str, Any]:
    if len(runtime_digest) != 64 or any(character not in "0123456789abcdef" for character in runtime_digest):
        raise ValidationError("Rollback Digest 必须是 SHA-256")
    target = root / ".yuan" / "releases" / runtime_digest
    manifest = _read_object(target / "snapshot.json", "Deployment Snapshot")
    if manifest.get("schema_version") != "yuan.deployment-snapshot/v1" or not verify_digest(manifest):
        raise IntegrityError("Deployment Snapshot Digest 不合法")
    if manifest.get("runtime_digest") != runtime_digest:
        raise IntegrityError("Deployment Snapshot Identity 不匹配")
    files = manifest.get("files")
    blocks = manifest.get("blocks")
    if not isinstance(files, list) or not isinstance(blocks, dict):
        raise IntegrityError("Deployment Snapshot 结构不合法")
    paths = []
    for item in files:
        if not isinstance(item, dict) or item.get("path") not in DEPLOYMENT_FILES:
            raise IntegrityError("Deployment Snapshot 包含未知路径")
        paths.append(item["path"])
        source = target / "files" / item["path"]
        if not source.is_file():
            raise IntegrityError("Deployment Snapshot 文件缺失")
        payload = source.read_bytes()
        if digest_bytes(payload) != item.get("digest") or len(payload) != item.get("bytes"):
            raise IntegrityError("Deployment Snapshot 文件损坏")
    required = set(DEPLOYMENT_FILES[:5])
    if len(paths) != len(set(paths)) or not required <= set(paths):
        raise IntegrityError("Deployment Snapshot 文件集合不完整或重复")
    if set(blocks) != {"bootstrap", "gitignore"}:
        raise IntegrityError("Deployment Snapshot Managed Block 集合不合法")
    for name, expected in blocks.items():
        block = target / f"{name}.txt"
        if not block.is_file() or digest_bytes(block.read_bytes()) != expected:
            raise IntegrityError("Deployment Snapshot Managed Block 损坏")
    return manifest


def _cleanup_candidates(root: Path, keep_digest: str | None = None) -> None:
    candidates = root / ".yuan" / "candidates"
    if not candidates.is_dir():
        return
    for path in candidates.iterdir():
        if path.is_file() and path.suffix in {".pyz", ".json"} and (keep_digest is None or not path.name.startswith(keep_digest)):
            path.unlink()


def _pinned_status(root: Path, runtime: Path) -> dict[str, Any]:
    try:
        completed = subprocess.run(
            [sys.executable, "-B", str(runtime), "--root", str(root), "status"],
            cwd=root,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=60,
            check=False,
            shell=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise IntegrityError("项目固定 Runtime 无法执行") from exc
    try:
        value = json.loads(completed.stdout.decode("utf-8"))
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise IntegrityError("项目固定 Runtime 没有返回合法 JSON") from exc
    if completed.returncode != 0 or not isinstance(value, dict):
        raise IntegrityError(f"项目固定 Runtime 状态检查失败：{value}")
    return value


def install_project(
    root: Path,
    *,
    release_context: dict[str, Any],
    profile: str = "AUDITED",
    run_id: str | None = None,
) -> dict[str, Any]:
    root = root.resolve()
    if not root.is_dir():
        raise ValidationError(f"目标项目目录不存在：{root}")
    if profile != "AUDITED":
        raise ValidationError("轻量项目安装器当前只提供 Codex AUDITED Adapter")
    run_id = _resolved_run_id(run_id)
    lock = root / ".yuan" / ".deployment.lock"
    with exclusive_lock(lock, timeout=DEPLOYMENT_LOCK_TIMEOUT):
        if (root / ".yuan" / "config.json").exists():
            raise ValidationError("目标项目已安装 Yuan；请使用 project update")
        agents = _merged_marked(root / "AGENTS.md", bootstrap_bytes().decode("utf-8"), BOOTSTRAP_START, BOOTSTRAP_END)
        ignored = _merged_marked(root / ".gitignore", GITIGNORE_CONTENT, GITIGNORE_START, GITIGNORE_END)
        captured = _capture(root, INSTALL_TRANSACTION_FILES)
        run_root = root / ".yuan-run" / "runs" / run_id
        candidate = root / ".yuan" / "candidates" / f"install-{os.getpid()}.pyz"
        artifact = build_runtime_zipapp(candidate)
        try:
            proof = _validated_release(candidate, artifact, release_context)
            runtime = root / ".yuan" / "bin" / "yuan.pyz"
            atomic_write(runtime, candidate.read_bytes())
            _write_adapter(root)
            _write_capabilities(root)
            atomic_write(root / "AGENTS.md", agents)
            atomic_write(root / ".gitignore", ignored)
            initialized = initialize_repository(root, profile, run_id)
            _write_release_evidence(root, artifact, release_context)
            record = _install_record(root, artifact, proof)
            status = _pinned_status(root, runtime)
        except Exception:
            _restore(root, captured)
            if run_root.is_dir():
                shutil.rmtree(run_root)
            raise
        finally:
            if candidate.is_file():
                candidate.unlink()
        _cleanup_candidates(root)
        return {
            "status": "INSTALLED",
            "root": str(root),
            "run_id": initialized["run_id"],
            "profile": initialized["profile"],
            "runtime_digest": artifact["digest"],
            "install_digest": record["digest"],
            "release_proof": proof,
            "decision": status["decision"],
            "agent_guidance": agent_guidance(root),
        }


def _read_install_config(root: Path) -> dict[str, Any]:
    path = root / ".yuan" / "config.json"
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise IntegrityError("目标项目 Yuan Config 不合法") from exc
    if not isinstance(value, dict) or not verify_digest(value):
        raise IntegrityError("目标项目 Yuan Config Digest 不匹配")
    return value


def update_project(root: Path, *, release_context: dict[str, Any]) -> dict[str, Any]:
    root = root.resolve()
    runtime = root / ".yuan" / "bin" / "yuan.pyz"
    with exclusive_lock(root / ".yuan" / ".deployment.lock", timeout=DEPLOYMENT_LOCK_TIMEOUT):
        if not (root / ".yuan" / "config.json").is_file() or not runtime.is_file():
            raise ValidationError("目标项目没有可更新的 Yuan 安装")
        current_status = _pinned_status(root, runtime)
        current_record = _verify_installation(root)
        current_digest = current_record["runtime"]["digest"]
        candidate = root / ".yuan" / "candidates" / f"yuan-{os.getpid()}.pyz"
        artifact = build_runtime_zipapp(candidate)
        try:
            proof = _validated_release(candidate, artifact, release_context)
            if artifact["digest"] == current_digest:
                _cleanup_candidates(root)
                return {
                    "status": "UNCHANGED",
                    "root": str(root),
                    "runtime_digest": current_digest,
                    "install_digest": current_record["digest"],
                    "release_proof": current_record.get("release"),
                    "agent_guidance": agent_guidance(root),
                }
            work = current_status.get("work")
            result = current_status.get("decision", {}).get("result")
            errors = current_status.get("errors")
            safe_empty = work is None and errors == [] and current_status.get("source_count") == 0
            safe_terminal = work is not None and result in SAFE_UPDATE_RESULTS and errors == []
            if not (safe_empty or safe_terminal):
                staged = candidate.with_name(f"{artifact['digest']}.pyz")
                os.replace(candidate, staged)
                metadata = with_digest({
                    "schema_version": "yuan.staged-release/v1",
                    "artifact": {key: artifact[key] for key in ("path", "digest", "bytes")},
                    "manifest": artifact["manifest"],
                    "proof": proof,
                    "blocked_by_result": result,
                })
                atomic_write(staged.with_suffix(".json"), canonical_bytes(metadata))
                _cleanup_candidates(root, artifact["digest"])
                return {
                    "status": "STAGED",
                    "root": str(root),
                    "runtime_digest": artifact["digest"],
                    "candidate": str(staged.relative_to(root)),
                    "blocked_by_result": result,
                    "agent_guidance": agent_guidance(root),
                }
            snapshot = _snapshot_deployment(root)
            captured = _capture(root, INSTALL_TRANSACTION_FILES)
            try:
                atomic_write(runtime, candidate.read_bytes())
                config = _read_install_config(root)
                protocol = protocol_bytes()
                config["protocol"] = {"id": "yuan.core", "revision": "0.2", "digest": digest_bytes(protocol)}
                config["harness"] = {"id": "yuan.python", "revision": __version__, "digest": harness_digest()}
                config["environment"] = environment_binding()
                atomic_write(root / ".yuan" / "protocol.md", protocol)
                atomic_write(root / ".yuan" / "config.json", canonical_bytes(with_digest(config)))
                _write_adapter(root)
                _write_capabilities(root)
                _install_bootstrap(root)
                _write_release_evidence(root, artifact, release_context)
                record = _install_record(root, artifact, proof)
                verified = _pinned_status(root, runtime)
            except Exception:
                _restore(root, captured)
                raise
            _cleanup_candidates(root)
            return {
                "status": "UPDATED",
                "root": str(root),
                "previous_runtime_digest": current_digest,
                "snapshot_digest": snapshot["runtime_digest"],
                "runtime_digest": artifact["digest"],
                "install_digest": record["digest"],
                "release_proof": proof,
                "decision": verified["decision"],
                "agent_guidance": agent_guidance(root),
            }
        finally:
            if candidate.is_file():
                candidate.unlink()


def rollback_project(root: Path, runtime_digest: str) -> dict[str, Any]:
    """在安全终态恢复完整部署快照，不改写任何 Run Event。"""

    root = root.resolve()
    runtime = root / ".yuan" / "bin" / "yuan.pyz"
    if not runtime.is_file():
        raise ValidationError("目标项目没有可回滚的 Yuan 安装")
    with exclusive_lock(root / ".yuan" / ".deployment.lock", timeout=DEPLOYMENT_LOCK_TIMEOUT):
        current = _pinned_status(root, runtime)
        current_record = _verify_installation(root)
        current_digest = current_record["runtime"]["digest"]
        if runtime_digest == current_digest:
            return {"status": "UNCHANGED", "root": str(root), "runtime_digest": current_digest}
        target = _load_snapshot(root, runtime_digest)
        work = current.get("work")
        errors = current.get("errors")
        result = current.get("decision", {}).get("result")
        safe_empty = work is None and errors == [] and current.get("source_count") == 0
        safe_terminal = work is not None and result == "COMPLETE" and errors == []
        snapshot_root = root / ".yuan" / "releases" / runtime_digest
        target_config = _read_object(snapshot_root / "files" / ".yuan/config.json", "Snapshot Config")
        bindings_match = work is None or (
            work.get("profile") == target_config.get("profile")
            and work.get("protocol") == target_config.get("protocol")
            and work.get("harness") == target_config.get("harness")
            and work.get("artifact", {}).get("environment") == target_config.get("environment")
        )
        if not (safe_empty or safe_terminal) or not bindings_match:
            raise ValidationError("当前 Run 或 Work Binding 不允许恢复该部署快照")
        _snapshot_deployment(root)
        captured = _capture(root, INSTALL_TRANSACTION_FILES)
        try:
            available = {item["path"] for item in target["files"]}
            for relative in DEPLOYMENT_FILES:
                destination = root / relative
                if relative in available:
                    atomic_write(destination, (snapshot_root / "files" / relative).read_bytes())
                elif destination.is_file():
                    destination.unlink()
            _merge_marked(
                root / "AGENTS.md",
                (snapshot_root / "bootstrap.txt").read_text(encoding="utf-8"),
                BOOTSTRAP_START,
                BOOTSTRAP_END,
            )
            _merge_marked(
                root / ".gitignore",
                (snapshot_root / "gitignore.txt").read_text(encoding="utf-8"),
                GITIGNORE_START,
                GITIGNORE_END,
            )
            restored_record = _verify_installation(root)
            verified = _pinned_status(root, runtime)
        except Exception:
            _restore(root, captured)
            raise
        _cleanup_candidates(root)
        return {
            "status": "ROLLED_BACK",
            "root": str(root),
            "previous_runtime_digest": current_digest,
            "runtime_digest": runtime_digest,
            "install_digest": restored_record["digest"],
            "decision": verified["decision"],
            "agent_guidance": agent_guidance(root),
        }


def project_status(root: Path) -> dict[str, Any]:
    root = root.resolve()
    runtime = root / ".yuan" / "bin" / "yuan.pyz"
    if not runtime.is_file():
        raise ValidationError("目标项目没有 Yuan 安装")
    with exclusive_lock(root / ".yuan" / ".deployment.lock", timeout=DEPLOYMENT_LOCK_TIMEOUT):
        record = _verify_installation(root)
        projection = _pinned_status(root, runtime)
        candidates = []
        candidate_root = root / ".yuan" / "candidates"
        if candidate_root.is_dir():
            for path in sorted(candidate_root.glob("*.json")):
                value = _read_object(path, "Staged Release")
                if value.get("schema_version") != "yuan.staged-release/v1" or not verify_digest(value):
                    raise IntegrityError("Staged Release Metadata 不合法")
                artifact = value.get("artifact")
                proof = value.get("proof")
                if not isinstance(artifact, dict) or not isinstance(proof, dict) or not verify_digest(proof):
                    raise IntegrityError("Staged Release Binding 不合法")
                staged = candidate_root / f"{artifact.get('digest')}.pyz"
                if not staged.is_file() or digest_bytes(staged.read_bytes()) != artifact.get("digest"):
                    raise IntegrityError("Staged Release Artifact 不存在或损坏")
                verify_release(value.get("manifest"), staged)
                candidates.append({
                    "runtime_digest": artifact["digest"],
                    "blocked_by_result": value["blocked_by_result"],
                })
        return {
            "status": "PASS",
            "root": str(root),
            "framework_version": record["framework_version"],
            "runtime_digest": record["runtime"]["digest"],
            "source": record.get("release", {}).get("source"),
            "capability_profile": record.get("capability_profile"),
            "staged": candidates,
            "decision": projection["decision"],
        }
