from __future__ import annotations

import shutil
import tempfile
from collections.abc import Callable
from pathlib import Path
from typing import TypeVar


T = TypeVar("T")


def run_job(callback: Callable[[Path], T]) -> T:
    workspace = Path(tempfile.mkdtemp(prefix="quality-benchmark-"))
    result = callback(workspace)
    shutil.rmtree(workspace)
    return result
