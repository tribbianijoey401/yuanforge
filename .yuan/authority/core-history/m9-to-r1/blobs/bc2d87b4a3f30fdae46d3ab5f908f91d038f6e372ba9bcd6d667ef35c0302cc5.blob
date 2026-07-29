"""Fail-closed invocation profiles for the standard-library Reference Port."""

from __future__ import annotations

import os
import pathlib
from typing import Sequence


PYTHON_PROFILE = "python-audit-sandbox/v1"
PYTHON_AUDIT_WRAPPER = r"""
import os as _os
import sys as _sys

_code = _sys.argv[1]
_user_argv = _sys.argv[2:]
_write_flags = _os.O_WRONLY | _os.O_RDWR | _os.O_CREAT | _os.O_TRUNC | _os.O_APPEND
_denied_prefixes = (
    "subprocess.",
    "socket.",
    "os.system",
    "os.spawn",
    "os.exec",
    "os.remove",
    "os.unlink",
    "os.rename",
    "os.replace",
    "os.mkdir",
    "os.rmdir",
    "os.chdir",
)

def _guard(event, args):
    if event == "open":
        mode = args[1] if len(args) > 1 else "r"
        flags = args[2] if len(args) > 2 else 0
        if (
            isinstance(mode, str)
            and any(token in mode for token in ("w", "a", "x", "+"))
        ) or (isinstance(flags, int) and flags & _write_flags):
            raise PermissionError("Yuan command profile denies filesystem writes")
    if event == "import" and args and str(args[0]).split(".", 1)[0] == "ctypes":
        raise PermissionError("Yuan command profile denies ctypes")
    if event.startswith(_denied_prefixes):
        raise PermissionError("Yuan command profile denies external side effects")

_sys.addaudithook(_guard)
_sys.argv = ["-c", *_user_argv]
exec(compile(_code, "<yuan-command>", "exec"), {"__name__": "__main__"})
"""


def _inside(root: pathlib.Path, value: pathlib.Path) -> bool:
    try:
        value.resolve(strict=False).relative_to(root)
    except ValueError:
        return False
    return True


def prepare_command(
    executable: pathlib.Path,
    argv: Sequence[str],
    root: pathlib.Path,
    profile: str,
) -> list[str]:
    if profile != PYTHON_PROFILE:
        raise ValueError("unsupported command invocation profile")
    if len(argv) < 3 or argv[1] != "-c":
        raise ValueError("Python profile accepts only an isolated -c invocation")
    for token in argv[3:]:
        path = pathlib.Path(token)
        if path.is_absolute() and not _inside(root, path):
            raise ValueError("absolute command argument escapes the Port root")
    return [
        str(executable),
        "-I",
        "-c",
        PYTHON_AUDIT_WRAPPER,
        argv[2],
        *argv[3:],
    ]
