"""Load the vendored executable State Contract without defining a second one."""

from __future__ import annotations

import importlib.util
from functools import lru_cache
from pathlib import Path
from types import ModuleType
from typing import Any


@lru_cache(maxsize=4)
def _load_guard(path_text: str, modified_ns: int) -> ModuleType | None:
    del modified_ns  # cache key invalidates when the managed asset changes
    path = Path(path_text)
    spec = importlib.util.spec_from_file_location(
        f"yuan_state_guard_{abs(hash(path_text))}", path
    )
    if spec is None or spec.loader is None:
        return None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def validate_persisted_state(
    project_root: Path,
    framework_root: Path,
) -> list[dict[str, Any]] | None:
    """Return canonical issues without executing Python from an arbitrary Project.

    Source Insight uses the Guard from the same Yuan Source checkout.  A
    Project-local installed Insight Tool may use the sibling managed
    `.yuan/framework` Guard because both are one installed Yuan distribution.
    A generic pip-installed Insight observing an unrelated Project falls back
    to legacy read-only signals instead of importing that Project's code.
    """
    module_path = Path(__file__).resolve()
    source_guard = module_path.parents[2] / "framework" / "tools" / "state_guard.py"
    if source_guard.is_file():
        guard_path = source_guard
    else:
        installed_yuan_root = module_path.parents[3] if len(module_path.parents) > 3 else None
        if installed_yuan_root is None or framework_root.parent.resolve() != installed_yuan_root:
            return None
        guard_path = framework_root / "tools" / "state_guard.py"
    try:
        modified_ns = guard_path.stat().st_mtime_ns
    except OSError:
        return None
    guard = _load_guard(str(guard_path.resolve()), modified_ns)
    if guard is None:
        return None
    issues = guard.validate_project_state(project_root, framework_root)
    return [issue.to_dict() for issue in issues]
