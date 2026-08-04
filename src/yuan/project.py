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
    available_profiles,
    capability_manifest,
    capability_paths,
    capability_payloads,
)
from .errors import IntegrityError, ValidationError, YuanError
from .identity import environment_binding, harness_digest, protocol_bytes, protocol_revision
from .ledger import Ledger, atomic_write, exclusive_lock
from .release import build_runtime_zipapp, verify_release
from .validate import identifier, with_digest


BOOTSTRAP_START = "<!-- yuan:bootstrap:start -->"
BOOTSTRAP_END = "<!-- yuan:bootstrap:end -->"
GITIGNORE_START = "# yuan:managed:start"
GITIGNORE_END = "# yuan:managed:end"
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
GITIGNORE_CONTENT = ".yuan-run/\n.yuan/drafts/\n.yuan/candidates/\n.yuan/releases/"
REQUIRED_CONFORMANCE_CHECKS = {
    "unit_tests", "schemas", "adapter", "bootstrap", "capability_profile", "automation", "size_budget", "reproducible_release"
}


def agent_guidance(root: Path, capability_profile: str = DEFAULT_PROFILE) -> dict[str, str]:
    """返回安装后可直接交给 Agent 的开始与继续提示。"""

    return {
        "project_root": str(root.resolve()),
        "status_command": "python -B .yuan/bin/yuan.pyz --root . status",
        "capability_profile": capability_profile,
        "start_prompt": (
            "请读取项目根目录 AGENTS.md，并按照 Yuan Agent Bootstrap 从 Intake 开始新需求；"
            "需要时向我提问，并在需求摘要和完整 Work 两个节点等待我确认。"
            "我的需求是：<在这里描述需求>"
        ),
        "continue_prompt": (
            "请读取项目根目录 AGENTS.md，运行 memory resume 恢复项目连续性并检查 Yuan 当前状态，然后按照 Yuan Agent Bootstrap "
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
    capability = None
    capability_path = root / CAPABILITY_MANIFEST_PATH
    if capability_path.is_file():
        installed_capability = _read_object(capability_path, "Capability Profile Manifest")
        if not verify_digest(installed_capability):
            raise IntegrityError("初始化时 Capability Profile Manifest 不合法")
        capability = {
            "id": installed_capability["profile_id"],
            "revision": installed_capability["profile_version"],
            "digest": installed_capability["digest"],
        }
    atomic_write(root / ".yuan" / "protocol.md", protocol)
    config = with_digest({
        "schema_version": "yuan.config/v1",
        "profile": profile,
        "protocol": {"id": "yuan.core", "revision": protocol_revision(protocol), "digest": digest_bytes(protocol)},
        "harness": {"id": "yuan.python", "revision": __version__, "digest": harness_digest()},
        "state_root": ".yuan-run",
        "artifact_exclude": [".yuan-run/**", "docs/memory/**", ".git/**", "__pycache__/**", "*.pyc"],
        "environment": environment_binding(),
        "capability": capability,
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


def _force_merged_marked(path: Path, content: str, start: str, end: str) -> bytes:
    """替换所有可识别的托管块；损坏的旧标记不能阻止框架修复。"""

    block = f"{start}\n{content.strip()}\n{end}\n"
    if not path.exists():
        return block.encode("utf-8")
    try:
        lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
    except (OSError, UnicodeError) as exc:
        raise ValidationError(f"不能读取 UTF-8 文件：{path}") from exc
    preserved: list[str] = []
    inside = False
    for line in lines:
        marker = line.strip()
        if marker == start:
            inside = True
            continue
        if marker == end:
            inside = False
            continue
        if not inside:
            preserved.append(line)
    prefix = "".join(preserved).rstrip()
    merged = (prefix + "\n\n" if prefix else "") + block
    return merged.encode("utf-8")


def _managed_bytes(path: Path, start: str, end: str) -> bytes:
    try:
        current = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        raise IntegrityError(f"不能读取 Managed Block：{path}") from exc
    if current.count(start) != 1 or current.count(end) != 1 or current.index(start) >= current.index(end):
        raise IntegrityError(f"Managed Block 缺失、重复或顺序错误：{path}")
    content = current.split(start, 1)[1].split(end, 1)[0].strip()
    return (content + "\n").encode("utf-8")


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


def _write_capabilities(root: Path, profile_id: str) -> dict[str, Any]:
    """安装发行包托管的能力文件；项目自定义能力位于独立目录。"""

    for relative, payload in capability_payloads(profile_id):
        atomic_write(root / relative, payload)
    manifest = with_digest(capability_manifest(profile_id))
    atomic_write(root / CAPABILITY_MANIFEST_PATH, canonical_bytes(manifest))
    (root / ".yuan" / "extensions" / "custom").mkdir(parents=True, exist_ok=True)
    return manifest


def _deployment_files_for_profile(profile_id: str) -> tuple[str, ...]:
    return CORE_DEPLOYMENT_FILES + capability_paths(profile_id)


def _transaction_files(*groups: tuple[str, ...]) -> tuple[str, ...]:
    values = [item for group in groups for item in group]
    values.extend((
        "AGENTS.md", ".gitignore", ".yuan-run/current.json", "docs/memory/index.json",
        "docs/memory/INDEX.md", "docs/memory/CURRENT.md", "docs/memory/PROJECT.md",
        "docs/memory/views/ARCHITECTURE.md", "docs/memory/views/DECISIONS.md",
        "docs/memory/views/PITFALLS.md", "docs/memory/views/CONVENTIONS.md",
    ))
    return tuple(dict.fromkeys(values))


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
            or manifest.get("schema_version") not in {"yuan.capability-profile/v1", "yuan.capability-profile/v2"}
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


def _cleanup_candidates(root: Path, keep_digest: str | None = None) -> None:
    candidates = root / ".yuan" / "candidates"
    if not candidates.is_dir():
        return
    for path in candidates.iterdir():
        if path.is_file() and path.suffix in {".pyz", ".json"} and (keep_digest is None or not path.name.startswith(keep_digest)):
            path.unlink()


def _memory_identity(root: Path) -> dict[str, Any]:
    """计算更新必须逐字节保留的项目记忆指纹。"""

    values: dict[str, Any] = {}
    for label, memory_root in (
        ("run_ledger", root / ".yuan-run"),
        ("long_term", root / "docs" / "memory"),
    ):
        if not memory_root.exists():
            values[label] = {"exists": False, "files": 0, "digest": None}
            continue
        files = []
        if memory_root.is_file() or memory_root.is_symlink():
            paths = [memory_root]
        else:
            paths = sorted(path for path in memory_root.rglob("*") if path.is_file() or path.is_symlink())
        for path in paths:
            relative = path.relative_to(root).as_posix()
            if path.is_symlink():
                payload = os.readlink(path).encode("utf-8")
                kind = "symlink"
            else:
                payload = path.read_bytes()
                kind = "file"
            files.append({"path": relative, "kind": kind, "bytes": len(payload), "digest": digest_bytes(payload)})
        values[label] = {
            "exists": True,
            "files": len(files),
            "digest": digest_bytes(canonical_bytes(files)),
        }
    return values


def _forced_release_context(root: Path, artifact: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    """为无门禁更新记录来源事实；该记录不是 Conformance 声明。"""

    source = with_digest({
        "schema_version": "yuan.release-source/v1",
        "kind": "forced-update",
        "revision": __version__,
        "dirty": True,
    })
    report = {
        "schema_version": "yuan.conformance-report/v1",
        "status": "SKIPPED",
        "harness_digest": harness_digest(),
        "checks": {},
        "reason": "project update 强制激活当前 Yuan Source，不使用 Conformance 准入",
    }
    context = {"report": report, "source": source}
    proof = with_digest({
        "schema_version": "yuan.deployment-proof/v1",
        "manifest_digest": artifact["manifest"]["digest"],
        "conformance_digest": digest_bytes(canonical_bytes(report)),
        "conformance_harness_digest": report["harness_digest"],
        "source": source,
        "activation": "FORCED_UPDATE",
    })
    return context, proof


def _fresh_config(capability_profile: str) -> dict[str, Any]:
    protocol = protocol_bytes()
    capability = capability_manifest(capability_profile)
    return with_digest({
        "schema_version": "yuan.config/v1",
        "profile": "AUDITED",
        "protocol": {"id": "yuan.core", "revision": protocol_revision(protocol), "digest": digest_bytes(protocol)},
        "harness": {"id": "yuan.python", "revision": __version__, "digest": harness_digest()},
        "state_root": ".yuan-run",
        "artifact_exclude": [".yuan-run/**", "docs/memory/**", ".git/**", "__pycache__/**", "*.pyc"],
        "environment": environment_binding(),
        "capability": {
            "id": capability["profile_id"],
            "revision": capability["profile_version"],
            "digest": capability["digest"],
        },
    })


def _remove_managed_capabilities(root: Path) -> None:
    extensions = root / ".yuan" / "extensions"
    if not extensions.is_dir():
        return
    for path in extensions.iterdir():
        if path.name == "custom":
            continue
        if path.is_dir() and not path.is_symlink():
            shutil.rmtree(path)
        elif path.exists() or path.is_symlink():
            path.unlink()


def _initialize_run_ledger_if_missing(root: Path) -> str | None:
    state = root / ".yuan-run"
    if state.exists():
        return None
    run_id = _resolved_run_id(None)
    ledger = Ledger(state, run_id)
    ledger.run_root.mkdir(parents=True, exist_ok=False)
    atomic_write(state / "current.json", canonical_bytes({"run_id": run_id}))
    return run_id


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
    stdout = completed.stdout.decode("utf-8", errors="replace")
    stderr = completed.stderr.decode("utf-8", errors="replace")
    try:
        value = json.loads(stdout)
    except json.JSONDecodeError as exc:
        raise IntegrityError(
            f"项目 Runtime 没有返回合法 JSON；exit_code={completed.returncode}；"
            f"stdout={stdout[-4000:]!r}；stderr={stderr[-4000:]!r}"
        ) from exc
    if completed.returncode != 0 or not isinstance(value, dict):
        raise IntegrityError(
            f"项目 Runtime 状态检查失败；exit_code={completed.returncode}；"
            f"stdout={stdout[-4000:]!r}；stderr={stderr[-4000:]!r}"
        )
    return value


def diagnose_project(root: Path) -> dict[str, Any]:
    """不信任旧安装的外部只读诊断；失败细节用于 Runtime Maintainer。"""

    root = root.resolve()
    if not root.is_dir():
        return {"status": "ERROR", "stage": "target", "root": str(root), "error": "目标项目目录不存在"}
    runtime = root / ".yuan" / "bin" / "yuan.pyz"
    managed = {
        relative: {"exists": (root / relative).is_file()}
        for relative in CORE_DEPLOYMENT_FILES
    }
    runtime_check: dict[str, Any]
    if not runtime.is_file():
        runtime_check = {"status": "MISSING", "command": "python -B .yuan/bin/yuan.pyz --root . status"}
    else:
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
            runtime_check = {
                "status": "PASS" if completed.returncode == 0 else "FAIL",
                "command": "python -B .yuan/bin/yuan.pyz --root . status",
                "exit_code": completed.returncode,
                "stdout": completed.stdout.decode("utf-8", errors="replace"),
                "stderr": completed.stderr.decode("utf-8", errors="replace"),
            }
        except (OSError, subprocess.TimeoutExpired) as exc:
            runtime_check = {"status": "FAIL", "command": "python -B .yuan/bin/yuan.pyz --root . status", "error": str(exc)}
    return {
        "status": "PASS",
        "stage": "diagnose",
        "root": str(root),
        "writable": os.access(root, os.W_OK),
        "managed": managed,
        "memory": _memory_identity(root),
        "runtime": runtime_check,
        "recommended_agent": "runtime-maintainer",
        "recommended_skill": "runtime-recovery",
        "recovery_command": f"python -B scripts/sync_project.py update {root}",
    }


def install_project(
    root: Path,
    *,
    release_context: dict[str, Any],
    profile: str = "AUDITED",
    capability_profile: str = DEFAULT_PROFILE,
    run_id: str | None = None,
) -> dict[str, Any]:
    root = root.resolve()
    if not root.is_dir():
        raise ValidationError(f"目标项目目录不存在：{root}")
    if profile != "AUDITED":
        raise ValidationError("轻量项目安装器当前只提供 Codex AUDITED Adapter")
    if capability_profile not in available_profiles():
        raise ValidationError(f"发行包不包含 Capability Profile：{capability_profile}")
    run_id = _resolved_run_id(run_id)
    lock = root / ".yuan" / ".deployment.lock"
    with exclusive_lock(lock, timeout=DEPLOYMENT_LOCK_TIMEOUT):
        if (root / ".yuan" / "config.json").exists():
            raise ValidationError("目标项目已安装 Yuan；请使用 project update")
        agents = _merged_marked(root / "AGENTS.md", bootstrap_bytes().decode("utf-8"), BOOTSTRAP_START, BOOTSTRAP_END)
        ignored = _merged_marked(root / ".gitignore", GITIGNORE_CONTENT, GITIGNORE_START, GITIGNORE_END)
        deployment_files = _deployment_files_for_profile(capability_profile)
        captured = _capture(root, _transaction_files(deployment_files))
        run_root = root / ".yuan-run" / "runs" / run_id
        candidate = root / ".yuan" / "candidates" / f"install-{os.getpid()}.pyz"
        artifact = build_runtime_zipapp(candidate)
        memory_scaffolded = False
        try:
            proof = _validated_release(candidate, artifact, release_context)
            runtime = root / ".yuan" / "bin" / "yuan.pyz"
            atomic_write(runtime, candidate.read_bytes())
            _write_adapter(root)
            _write_capabilities(root, capability_profile)
            atomic_write(root / "AGENTS.md", agents)
            atomic_write(root / ".gitignore", ignored)
            initialized = initialize_repository(root, profile, run_id)
            memory_root = root / "docs" / "memory"
            if not memory_root.is_dir() or not any(path.is_file() for path in memory_root.rglob("*")):
                from .memory import rebuild_memory

                rebuild_memory(root)
                memory_scaffolded = True
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
            "memory_scaffolded": memory_scaffolded,
            "release_proof": proof,
            "decision": status["decision"],
            "agent_guidance": agent_guidance(root, capability_profile),
        }


def update_project(
    root: Path,
    *,
    release_context: dict[str, Any] | None = None,
    capability_profile: str | None = None,
) -> dict[str, Any]:
    """用当前 Yuan Source 强制重建托管框架层。

    更新不依赖旧 Runtime、Install Record、Active Work 或 Conformance；项目
    Ledger 与长期记忆必须保持逐字节不变。逐文件原子写入用于避免半个文件，
    但不会把失败回滚成旧框架。
    """

    root = root.resolve()
    if not root.is_dir():
        raise ValidationError(f"目标项目目录不存在：{root}")
    runtime = root / ".yuan" / "bin" / "yuan.pyz"
    with exclusive_lock(root / ".yuan" / ".deployment.lock", timeout=DEPLOYMENT_LOCK_TIMEOUT):
        capability_profile = capability_profile or DEFAULT_PROFILE
        if capability_profile not in available_profiles():
            raise ValidationError(f"新发行包不提供目标 Capability Profile：{capability_profile}")
        memory_before = _memory_identity(root)
        candidate = root / ".yuan" / "candidates" / f"yuan-{os.getpid()}.pyz"
        artifact = build_runtime_zipapp(candidate)
        try:
            context, proof = _forced_release_context(root, artifact)
            atomic_write(runtime, candidate.read_bytes())
            _remove_managed_capabilities(root)
            _write_capabilities(root, capability_profile)
            protocol = protocol_bytes()
            atomic_write(root / ".yuan" / "protocol.md", protocol)
            atomic_write(root / ".yuan" / "config.json", canonical_bytes(_fresh_config(capability_profile)))
            _write_adapter(root)
            atomic_write(
                root / "AGENTS.md",
                _force_merged_marked(root / "AGENTS.md", bootstrap_bytes().decode("utf-8"), BOOTSTRAP_START, BOOTSTRAP_END),
            )
            atomic_write(
                root / ".gitignore",
                _force_merged_marked(root / ".gitignore", GITIGNORE_CONTENT, GITIGNORE_START, GITIGNORE_END),
            )
            _write_release_evidence(root, artifact, context)
            record = _install_record(root, artifact, proof)
            initialized_run = _initialize_run_ledger_if_missing(root)
            _cleanup_candidates(root)
            diagnostics: dict[str, Any]
            try:
                verified = _pinned_status(root, runtime)
                diagnostics = {"status": "PASS", "decision": verified.get("decision")}
            except Exception as exc:
                diagnostics = {"status": "WARNING", "error": str(exc)}
            memory_after = _memory_identity(root)
            changed_memory = [
                label for label, before in memory_before.items()
                if before["exists"] and memory_after[label] != before
            ]
            if changed_memory:
                raise IntegrityError("强制更新意外修改了项目 Memory：" + ", ".join(changed_memory))
            return {
                "status": "UPDATED",
                "root": str(root),
                "runtime_digest": artifact["digest"],
                "install_digest": record["digest"],
                "release_proof": proof,
                "memory_preserved": True,
                "memory_initialized_run": initialized_run,
                "memory": memory_after,
                "diagnostics": diagnostics,
                "agent_guidance": agent_guidance(root, capability_profile),
            }
        finally:
            if candidate.is_file():
                candidate.unlink()


def project_status(root: Path) -> dict[str, Any]:
    root = root.resolve()
    runtime = root / ".yuan" / "bin" / "yuan.pyz"
    if not runtime.is_file():
        raise ValidationError("目标项目没有 Yuan 安装")
    with exclusive_lock(root / ".yuan" / ".deployment.lock", timeout=DEPLOYMENT_LOCK_TIMEOUT):
        record = _verify_installation(root)
        projection = _pinned_status(root, runtime)
        return {
            "status": "PASS",
            "root": str(root),
            "framework_version": record["framework_version"],
            "runtime_digest": record["runtime"]["digest"],
            "source": record.get("release", {}).get("source"),
            "capability_profile": record.get("capability_profile"),
            "staged": [],
            "decision": projection["decision"],
        }
