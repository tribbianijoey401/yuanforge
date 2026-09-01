from __future__ import annotations

import unittest
from pathlib import Path

from runner import run_job


class RunJobTests(unittest.TestCase):
    def test_cleans_workspace_after_success(self) -> None:
        observed: list[Path] = []

        def successful_job(workspace: Path) -> str:
            observed.append(workspace)
            self.assertTrue(workspace.is_dir())
            return "done"

        self.assertEqual("done", run_job(successful_job))
        self.assertFalse(observed[0].exists())
