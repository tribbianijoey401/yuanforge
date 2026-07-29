from __future__ import annotations

import importlib.util
import pathlib
import sys
from types import ModuleType


CORE_ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(CORE_ROOT) not in sys.path:
    sys.path.insert(0, str(CORE_ROOT))


def load_core_module(name: str) -> ModuleType:
    module_name = f"yuan_core_01_{name}"
    path = CORE_ROOT / f"{name}.py"
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module
