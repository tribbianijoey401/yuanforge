"""Yuan Microkernel 的最小 JSON CLI。"""

from __future__ import annotations

import argparse
import copy
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .adapters import validate_adapter_descriptor
from .canonical import canonical_bytes, digest, digest_bytes
from .errors import YuanError
from .paths import resolve_inside
from .project import initialize_repository, install_project, update_project
from .release import read_manifest, verify_release
from .runtime import (
    accept_work,
    active_ledger,
    begin_attempt,
    dispatch_attempt,
    load_config,
    list_runs,
    mark_attempt_unknown,
    observe_attempt,
    read_json,
    rebuild,
    record_reduction,
    resolve_attempt,
    run_verifier,
    start_successor,
)
from .validate import validate_proposal, with_digest


class ChineseArgumentParser(argparse.ArgumentParser):
    """只本地化 argparse 的固定界面文案，不改变 Command 标识。"""

    def format_usage(self) -> str:
        return super().format_usage().replace("usage: ", "用法：", 1)

    def format_help(self) -> str:
        return super().format_help().replace("usage: ", "用法：", 1)


def localize_parser(value: argparse.ArgumentParser) -> None:
    value._positionals.title = "位置参数"
    value._optionals.title = "选项"
    for action in value._actions:
        if isinstance(action, argparse._HelpAction):
            action.help = "显示帮助并退出"
        elif isinstance(action, argparse._SubParsersAction):
            for child in action.choices.values():
                localize_parser(child)


def emit(value: Any) -> None:
    sys.stdout.buffer.write(canonical_bytes(value) + b"\n")


def init_repository(root: Path, profile: str, run_id: str | None) -> dict[str, Any]:
    return initialize_repository(root, profile, run_id)


def work_template(root: Path, *, successor: bool = False) -> dict[str, Any]:
    config = load_config(root)
    if successor:
        _, ledger = active_ledger(root)
        projection = rebuild(root, write=False)
        if projection["work"] is None:
            raise YuanError("当前 Run 没有可继任的 Work")
        work = copy.deepcopy(projection["work"])
        work["revision"] += 1
        from .runtime import predecessor_binding

        work["predecessor"] = predecessor_binding(ledger, projection)
        work["profile"] = config["profile"]
        work["protocol"] = config["protocol"]
        work["harness"] = config["harness"]
        work["artifact"]["environment"] = config["environment"]
        work["created_at"] = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        return with_digest(work)
    verifier_files = [{"path": "tests/verify.py", "digest": "0" * 64}]
    verifier = {
        "id": "replace-me",
        "revision": "1",
        "digest": digest({"kind": "python-script", "entrypoint": "tests/verify.py", "files": verifier_files}),
        "kind": "python-script",
        "entrypoint": "tests/verify.py",
        "timeout_seconds": 30,
        "files": verifier_files,
    }
    work = {
        "schema_version": "yuan.work/v1",
        "work_id": "WORK-001",
        "revision": 1,
        "goal": "替换为具体、可测试的目标。",
        "profile": config["profile"],
        "protocol": config["protocol"],
        "harness": config["harness"],
        "artifact": {
            "root": ".",
            "include": ["**"],
            "exclude": config["artifact_exclude"] + [".yuan/**"],
            "environment": config["environment"],
        },
        "acceptance_criteria": [{
            "id": "AC-001",
            "description": "替换为 Typed Acceptance Criterion。",
            "required": True,
            "verifier": verifier,
            "min_assertions": 1,
            "independence": "independent",
        }],
        "safety_invariants": [{
            "id": "SAFE-001",
            "description": "Required Verifier 同时证明已声明的安全属性。",
            "criterion_id": "AC-001",
        }],
        "grants": [{
            "id": "GRANT-001",
            "action_types": ["file-read", "file-write", "command", "verify", "reconcile"],
            "side_effect_classes": ["none", "filesystem", "process"],
            "scopes": ["src", "tests"],
        }],
        "budgets": {"ticks": 20, "attempts": 10, "tool_calls": 50, "command_seconds": 600},
        "predecessor": None,
        "created_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
    }
    return with_digest(work)


def attempt_template(
    root: Path,
    *,
    attempt_id: str,
    strategy: str,
    claim: str,
    falsification: str,
    inputs: list[str],
    action_type: str,
    paths: list[str],
    side_effect_class: str,
    grant_id: str | None,
    read_only: bool,
    high_impact: bool,
    tool_calls: int,
    command_seconds: int,
) -> dict[str, Any]:
    projection = rebuild(root, write=False)
    if projection["work"] is None or projection["errors"]:
        raise YuanError("没有合法 Active Work，不能创建 Proposal")
    relevant = []
    for relative in inputs:
        target = resolve_inside(root.resolve(), relative)
        if target.is_symlink() or not target.is_file():
            raise YuanError(f"Relevant Input 不存在或不安全：{relative}")
        relevant.append({"path": relative.replace("\\", "/"), "digest": digest_bytes(target.read_bytes())})
    proposal = {
        "attempt_id": attempt_id,
        "strategy": strategy,
        "hypothesis": {"claim": claim, "falsification": falsification},
        "relevant_inputs": relevant,
        "action": {
            "type": action_type,
            "mutating": not read_only,
            "side_effect_class": side_effect_class,
            "paths": [item.replace("\\", "/") for item in paths],
            "grant_id": grant_id,
            "high_impact": high_impact,
        },
        "budget_charge": {
            "ticks": 1,
            "attempts": 1,
            "tool_calls": tool_calls,
            "command_seconds": command_seconds,
        },
    }
    return validate_proposal(proposal)


def parser() -> argparse.ArgumentParser:
    top = ChineseArgumentParser(prog="yuan", description="Yuan 确定性 Harness Microkernel")
    top.add_argument("--root", type=Path, default=Path.cwd(), help="仓库根目录，默认使用当前目录")
    commands = top.add_subparsers(dest="command", required=True)
    init = commands.add_parser("init", help="初始化 Yuan Runtime")
    init.add_argument("--profile", choices=("GUIDED", "AUDITED", "ENFORCED"), default="AUDITED")
    init.add_argument("--run-id")
    work = commands.add_parser("work", help="管理不可变 Work Contract")
    work_sub = work.add_subparsers(dest="work_command", required=True)
    work_template_parser = work_sub.add_parser("template", help="生成 Work 草稿")
    work_template_parser.add_argument("--successor", action="store_true", help="基于当前 Terminal Run 生成继任 Work")
    work_accept = work_sub.add_parser("accept", help="验证并接受 Work")
    work_accept.add_argument("file", type=Path)
    work_bind = work_sub.add_parser("bind-verifier", help="绑定 Verifier Closure digest")
    work_bind.add_argument("file", type=Path)
    work_bind.add_argument("--criterion", required=True)
    attempt = commands.add_parser("attempt", help="管理 Attempt 生命周期")
    attempt_sub = attempt.add_subparsers(dest="attempt_command", required=True)
    attempt_template_parser = attempt_sub.add_parser("template", help="根据当前文件生成带 Input Digest 的 Proposal")
    attempt_template_parser.add_argument("--attempt-id", required=True)
    attempt_template_parser.add_argument("--strategy", required=True)
    attempt_template_parser.add_argument("--claim", required=True)
    attempt_template_parser.add_argument("--falsification", required=True)
    attempt_template_parser.add_argument("--input", action="append", default=[])
    attempt_template_parser.add_argument("--action-type", choices=("file-read", "file-write", "command", "verify"), required=True)
    attempt_template_parser.add_argument("--path", action="append", default=[])
    attempt_template_parser.add_argument("--side-effect-class", choices=("none", "filesystem", "process", "network", "external"), required=True)
    attempt_template_parser.add_argument("--grant-id")
    attempt_template_parser.add_argument("--read-only", action="store_true")
    attempt_template_parser.add_argument("--high-impact", action="store_true")
    attempt_template_parser.add_argument("--tool-calls", type=int, default=1)
    attempt_template_parser.add_argument("--command-seconds", type=int, default=0)
    attempt_begin = attempt_sub.add_parser("begin", help="准备新的 Attempt")
    attempt_begin.add_argument("file", type=Path)
    attempt_dispatch = attempt_sub.add_parser("dispatch", help="记录 Attempt 已派发")
    attempt_dispatch.add_argument("--attempt", required=True)
    attempt_observe = attempt_sub.add_parser("observe", help="记录 Receipt 并观测 Artifact Diff")
    attempt_observe.add_argument("--attempt", required=True)
    attempt_observe.add_argument("--receipt", type=Path, required=True)
    attempt_unknown = attempt_sub.add_parser("mark-unknown", help="把未确定副作用标记为 UNKNOWN")
    attempt_unknown.add_argument("--attempt", required=True)
    attempt_unknown.add_argument("--reason", required=True)
    attempt_reconcile = attempt_sub.add_parser("reconcile", help="启动只读 Reconciliation Attempt")
    attempt_reconcile.add_argument("--attempt", required=True)
    attempt_reconcile.add_argument("file", type=Path)
    attempt_resolve = attempt_sub.add_parser("resolve", help="追加 UNKNOWN Terminal Resolution")
    attempt_resolve.add_argument("--attempt", required=True)
    attempt_resolve.add_argument("--reconciler", required=True)
    attempt_resolve.add_argument("--resolution", choices=("COMMITTED", "NO_EFFECT"), required=True)
    attempt_resolve.add_argument("--evidence")
    verify = commands.add_parser("verify", help="运行 Work 预绑定的 Verifier")
    verify.add_argument("--criterion", required=True)
    verify.add_argument("--attempt", required=True)
    commands.add_parser("status", help="重建并显示当前 Run Memory")
    commands.add_parser("rebuild", help="从 Ledger 重建 Run Memory")
    commands.add_parser("reduce", help="记录 Reducer 的唯一判定")
    seal = commands.add_parser("seal", help="为 JSON Record 添加 digest")
    seal.add_argument("file", type=Path)
    recover = commands.add_parser("recover", help="从不可变 Event 恢复 Ledger Head")
    recover.add_argument("--force-stale-lock", action="store_true")
    run = commands.add_parser("run", help="查询或创建 Run")
    run_sub = run.add_subparsers(dest="run_command", required=True)
    run_sub.add_parser("list", help="列出全部 Run")
    run_successor = run_sub.add_parser("successor", help="以显式 Predecessor Binding 创建继任 Run")
    run_successor.add_argument("file", type=Path)
    run_successor.add_argument("--run-id", required=True)
    adapter = commands.add_parser("adapter", help="检查 Adapter Capability Descriptor")
    adapter_sub = adapter.add_subparsers(dest="adapter_command", required=True)
    adapter_check = adapter_sub.add_parser("check", help="验证 Adapter Descriptor")
    adapter_check.add_argument("file", type=Path)
    release = commands.add_parser("release", help="验证确定性 Release")
    release_sub = release.add_subparsers(dest="release_command", required=True)
    release_verify = release_sub.add_parser("verify", help="校验 Artifact、Manifest 与可选 Source")
    release_verify.add_argument("manifest", type=Path)
    release_verify.add_argument("--artifact", type=Path, required=True)
    release_verify.add_argument("--check-source", action="store_true")
    project = commands.add_parser("project", help="安装或同步目标项目的 Yuan Runtime")
    project_sub = project.add_subparsers(dest="project_command", required=True)
    project_install = project_sub.add_parser("install", help="向目标项目安装固定 Runtime 与 Agent Bootstrap")
    project_install.add_argument("target", type=Path)
    project_install.add_argument("--profile", choices=("AUDITED",), default="AUDITED")
    project_install.add_argument("--run-id")
    project_update = project_sub.add_parser("update", help="安全同步当前 Yuan Release")
    project_update.add_argument("target", type=Path)
    localize_parser(top)
    return top


def execute(args: argparse.Namespace) -> Any:
    root = args.root.resolve()
    if args.command == "init":
        return init_repository(root, args.profile, args.run_id)
    if args.command == "work" and args.work_command == "template":
        return work_template(root, successor=args.successor)
    if args.command == "work" and args.work_command == "accept":
        return accept_work(root, read_json(args.file))
    if args.command == "work" and args.work_command == "bind-verifier":
        work = copy.deepcopy(read_json(args.file))
        matches = [item for item in work.get("acceptance_criteria", []) if item.get("id") == args.criterion]
        if len(matches) != 1:
            raise YuanError("Criterion 不存在或不唯一")
        verifier = matches[0].get("verifier", {})
        files = verifier.get("files")
        if not isinstance(files, list) or not files:
            raise YuanError("Verifier File Closure 不能为空")
        for item in files:
            path = resolve_inside(root.resolve(), item["path"])
            if path.is_symlink() or not path.is_file():
                raise YuanError(f"Verifier File 不存在或不安全：{item['path']}")
            item["digest"] = digest_bytes(path.read_bytes())
        verifier["digest"] = digest({"kind": verifier.get("kind"), "entrypoint": verifier.get("entrypoint"), "files": files})
        return with_digest(work)
    if args.command == "attempt" and args.attempt_command == "template":
        return attempt_template(
            root,
            attempt_id=args.attempt_id,
            strategy=args.strategy,
            claim=args.claim,
            falsification=args.falsification,
            inputs=args.input,
            action_type=args.action_type,
            paths=args.path,
            side_effect_class=args.side_effect_class,
            grant_id=args.grant_id,
            read_only=args.read_only,
            high_impact=args.high_impact,
            tool_calls=args.tool_calls,
            command_seconds=args.command_seconds,
        )
    if args.command == "attempt" and args.attempt_command == "begin":
        return begin_attempt(root, read_json(args.file))
    if args.command == "attempt" and args.attempt_command == "dispatch":
        return dispatch_attempt(root, args.attempt)
    if args.command == "attempt" and args.attempt_command == "observe":
        return observe_attempt(root, args.attempt, read_json(args.receipt))
    if args.command == "attempt" and args.attempt_command == "mark-unknown":
        return mark_attempt_unknown(root, args.attempt, args.reason)
    if args.command == "attempt" and args.attempt_command == "reconcile":
        proposal = read_json(args.file)
        proposal["reconciliation"] = {"target_attempt_id": args.attempt}
        return begin_attempt(root, proposal)
    if args.command == "attempt" and args.attempt_command == "resolve":
        return resolve_attempt(root, args.attempt, args.reconciler, args.resolution, args.evidence)
    if args.command == "verify":
        return run_verifier(root, args.criterion, args.attempt)
    if args.command in {"status", "rebuild"}:
        return rebuild(root)
    if args.command == "reduce":
        return record_reduction(root)
    if args.command == "recover":
        _, ledger = active_ledger(root)
        receipt = ledger.recover_head(force=args.force_stale_lock)
        return {"recovery": receipt, "projection": rebuild(root)}
    if args.command == "run" and args.run_command == "list":
        return list_runs(root)
    if args.command == "run" and args.run_command == "successor":
        return start_successor(root, read_json(args.file), args.run_id)
    if args.command == "adapter" and args.adapter_command == "check":
        descriptor = validate_adapter_descriptor(read_json(args.file), root)
        return {
            "status": "PASS",
            "adapter_id": descriptor["adapter_id"],
            "profile": descriptor["profile"],
            "capabilities": descriptor["capabilities"],
        }
    if args.command == "release" and args.release_command == "verify":
        return verify_release(
            read_manifest(args.manifest),
            args.artifact,
            repo_root=root if args.check_source else None,
        )
    if args.command == "project" and args.project_command == "install":
        return install_project(args.target, profile=args.profile, run_id=args.run_id)
    if args.command == "project" and args.project_command == "update":
        return update_project(args.target)
    if args.command == "seal":
        return with_digest(read_json(args.file))
    raise AssertionError("到达不可达的 Command 分支")


def main(argv: list[str] | None = None) -> int:
    try:
        args = parser().parse_args(argv)
        emit(execute(args))
        return 0
    except YuanError as exc:
        emit({"status": "ERROR", "error": str(exc), "result": "BLOCKED"})
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
