"""从当前 Yuan 源码同步目标 Vibe Coding 项目。"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from yuan.project import (  # noqa: E402
    diagnose_project,
    install_project,
    load_release_context,
    project_status,
    update_project,
)
from yuan.capabilities import DEFAULT_PROFILE, available_profiles  # noqa: E402


class ChineseArgumentParser(argparse.ArgumentParser):
    """输出中文用法标题和帮助选项。"""

    def __init__(self, *args: object, **kwargs: object) -> None:
        kwargs["add_help"] = False
        super().__init__(*args, **kwargs)
        self.add_argument("-h", "--help", action="help", help="显示帮助并退出")

    def format_usage(self) -> str:
        return super().format_usage().replace("usage:", "用法:", 1)

    def format_help(self) -> str:
        return super().format_help().replace("usage:", "用法:", 1)


def _localize_parser(parser: argparse.ArgumentParser) -> None:
    """将 argparse 自动生成的帮助页标题本地化。"""

    parser._positionals.title = "位置参数"
    parser._optionals.title = "选项"
    for action in parser._actions:
        if isinstance(action, argparse._SubParsersAction):
            action.container.title = "命令"
            for child in action.choices.values():
                _localize_parser(child)


def _print_agent_guidance(result: dict[str, object]) -> None:
    """在不污染 JSON 标准输出的前提下面向用户显示入口提示。"""

    guidance = result.get("agent_guidance")
    if not isinstance(guidance, dict):
        return
    print("\nYuan 已就绪：", file=sys.stderr)
    print(f"1. 使用 Codex、Claude Code 等 Agent 打开项目：{guidance['project_root']}", file=sys.stderr)
    print("2. 开始新需求时，直接描述目标、范围和限制，例如：", file=sys.stderr)
    print(f"   {guidance['start_prompt']}", file=sys.stderr)
    print("3. 恢复中断工作时，直接说明继续即可，例如：", file=sys.stderr)
    print(f"   {guidance['continue_prompt']}", file=sys.stderr)
    print("Yuan 会从 AGENTS.md 和项目固定 Runtime 自动恢复状态、检索记忆、路由 Agent/Skill 并进入确认节点。", file=sys.stderr)


def _configure_utf8_streams() -> None:
    """让 JSON 和人类提示在 Windows 重定向时仍使用同一编码。"""

    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            reconfigure(encoding="utf-8")


def _verified_context(report_path: Path | None) -> dict[str, object]:
    if report_path is None:
        print("正在运行 Yuan Conformance Suite，请稍候……", file=sys.stderr)
        completed = subprocess.run(
            [sys.executable, "-B", str(ROOT / "scripts" / "run_conformance.py")],
            cwd=ROOT,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        if completed.returncode != 0:
            stdout = completed.stdout.decode("utf-8", errors="replace")
            stderr = completed.stderr.decode("utf-8", errors="replace")
            raise RuntimeError(
                f"当前 Yuan Source 没有通过 Conformance Suite；exit_code={completed.returncode}；"
                f"stdout={stdout[-4000:]!r}；stderr={stderr[-4000:]!r}"
            )
        print("Conformance PASS，开始同步已验证 Release。", file=sys.stderr)
        report_path = ROOT / "dist" / "conformance-report.json"
    return load_release_context(ROOT, report_path)


def main() -> int:
    _configure_utf8_streams()
    parser = ChineseArgumentParser(description="安装或更新目标项目的 Yuan Runtime 与 Agent Bootstrap")
    commands = parser.add_subparsers(dest="command", required=True)
    install = commands.add_parser("install", help="首次安装")
    install.add_argument("target", type=Path)
    install.add_argument("--profile", choices=("AUDITED",), default="AUDITED")
    install.add_argument("--capability-profile", choices=available_profiles(), default=DEFAULT_PROFILE)
    install.add_argument("--run-id")
    install.add_argument("--conformance-report", type=Path, help="使用已有且匹配当前 Release 的 Conformance Report")
    update = commands.add_parser("update", help="强制激活当前 Yuan Source")
    update.add_argument("target", type=Path)
    update.add_argument("--capability-profile", choices=available_profiles(), help="选择要强制部署的 Capability Profile")
    status = commands.add_parser("status", help="检查项目部署与暂存版本")
    status.add_argument("target", type=Path)
    diagnose = commands.add_parser("diagnose", help="不依赖旧 Runtime 收集完整部署诊断")
    diagnose.add_argument("target", type=Path)
    _localize_parser(parser)
    args = parser.parse_args()
    try:
        if args.command == "install":
            result = install_project(
                args.target,
                release_context=_verified_context(args.conformance_report),
                profile=args.profile,
                capability_profile=args.capability_profile,
                run_id=args.run_id,
            )
        elif args.command == "update":
            result = update_project(
                args.target,
                capability_profile=args.capability_profile,
            )
        elif args.command == "status":
            result = project_status(args.target)
        elif args.command == "diagnose":
            result = diagnose_project(args.target)
        else:
            raise AssertionError("到达不可达的 sync_project 命令分支")
        print(json.dumps(result, ensure_ascii=False, separators=(",", ":")))
        _print_agent_guidance(result)
        return 0
    except Exception as exc:
        print(json.dumps({
            "status": "ERROR",
            "stage": f"sync_project.{getattr(args, 'command', 'parse')}",
            "target": str(getattr(args, "target", "")),
            "error_type": type(exc).__name__,
            "error": str(exc),
            "recommended_agent": "runtime-maintainer",
            "recommended_skill": "runtime-recovery",
        }, ensure_ascii=False, separators=(",", ":")), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
