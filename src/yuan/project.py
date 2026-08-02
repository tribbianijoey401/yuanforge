"""把固定版本 Yuan Runtime 安装或同步到 Vibe Coding 项目。"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from importlib import resources
from pathlib import Path
from typing import Any

from . import __version__
from .canonical import canonical_bytes, digest_bytes, verify_digest
from .errors import IntegrityError, ValidationError, YuanError
from .identity import environment_binding, harness_digest, protocol_bytes
from .ledger import Ledger, atomic_write
from .release import build_runtime_zipapp
from .validate import identifier, with_digest


BOOTSTRAP_START = "<!-- yuan:bootstrap:start -->"
BOOTSTRAP_END = "<!-- yuan:bootstrap:end -->"
GITIGNORE_START = "# yuan:managed:start"
GITIGNORE_END = "# yuan:managed:end"
SAFE_UPDATE_RESULTS = {"COMPLETE"}


def agent_guidance(root: Path) -> dict[str, str]:
    """返回安装后可直接交给 Agent 的开始与继续提示。"""

    return {
        "project_root": str(root.resolve()),
        "status_command": "python -B .yuan/bin/yuan.pyz --root . status",
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


def initialize_repository(root: Path, profile: str, run_id: str | None) -> dict[str, Any]:
    root = root.resolve()
    config_path = root / ".yuan" / "config.json"
    if config_path.exists():
        raise YuanError("仓库已经初始化")
    if profile == "ENFORCED":
        raise YuanError("ENFORCED 需要另行安装符合规范的 Action Port Adapter")
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
    if run_id is None:
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        run_id = f"RUN-{stamp}-{os.getpid()}"
    identifier(run_id, "run_id")
    state_root = root / config["state_root"]
    Ledger(state_root, run_id).run_root.mkdir(parents=True, exist_ok=False)
    atomic_write(state_root / "current.json", canonical_bytes({"run_id": run_id}))
    return {"status": "INITIALIZED", "run_id": run_id, "profile": profile, "protocol": config["protocol"], "harness": config["harness"]}


def _merge_marked(path: Path, content: str, start: str, end: str) -> None:
    block = f"{start}\n{content.strip()}\n{end}\n"
    if not path.exists():
        atomic_write(path, block.encode("utf-8"))
        return
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
    atomic_write(path, merged.encode("utf-8"))


def _install_bootstrap(root: Path) -> None:
    _merge_marked(
        root / "AGENTS.md",
        bootstrap_bytes().decode("utf-8"),
        BOOTSTRAP_START,
        BOOTSTRAP_END,
    )
    _merge_marked(
        root / ".gitignore",
        ".yuan-run/\n.yuan/drafts/\n.yuan/candidates/\n.yuan/releases/",
        GITIGNORE_START,
        GITIGNORE_END,
    )


def _install_record(root: Path, artifact: dict[str, Any]) -> dict[str, Any]:
    protocol = root / ".yuan" / "protocol.md"
    adapter = root / ".yuan" / "adapters" / "codex-audited.json"
    record = with_digest({
        "schema_version": "yuan.project-install/v1",
        "framework_version": __version__,
        "runtime": {"path": ".yuan/bin/yuan.pyz", "digest": artifact["digest"], "bytes": artifact["bytes"]},
        "protocol_digest": digest_bytes(protocol.read_bytes()),
        "bootstrap_digest": digest_bytes(bootstrap_bytes()),
        "adapter_digest": digest_bytes(adapter.read_bytes()),
    })
    atomic_write(root / ".yuan" / "install.json", canonical_bytes(record))
    return record


def _write_adapter(root: Path) -> None:
    atomic_write(
        root / ".yuan" / "adapters" / "codex-audited.json",
        canonical_bytes(codex_descriptor()),
    )


def _pinned_status(root: Path, runtime: Path) -> dict[str, Any]:
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
    try:
        value = json.loads(completed.stdout.decode("utf-8"))
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise IntegrityError("项目固定 Runtime 没有返回合法 JSON") from exc
    if completed.returncode != 0 or not isinstance(value, dict):
        raise IntegrityError(f"项目固定 Runtime 状态检查失败：{value}")
    return value


def install_project(root: Path, *, profile: str = "AUDITED", run_id: str | None = None) -> dict[str, Any]:
    root = root.resolve()
    if not root.is_dir():
        raise ValidationError(f"目标项目目录不存在：{root}")
    if profile != "AUDITED":
        raise ValidationError("轻量项目安装器当前只提供 Codex AUDITED Adapter")
    if (root / ".yuan" / "config.json").exists():
        raise ValidationError("目标项目已安装 Yuan；请使用 project update")
    runtime = root / ".yuan" / "bin" / "yuan.pyz"
    artifact = build_runtime_zipapp(runtime)
    _write_adapter(root)
    _install_bootstrap(root)
    initialized = initialize_repository(root, profile, run_id)
    record = _install_record(root, artifact)
    status = _pinned_status(root, runtime)
    return {
        "status": "INSTALLED",
        "root": str(root),
        "run_id": initialized["run_id"],
        "profile": initialized["profile"],
        "runtime_digest": artifact["digest"],
        "install_digest": record["digest"],
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


def update_project(root: Path) -> dict[str, Any]:
    root = root.resolve()
    runtime = root / ".yuan" / "bin" / "yuan.pyz"
    if not (root / ".yuan" / "config.json").is_file() or not runtime.is_file():
        raise ValidationError("目标项目没有可更新的 Yuan 安装")
    current_status = _pinned_status(root, runtime)
    current_digest = digest_bytes(runtime.read_bytes())
    candidate = root / ".yuan" / "candidates" / f"yuan-{os.getpid()}.pyz"
    artifact = build_runtime_zipapp(candidate)
    if artifact["digest"] == current_digest:
        candidate.unlink()
        _write_adapter(root)
        _install_bootstrap(root)
        record = _install_record(root, {**artifact, "path": runtime.name})
        return {
            "status": "UNCHANGED",
            "root": str(root),
            "runtime_digest": current_digest,
            "install_digest": record["digest"],
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
        return {
            "status": "STAGED",
            "root": str(root),
            "runtime_digest": artifact["digest"],
            "candidate": str(staged.relative_to(root)),
            "blocked_by_result": result,
            "agent_guidance": agent_guidance(root),
        }

    managed = [
        runtime,
        root / ".yuan" / "config.json",
        root / ".yuan" / "protocol.md",
        root / ".yuan" / "install.json",
        root / ".yuan" / "adapters" / "codex-audited.json",
        root / "AGENTS.md",
        root / ".gitignore",
    ]
    previous = {path: path.read_bytes() if path.exists() else None for path in managed}
    backup = root / ".yuan" / "releases" / current_digest / "yuan.pyz"
    if backup.exists() and digest_bytes(backup.read_bytes()) != current_digest:
        raise IntegrityError("Runtime Backup Digest 冲突")
    if not backup.exists():
        atomic_write(backup, runtime.read_bytes())
    try:
        atomic_write(runtime, candidate.read_bytes())
        config = _read_install_config(root)
        protocol = protocol_bytes()
        config["protocol"] = {"id": "yuan.core", "revision": "0.2", "digest": digest_bytes(protocol)}
        config["harness"] = {"id": "yuan.python", "revision": __version__, "digest": harness_digest()}
        config["environment"] = environment_binding()
        config = with_digest(config)
        atomic_write(root / ".yuan" / "protocol.md", protocol)
        atomic_write(root / ".yuan" / "config.json", canonical_bytes(config))
        _write_adapter(root)
        _install_bootstrap(root)
        record = _install_record(root, {**artifact, "path": runtime.name})
        verified = _pinned_status(root, runtime)
    except Exception:
        for path, payload in previous.items():
            if payload is None:
                if path.exists():
                    path.unlink()
            else:
                atomic_write(path, payload)
        raise
    finally:
        if candidate.exists():
            candidate.unlink()
    return {
        "status": "UPDATED",
        "root": str(root),
        "previous_runtime_digest": current_digest,
        "runtime_digest": artifact["digest"],
        "install_digest": record["digest"],
        "decision": verified["decision"],
        "agent_guidance": agent_guidance(root),
    }
