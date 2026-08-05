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
from .capabilities import (
    CUSTOM_ROOT,
    DEFAULT_PROFILE,
    available_profiles,
    bind_custom_descriptor,
    installed_catalog,
    route_capabilities,
    routing_plan,
    resolve_capabilities,
)
from .errors import YuanError
from .ledger import atomic_write
from .memory import (
    check_memory_source,
    checkpoint_memory,
    memory_context,
    memory_resume,
    memory_show,
    memory_status,
    memory_template,
    rebuild_memory,
    record_memory,
)
from .paths import resolve_inside
from .project import (
    diagnose_project,
    initialize_repository,
    install_project,
    load_release_context,
    project_status,
    update_project,
)
from .release import read_manifest, verify_release
from .runtime import (
    accept_work,
    active_ledger,
    begin_attempt,
    dispatch_attempt,
    handoff_template,
    load_config,
    list_runs,
    mark_attempt_unknown,
    observe_attempt,
    read_json,
    rebuild,
    record_reduction,
    record_handoff,
    resolve_attempt,
    run_verifier,
    start_successor,
    supersede_work,
)
from .validate import validate_proposal, validate_work, with_digest
from .workflow import (
    confirm_intake,
    confirm_work,
    intake_decision,
    intake_template as create_intake_template,
    validate_intake,
)


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


def configure_utf8_streams() -> None:
    """确保 Windows 终端中的中文 Help 与错误信息使用 UTF-8。"""

    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            reconfigure(encoding="utf-8")


def init_repository(root: Path, profile: str, run_id: str | None) -> dict[str, Any]:
    return initialize_repository(root, profile, run_id)


def _core_routing(risk: str, signals: list[str]) -> dict[str, Any]:
    value = {
        "schema_version": "yuan.routing/v1",
        "profile_id": "core",
        "profile_digest": digest({"profile": "core"}),
        "risk": risk,
        "signals": signals,
        "agents": [],
        "skills": [],
        "handoff_agents": [],
        "artifact_review_agents": [],
    }
    return with_digest(value)


def work_template(
    root: Path,
    *,
    successor: bool = False,
    intake: dict[str, Any] | None = None,
) -> dict[str, Any]:
    config = load_config(root)
    if intake is None:
        if config["capability"] is not None:
            raise YuanError("已安装工程能力要求先创建并确认 Intake，再生成 Work")
        intake = create_intake_template("手动 Core Work")
        intake["risk"] = {"level": "R2", "rationale": "手动 Core 流程，不启用工程角色路由。"}
        intake = with_digest(intake)
        intake = confirm_intake(intake, "手动 Core 流程确认")
    validate_intake(intake, require_confirmation=True)
    routing = (
        routing_plan(root, risk=intake["risk"]["level"], signals=intake["signals"])
        if config["capability"] is not None
        else _core_routing(intake["risk"]["level"], intake["signals"])
    )
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
        work["intake"] = intake
        work["routing"] = routing
        work["confirmation"] = None
        work["created_at"] = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        return with_digest(work)
    verifier_path = ".yuan/drafts/verifiers/AC-001.py"
    verifier_files = [{"path": verifier_path, "digest": "0" * 64}]
    verifier = {
        "id": "replace-me",
        "revision": "1",
        "digest": digest({"kind": "python-script", "entrypoint": verifier_path, "files": verifier_files}),
        "kind": "python-script",
        "entrypoint": verifier_path,
        "timeout_seconds": 30,
        "files": verifier_files,
    }
    work = {
        "schema_version": "yuan.work/v2",
        "work_id": "WORK-001",
        "revision": 1,
        "goal": "替换为具体、可测试的目标。",
        "profile": config["profile"],
        "protocol": config["protocol"],
        "harness": config["harness"],
        "intake": intake,
        "routing": routing,
        "confirmation": None,
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
    intake = commands.add_parser("intake", help="澄清并确认用户需求")
    intake_sub = intake.add_subparsers(dest="intake_command", required=True)
    intake_template_parser = intake_sub.add_parser("template", help="创建需求 Intake 草稿")
    intake_template_parser.add_argument("--request", required=True)
    intake_check = intake_sub.add_parser("check", help="检查待决问题与确认状态")
    intake_check.add_argument("file", type=Path)
    intake_confirm = intake_sub.add_parser("confirm", help="绑定用户对需求、答案、假设和风险的确认")
    intake_confirm.add_argument("file", type=Path)
    intake_confirm.add_argument("--statement", required=True)
    work = commands.add_parser("work", help="管理不可变 Work Contract")
    work_sub = work.add_subparsers(dest="work_command", required=True)
    work_template_parser = work_sub.add_parser("template", help="生成 Work 草稿")
    work_template_parser.add_argument("--successor", action="store_true", help="基于当前 Terminal Run 生成继任 Work")
    work_template_parser.add_argument("--intake", type=Path, help="已确认的 Intake JSON")
    work_accept = work_sub.add_parser("accept", help="验证并接受 Work")
    work_accept.add_argument("file", type=Path)
    work_bind = work_sub.add_parser("bind-verifier", help="绑定 Verifier Closure digest")
    work_bind.add_argument("file", type=Path)
    work_bind.add_argument("--criterion", required=True)
    work_confirm = work_sub.add_parser("confirm", help="绑定用户对完整 Work Contract 的最终确认")
    work_confirm.add_argument("file", type=Path)
    work_confirm.add_argument("--statement", required=True)
    attempt = commands.add_parser("attempt", help="管理 Attempt 生命周期")
    attempt_sub = attempt.add_subparsers(dest="attempt_command", required=True)
    attempt_template_parser = attempt_sub.add_parser("template", help="根据当前文件生成带 Input Digest 的 Proposal")
    attempt_template_parser.add_argument("--attempt-id", required=True)
    attempt_template_parser.add_argument("--strategy", required=True)
    attempt_template_parser.add_argument("--claim", required=True)
    attempt_template_parser.add_argument("--falsification", required=True)
    attempt_template_parser.add_argument("--input", action="append", default=[])
    attempt_template_parser.add_argument("--action-type", choices=("file-read", "file-write", "command", "verify", "reconcile"), required=True)
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
    handoff = commands.add_parser("handoff", help="记录 Agent 角色输出与下一角色交接")
    handoff_sub = handoff.add_subparsers(dest="handoff_command", required=True)
    handoff_template_parser = handoff_sub.add_parser("template", help="生成绑定当前 Work/Artifact 的 Role Handoff")
    handoff_template_parser.add_argument("--handoff-id", required=True)
    handoff_template_parser.add_argument("--agent", required=True)
    handoff_template_parser.add_argument("--to", required=True)
    handoff_template_parser.add_argument("--phase", choices=("intake", "design", "implementation", "review", "verification", "handoff"), required=True)
    handoff_template_parser.add_argument("--status", choices=("READY", "NEEDS_WORK"), required=True)
    handoff_template_parser.add_argument("--summary", required=True)
    handoff_template_parser.add_argument("--evidence", action="append", default=[])
    handoff_record = handoff_sub.add_parser("record", help="验证并追加不可变 Role Handoff")
    handoff_record.add_argument("file", type=Path)
    commands.add_parser("status", help="显示当前 Run 状态")
    commands.add_parser("rebuild", help="操作员恢复：从 Ledger 重建派生 Run Memory")
    commands.add_parser("reduce", help="记录 Reducer 的唯一判定")
    seal = commands.add_parser("seal", help="为 JSON Record 添加 digest")
    seal.add_argument("file", type=Path)
    recover = commands.add_parser("recover", help="操作员恢复：从不可变 Event 恢复 Ledger Head")
    recover.add_argument("--force-stale-lock", action="store_true")
    run = commands.add_parser("run", help="查询或创建 Run")
    run_sub = run.add_subparsers(dest="run_command", required=True)
    run_sub.add_parser("list", help="列出全部 Run")
    run_successor = run_sub.add_parser("successor", help="以显式 Predecessor Binding 创建继任 Run")
    run_successor.add_argument("file", type=Path)
    run_successor.add_argument("--run-id", required=True)
    run_supersede = run_sub.add_parser("supersede", help="因用户需求变更关闭当前非终态 Work")
    run_supersede.add_argument("--reason", required=True)
    run_supersede.add_argument("--request", required=True)
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
    memory = commands.add_parser("memory", help="管理项目长期记忆与跨会话连续性")
    memory_sub = memory.add_subparsers(dest="memory_command", required=True)
    memory_template_parser = memory_sub.add_parser("template", help="按类型生成具备相应来源约束的 Memory Record")
    memory_template_parser.add_argument("--memory-id", required=True)
    memory_template_parser.add_argument("--kind", choices=("project", "feature", "module", "architecture", "convention", "decision", "pitfall", "incident", "checkpoint", "handoff"), required=True)
    memory_template_parser.add_argument("--title", required=True)
    memory_template_parser.add_argument("--summary", required=True)
    memory_template_parser.add_argument("--details", required=True)
    memory_template_parser.add_argument("--status", choices=("active", "resolved", "superseded", "deprecated"), default="active")
    memory_template_parser.add_argument("--tag", action="append", default=[])
    memory_template_parser.add_argument("--relation", action="append", default=[])
    memory_template_parser.add_argument("--bind", action="append", default=[])
    memory_check = memory_sub.add_parser("check", help="验证 Memory Record 与当前 Work/Evidence Binding")
    memory_check.add_argument("file", type=Path)
    memory_record = memory_sub.add_parser("record", help="追加不可变 Memory Revision 并重建索引")
    memory_record.add_argument("file", type=Path)
    memory_sub.add_parser("list", help="列出当前 Memory Heads")
    memory_show_parser = memory_sub.add_parser("show", help="显示指定 Memory 的最新 Revision")
    memory_show_parser.add_argument("memory_id")
    memory_sub.add_parser("status", help="检查 Memory Binding 是否过期")
    memory_context_parser = memory_sub.add_parser("context", help="为新需求检索相关长期记忆")
    memory_context_parser.add_argument("--request", required=True)
    memory_context_parser.add_argument("--limit", type=int, default=10)
    memory_checkpoint = memory_sub.add_parser("checkpoint", help="保存当前工作检查点并重建 CURRENT.md")
    memory_checkpoint.add_argument("--summary", required=True)
    memory_checkpoint.add_argument("--details", required=True)
    memory_checkpoint.add_argument("--completed", action="append", default=[])
    memory_checkpoint.add_argument("--blocker", action="append", default=[])
    memory_checkpoint.add_argument("--next-step", action="append", default=[])
    memory_checkpoint.add_argument("--open-question", action="append", default=[])
    memory_checkpoint.add_argument("--resume-command", action="append", default=[])
    memory_resume_parser = memory_sub.add_parser("resume", help="恢复最新连续性检查点与相关长期知识")
    memory_resume_parser.add_argument("--request")
    memory_resume_parser.add_argument("--limit", type=int, default=10)
    memory_sub.add_parser("rebuild", help="操作员恢复：从追加式 Record 重建 JSON/Markdown 索引")
    project = commands.add_parser("project", help="安装或同步目标项目的 Yuan Runtime")
    project_sub = project.add_subparsers(dest="project_command", required=True)
    project_install = project_sub.add_parser("install", help="向目标项目安装固定 Runtime 与 Agent Bootstrap")
    project_install.add_argument("target", type=Path)
    project_install.add_argument("--profile", choices=("AUDITED",), default="AUDITED")
    project_install.add_argument("--capability-profile", choices=available_profiles(), default=DEFAULT_PROFILE)
    project_install.add_argument("--run-id")
    project_install.add_argument("--release-root", type=Path, default=Path.cwd(), help="Yuan Source/Release 根目录")
    project_install.add_argument("--conformance-report", type=Path, default=Path("dist/conformance-report.json"), help="相对 Release Root 的验证报告")
    project_update = project_sub.add_parser("update", help="强制激活当前 Yuan Source")
    project_update.add_argument("target", type=Path)
    project_update.add_argument("--capability-profile", choices=available_profiles(), help="选择要强制部署的 Capability Profile")
    project_status_parser = project_sub.add_parser("status", help="检查项目部署与暂存版本")
    project_status_parser.add_argument("target", type=Path)
    project_diagnose = project_sub.add_parser("diagnose", help="不依赖旧 Runtime 收集完整部署诊断")
    project_diagnose.add_argument("target", type=Path)
    capability = commands.add_parser("capability", help="发现并解析 Rules、Agents 与 Skills")
    capability_sub = capability.add_subparsers(dest="capability_command", required=True)
    capability_sub.add_parser("list", help="列出已安装能力及触发条件")
    capability_resolve = capability_sub.add_parser("resolve", help="解析本 Tick 要加载的能力文件")
    capability_resolve.add_argument("--rule", action="append", default=[])
    capability_resolve.add_argument("--agent", action="append", default=[])
    capability_resolve.add_argument("--skill", action="append", default=[])
    capability_route = capability_sub.add_parser("route", help="根据 Risk 与 Signal 生成确定性 Agent/Skill 路由")
    capability_route.add_argument("--risk", choices=("R0", "R1", "R2"), required=True)
    capability_route.add_argument("--signal", action="append", default=[])
    capability_bind = capability_sub.add_parser("bind-custom", help="绑定 Custom Extension 文件与 Descriptor Digest")
    capability_bind.add_argument("directory", type=Path)
    capability_bind.add_argument("--write", action="store_true", help="原子更新扩展的 extension.json")
    localize_parser(top)
    return top


def execute(args: argparse.Namespace) -> Any:
    root = args.root.resolve()
    if args.command == "init":
        return init_repository(root, args.profile, args.run_id)
    if args.command == "intake" and args.intake_command == "template":
        return create_intake_template(args.request)
    if args.command == "intake" and args.intake_command == "check":
        return intake_decision(read_json(args.file))
    if args.command == "intake" and args.intake_command == "confirm":
        return confirm_intake(read_json(args.file), args.statement)
    if args.command == "work" and args.work_command == "template":
        intake_value = None if args.intake is None else read_json(args.intake)
        return work_template(root, successor=args.successor, intake=intake_value)
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
        work["confirmation"] = None
        return with_digest(work)
    if args.command == "work" and args.work_command == "confirm":
        work = confirm_work(read_json(args.file), args.statement)
        validate_work(work, require_confirmation=True)
        return work
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
    if args.command == "handoff" and args.handoff_command == "template":
        return handoff_template(
            root,
            handoff_id=args.handoff_id,
            agent_id=args.agent,
            to_agent_id=args.to,
            phase=args.phase,
            status=args.status,
            summary=args.summary,
            evidence_ids=args.evidence,
        )
    if args.command == "handoff" and args.handoff_command == "record":
        return record_handoff(root, read_json(args.file))
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
    if args.command == "run" and args.run_command == "supersede":
        return supersede_work(root, reason=args.reason, request=args.request)
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
    if args.command == "memory" and args.memory_command == "template":
        return memory_template(
            root,
            memory_id=args.memory_id,
            kind=args.kind,
            title=args.title,
            summary=args.summary,
            details=args.details,
            status=args.status,
            tags=args.tag,
            relations=args.relation,
            bind_paths=args.bind,
        )
    if args.command == "memory" and args.memory_command == "check":
        return check_memory_source(root, read_json(args.file))
    if args.command == "memory" and args.memory_command == "record":
        return record_memory(root, read_json(args.file))
    if args.command == "memory" and args.memory_command == "list":
        return rebuild_memory(root, write=False)
    if args.command == "memory" and args.memory_command == "show":
        return memory_show(root, args.memory_id)
    if args.command == "memory" and args.memory_command == "status":
        return memory_status(root)
    if args.command == "memory" and args.memory_command == "context":
        return memory_context(root, args.request, limit=args.limit)
    if args.command == "memory" and args.memory_command == "checkpoint":
        return checkpoint_memory(
            root,
            summary=args.summary,
            details=args.details,
            completed=args.completed,
            blockers=args.blocker,
            next_steps=args.next_step,
            open_questions=args.open_question,
            resume_commands=args.resume_command,
        )
    if args.command == "memory" and args.memory_command == "resume":
        return memory_resume(root, args.request, limit=args.limit)
    if args.command == "memory" and args.memory_command == "rebuild":
        return rebuild_memory(root)
    if args.command == "project" and args.project_command == "install":
        context = load_release_context(args.release_root, args.release_root / args.conformance_report)
        return install_project(
            args.target,
            release_context=context,
            profile=args.profile,
            capability_profile=args.capability_profile,
            run_id=args.run_id,
        )
    if args.command == "project" and args.project_command == "update":
        return update_project(args.target, capability_profile=args.capability_profile)
    if args.command == "project" and args.project_command == "status":
        return project_status(args.target)
    if args.command == "project" and args.project_command == "diagnose":
        return diagnose_project(args.target)
    if args.command == "capability" and args.capability_command == "list":
        return installed_catalog(root)
    if args.command == "capability" and args.capability_command == "resolve":
        return resolve_capabilities(
            root,
            rules=args.rule,
            agents=args.agent,
            skills=args.skill,
        )
    if args.command == "capability" and args.capability_command == "route":
        return route_capabilities(root, risk=args.risk, signals=args.signal)
    if args.command == "capability" and args.capability_command == "bind-custom":
        directory = resolve_inside(root, args.directory.as_posix())
        custom_root = (root / CUSTOM_ROOT).resolve()
        if directory == custom_root or custom_root not in directory.parents:
            raise YuanError("Custom Extension 必须位于 .yuan/extensions/custom/<extension-id>/")
        descriptor = bind_custom_descriptor(directory)
        if args.write:
            atomic_write(directory / "extension.json", canonical_bytes(descriptor))
            return {
                "status": "CUSTOM_BOUND",
                "extension_id": descriptor["extension_id"],
                "descriptor": (directory / "extension.json").relative_to(root).as_posix(),
                "digest": descriptor["digest"],
            }
        return descriptor
    if args.command == "seal":
        return with_digest(read_json(args.file))
    raise AssertionError("到达不可达的 Command 分支")


def main(argv: list[str] | None = None) -> int:
    configure_utf8_streams()
    try:
        args = parser().parse_args(argv)
        emit(execute(args))
        return 0
    except YuanError as exc:
        emit({"status": "ERROR", "error": str(exc), "result": "BLOCKED"})
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
