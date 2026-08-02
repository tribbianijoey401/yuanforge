"""从当前 Yuan 源码同步目标 Vibe Coding 项目。"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from yuan.project import install_project, update_project  # noqa: E402


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
    """在不污染 JSON 标准输出的前提下显示 Agent 下一步。"""

    guidance = result.get("agent_guidance")
    if not isinstance(guidance, dict):
        return
    status = result.get("status")
    print("\nYuan 下一步：", file=sys.stderr)
    if status == "STAGED":
        print("1. 当前 Work 尚未完成，新 Runtime 仅已暂存。", file=sys.stderr)
        print("2. 继续当前 Work 时发送：", file=sys.stderr)
        print(f"   {guidance['continue_prompt']}", file=sys.stderr)
        print("3. Reducer 返回 COMPLETE 后，重新运行 update。", file=sys.stderr)
    else:
        print(f"1. 使用 Codex、Claude Code 等 Agent 打开项目：{guidance['project_root']}", file=sys.stderr)
        print("2. 开始新工作时发送：", file=sys.stderr)
        print(f"   {guidance['start_prompt']}", file=sys.stderr)
        print("3. 继续未完成工作时发送：", file=sys.stderr)
        print(f"   {guidance['continue_prompt']}", file=sys.stderr)
    print(f"固定 Runtime 状态命令：{guidance['status_command']}", file=sys.stderr)


def _configure_utf8_streams() -> None:
    """让 JSON 和人类提示在 Windows 重定向时仍使用同一编码。"""

    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            reconfigure(encoding="utf-8")


def main() -> int:
    _configure_utf8_streams()
    parser = ChineseArgumentParser(description="安装或更新目标项目的 Yuan Runtime 与 Agent Bootstrap")
    commands = parser.add_subparsers(dest="command", required=True)
    install = commands.add_parser("install", help="首次安装")
    install.add_argument("target", type=Path)
    install.add_argument("--profile", choices=("AUDITED",), default="AUDITED")
    install.add_argument("--run-id")
    update = commands.add_parser("update", help="同步当前 Yuan Release")
    update.add_argument("target", type=Path)
    _localize_parser(parser)
    args = parser.parse_args()
    try:
        if args.command == "install":
            result = install_project(args.target, profile=args.profile, run_id=args.run_id)
        else:
            result = update_project(args.target)
        print(json.dumps(result, ensure_ascii=False, separators=(",", ":")))
        _print_agent_guidance(result)
        return 0
    except Exception as exc:
        print(json.dumps({"status": "ERROR", "error": str(exc)}, ensure_ascii=False, separators=(",", ":")), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
