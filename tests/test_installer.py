from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INSTALLER = ROOT / "bin" / "yuanforge-init"
SYNC = ROOT / "scripts" / "sync_project.py"


class InstallerTests(unittest.TestCase):
    def run_command(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, "-B", *args],
            cwd=ROOT,
            text=True,
            encoding="utf-8",
            capture_output=True,
            check=False,
        )

    def test_new_install_creates_vnext_layout_and_natural_prompt(self):
        with tempfile.TemporaryDirectory(prefix="yuan-vnext-new-") as parent:
            project = Path(parent) / "project"
            result = self.run_command(str(INSTALLER), str(project), "--force")
            self.assertEqual(0, result.returncode, result.stdout + result.stderr)

            self.assertTrue((project / ".yuan" / "framework").is_dir())
            self.assertTrue((project / ".yuan" / "overrides" / "README.md").is_file())
            for name in (
                "PRODUCT.md",
                "ARCHITECTURE.md",
                "DECISIONS.md",
                "BACKLOG.md",
                "WORK.md",
                "STATUS.md",
                "MEMORY.md",
            ):
                self.assertTrue((project / "docs" / name).is_file())

            self.assertIn("直接向 Agent 描述你的 Goal、Bug 或修改需求", result.stdout)
            self.assertIn("不需要在描述中指定 Phase、Agent 或 Skill", result.stdout)
            self.assertNotIn("启动 12 人专家团", result.stdout)

    def test_update_replaces_official_snapshot_and_preserves_project_content(self):
        with tempfile.TemporaryDirectory(prefix="yuan-vnext-update-") as parent:
            project = Path(parent) / "project"
            project.mkdir()
            (project / "docs").mkdir()
            memory = project / "docs" / "MEMORY.md"
            memory.write_text("# 用户长期记忆\n不要覆盖\n", encoding="utf-8")
            source = project / "src" / "app.py"
            source.parent.mkdir()
            source.write_text("print('project-owned')\n", encoding="utf-8")

            override = project / ".yuan" / "overrides" / "policies" / "core.md"
            override.parent.mkdir(parents=True)
            override.write_text("# Project Override\n", encoding="utf-8")
            stale = project / ".yuan" / "framework" / "stale.txt"
            stale.parent.mkdir(parents=True)
            stale.write_text("old official snapshot", encoding="utf-8")
            old_runtime = project / ".yuan" / "runtime" / "lock"
            old_runtime.parent.mkdir(parents=True)
            old_runtime.write_text("stale lock", encoding="utf-8")
            old_custom = project / ".yuan" / "skills" / "user-team" / "SKILL.md"
            old_custom.parent.mkdir(parents=True)
            old_custom.write_text("# User Skill\n", encoding="utf-8")

            result = self.run_command(str(SYNC), "update", str(project))
            self.assertEqual(0, result.returncode, result.stdout + result.stderr)

            self.assertEqual("# 用户长期记忆\n不要覆盖\n", memory.read_text(encoding="utf-8"))
            self.assertEqual("print('project-owned')\n", source.read_text(encoding="utf-8"))
            self.assertEqual("# Project Override\n", override.read_text(encoding="utf-8"))
            migrated = project / ".yuan" / "overrides" / "skills" / "user-team" / "SKILL.md"
            self.assertEqual("# User Skill\n", migrated.read_text(encoding="utf-8"))

            self.assertFalse(stale.exists())
            self.assertFalse((project / ".yuan" / "runtime").exists())
            self.assertTrue((project / ".yuan" / "framework" / "VERSION").is_file())
            record = json.loads(
                (project / ".yuan" / "install.json").read_text(encoding="utf-8")
            )
            self.assertEqual(".yuan/framework", record["layout"])

            checked = self.run_command(str(SYNC), "check", str(project))
            self.assertEqual(0, checked.returncode, checked.stdout + checked.stderr)
            self.assertIn("PASS", checked.stdout)


if __name__ == "__main__":
    unittest.main()
