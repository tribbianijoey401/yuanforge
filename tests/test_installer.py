from __future__ import annotations

import json
import os
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
        env = os.environ.copy()
        env["PYTHONIOENCODING"] = "utf-8"
        return subprocess.run(
            [sys.executable, "-B", *args],
            cwd=ROOT,
            text=True,
            encoding="utf-8",
            env=env,
            capture_output=True,
            check=False,
        )

    def test_new_install_creates_vnext_layout_and_natural_prompt(self):
        with tempfile.TemporaryDirectory(prefix="yuan-vnext-new-") as parent:
            project = Path(parent) / "project"
            result = self.run_command(str(INSTALLER), str(project), "--force")
            self.assertEqual(0, result.returncode, result.stdout + result.stderr)

            self.assertTrue((project / ".yuan" / "framework").is_dir())
            self.assertTrue(
                (project / ".yuan" / "insight" / "tool" / "yuan_insight" / "cli.py").is_file()
            )
            self.assertTrue((project / ".yuan" / "insight" / "yuan.py").is_file())
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

            observed = self.run_command(
                str(project / ".yuan" / "insight" / "yuan.py"),
                "observe",
                str(project),
                "--once",
            )
            self.assertEqual(0, observed.returncode, observed.stdout + observed.stderr)
            self.assertIn('"status": "OBSERVED"', observed.stdout)

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
            insight_history = project / ".yuan" / "insight" / "summaries" / "OLD.json"
            insight_history.parent.mkdir(parents=True)
            insight_history.write_text('{"work_id":"OLD"}\n', encoding="utf-8")

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
            self.assertEqual(
                (ROOT / "AGENTS.md").read_bytes(),
                (project / "AGENTS.md").read_bytes(),
            )
            self.assertEqual(
                (ROOT / "framework" / "policies" / "core.md").read_bytes(),
                (project / ".yuan" / "framework" / "policies" / "core.md").read_bytes(),
            )
            self.assertEqual(
                (ROOT / "insight" / "yuan_insight" / "cli.py").read_bytes(),
                (
                    project
                    / ".yuan"
                    / "insight"
                    / "tool"
                    / "yuan_insight"
                    / "cli.py"
                ).read_bytes(),
            )
            self.assertEqual(
                '{"work_id":"OLD"}\n', insight_history.read_text(encoding="utf-8")
            )
            self.assertTrue(
                (project / ".yuan" / "insight" / "tool" / "yuan_insight" / "cli.py").is_file()
            )
            record = json.loads(
                (project / ".yuan" / "install.json").read_text(encoding="utf-8")
            )
            self.assertEqual(".yuan/framework", record["layout"])
            self.assertEqual(".yuan/insight/tool", record["insight_tool"])

            checked = self.run_command(str(SYNC), "check", str(project))
            self.assertEqual(0, checked.returncode, checked.stdout + checked.stderr)
            self.assertIn("PASS", checked.stdout)

    def test_update_blocks_active_work_before_changing_managed_files(self):
        with tempfile.TemporaryDirectory(prefix="yuan-vnext-active-update-") as parent:
            project = Path(parent) / "project"
            docs = project / "docs"
            docs.mkdir(parents=True)
            status = docs / "STATUS.md"
            status.write_text(
                """---
work: FEATURE-1
work_state: active
workflow: new-feature
stage: implement
---

# Current Situation

正在实现。
""",
                encoding="utf-8",
            )
            work = docs / "WORK.md"
            work.write_text("# Active Work\n\n## Goal\n\n完成 FEATURE-1。\n", encoding="utf-8")
            stale = project / ".yuan" / "framework" / "stale.txt"
            stale.parent.mkdir(parents=True)
            stale.write_text("must remain until update is allowed\n", encoding="utf-8")

            result = self.run_command(str(SYNC), "update", str(project))

            self.assertNotEqual(0, result.returncode)
            self.assertIn("UPDATE_BLOCKED_ACTIVE_WORK", result.stdout + result.stderr)
            self.assertTrue(stale.is_file())
            self.assertEqual(
                "# Active Work\n\n## Goal\n\n完成 FEATURE-1。\n",
                work.read_text(encoding="utf-8"),
            )

    def test_update_allows_paused_work_and_preserves_checkpoint(self):
        with tempfile.TemporaryDirectory(prefix="yuan-vnext-paused-update-") as parent:
            project = Path(parent) / "project"
            docs = project / "docs"
            docs.mkdir(parents=True)
            status = docs / "STATUS.md"
            status_payload = """---
work: FEATURE-2
work_state: paused
workflow: new-feature
stage: implement
---

# Current Situation

Work 已暂停，等待下次 Session 恢复。
"""
            status.write_text(status_payload, encoding="utf-8")
            work = docs / "WORK.md"
            work_payload = "# Active Work\n\n## Goal\n\n完成 FEATURE-2。\n\n## Current Task\n\n从断点继续。\n"
            work.write_text(work_payload, encoding="utf-8")

            result = self.run_command(str(SYNC), "update", str(project))

            self.assertEqual(0, result.returncode, result.stdout + result.stderr)
            self.assertEqual(status_payload, status.read_text(encoding="utf-8"))
            self.assertEqual(work_payload, work.read_text(encoding="utf-8"))
            self.assertTrue((project / ".yuan" / "framework" / "VERSION").is_file())

    def test_update_allows_unstructured_existing_work_state_without_rewriting_it(self):
        with tempfile.TemporaryDirectory(prefix="yuan-vnext-unknown-update-") as parent:
            project = Path(parent) / "project"
            docs = project / "docs"
            docs.mkdir(parents=True)
            status = docs / "STATUS.md"
            status_payload = "# Status\n\n- **State**: Completed\n"
            status.write_text(status_payload, encoding="utf-8")
            work = docs / "WORK.md"
            work_payload = "# Active Work\n\n## Goal\n\n遗留 Work。\n"
            work.write_text(work_payload, encoding="utf-8")

            result = self.run_command(str(SYNC), "update", str(project))

            self.assertEqual(0, result.returncode, result.stdout + result.stderr)
            self.assertEqual(status_payload, status.read_text(encoding="utf-8"))
            self.assertEqual(work_payload, work.read_text(encoding="utf-8"))
            self.assertTrue((project / ".yuan" / "framework" / "VERSION").is_file())

    def test_existing_install_does_not_interpret_project_documents(self):
        with tempfile.TemporaryDirectory(prefix="yuan-vnext-existing-install-") as parent:
            project = Path(parent) / "project"
            docs = project / "docs"
            docs.mkdir(parents=True)
            status = docs / "STATUS.md"
            status_payload = "# Project Status\n\nThis file belongs to the project.\n"
            status.write_text(status_payload, encoding="utf-8")
            work = docs / "WORK.md"
            work_payload = "# Work Notes\n\nThis is not Yuan state.\n"
            work.write_text(work_payload, encoding="utf-8")

            result = self.run_command(
                str(INSTALLER), str(project), "--mode", "existing", "--force"
            )

            self.assertEqual(0, result.returncode, result.stdout + result.stderr)
            self.assertEqual(status_payload, status.read_text(encoding="utf-8"))
            self.assertEqual(work_payload, work.read_text(encoding="utf-8"))
            self.assertTrue((project / ".yuan" / "framework" / "VERSION").is_file())

    def test_update_reports_each_preserved_yuan_path_and_reason(self):
        with tempfile.TemporaryDirectory(prefix="yuan-vnext-preserved-report-") as parent:
            project = Path(parent) / "project"
            docs = project / "docs"
            docs.mkdir(parents=True)
            (docs / "STATUS.md").write_text(
                """---
work: null
work_state: idle
workflow: null
stage: null
---
""",
                encoding="utf-8",
            )
            (docs / "WORK.md").write_text(
                "# Active Work\n\nNo active work.\n",
                encoding="utf-8",
            )
            (docs / "MEMORY.md").write_text(
                "# Persistent Memory\n\nProject-owned fact.\n",
                encoding="utf-8",
            )
            override = project / ".yuan" / "overrides" / "policies" / "core.md"
            override.parent.mkdir(parents=True)
            override.write_text("# Override\n", encoding="utf-8")
            trace = project / ".yuan" / "insight" / "traces" / "current.jsonl"
            trace.parent.mkdir(parents=True)
            trace.write_text("{}\n", encoding="utf-8")
            gitignore = project / ".gitignore"
            gitignore.write_text("# Project rules\nbuild/\n", encoding="utf-8")

            result = self.run_command(str(SYNC), "update", str(project))

            self.assertEqual(0, result.returncode, result.stdout + result.stderr)
            self.assertIn("PRESERVED docs/STATUS.md | Project Document", result.stdout)
            self.assertIn("PRESERVED docs/WORK.md | Project Document", result.stdout)
            self.assertIn("PRESERVED docs/MEMORY.md | Project Document", result.stdout)
            self.assertIn("PRESERVED .yuan/overrides/ | Project Override", result.stdout)
            self.assertIn(
                "PRESERVED .yuan/insight/traces/ | Insight Observation Data",
                result.stdout,
            )
            self.assertIn("MERGED .gitignore", result.stdout)
            self.assertEqual("# Override\n", override.read_text(encoding="utf-8"))
            self.assertEqual("{}\n", trace.read_text(encoding="utf-8"))
            self.assertTrue(gitignore.read_text(encoding="utf-8").startswith("# Project rules\nbuild/\n"))

    def test_check_warns_on_active_work_status_divergence_without_failing(self):
        with tempfile.TemporaryDirectory(prefix="yuan-vnext-state-check-") as parent:
            project = Path(parent) / "project"
            installed = self.run_command(str(INSTALLER), str(project), "--force")
            self.assertEqual(0, installed.returncode, installed.stdout + installed.stderr)
            (project / "docs" / "WORK.md").write_text(
                "# Active Work\n\n## Goal\n\n修复状态漂移。\n",
                encoding="utf-8",
            )

            checked = self.run_command(str(SYNC), "check", str(project))

            self.assertEqual(0, checked.returncode, checked.stdout + checked.stderr)
            self.assertIn("STATE_DIVERGENCE", checked.stdout)
            self.assertIn("PASS", checked.stdout)

    def test_check_reuses_state_guard_for_unknown_stage_and_agent(self):
        with tempfile.TemporaryDirectory(prefix="yuan-vnext-state-guard-check-") as parent:
            project = Path(parent) / "project"
            installed = self.run_command(str(INSTALLER), str(project), "--force")
            self.assertEqual(0, installed.returncode, installed.stdout + installed.stderr)
            (project / "docs" / "STATUS.md").write_text(
                """---
work: BUG-contract
work_state: active
workflow: complex-bug
stage: specialist_execution
agent:
  id: frontend-fixer
  state: running
---
""",
                encoding="utf-8",
            )
            (project / "docs" / "WORK.md").write_text(
                "# Active Work\n\n## Goal\n\n修复状态。\n\n"
                "## Current Task\n\n执行实现。\n",
                encoding="utf-8",
            )

            checked = self.run_command(str(SYNC), "check", str(project))

            self.assertEqual(0, checked.returncode, checked.stdout + checked.stderr)
            self.assertIn("STATE_DIVERGENCE[STATE_STAGE_UNKNOWN]", checked.stdout)
            self.assertIn("STATE_DIVERGENCE[STATE_AGENT_UNKNOWN]", checked.stdout)
            self.assertIn("STATE_DIVERGENCE[STATE_AGENT_STATE_UNKNOWN]", checked.stdout)

    def test_update_repairs_only_missing_project_documents(self):
        with tempfile.TemporaryDirectory(prefix="yuan-vnext-repair-docs-") as parent:
            project = Path(parent) / "project"
            docs = project / "docs"
            docs.mkdir(parents=True)
            memory = docs / "MEMORY.md"
            memory_payload = b"# Persistent Memory\n\nproject-owned bytes\n"
            memory.write_bytes(memory_payload)

            result = self.run_command(str(SYNC), "update", str(project))

            self.assertEqual(0, result.returncode, result.stdout + result.stderr)
            self.assertEqual(memory_payload, memory.read_bytes())
            for name in (
                "PRODUCT.md",
                "ARCHITECTURE.md",
                "DECISIONS.md",
                "BACKLOG.md",
                "WORK.md",
                "STATUS.md",
            ):
                self.assertTrue((docs / name).is_file(), name)
                self.assertIn(f"CREATED docs/{name}", result.stdout)

            checked = self.run_command(str(SYNC), "check", str(project))
            self.assertEqual(0, checked.returncode, checked.stdout + checked.stderr)

    def test_check_fails_when_required_work_state_files_are_missing(self):
        with tempfile.TemporaryDirectory(prefix="yuan-vnext-missing-state-") as parent:
            project = Path(parent) / "project"
            installed = self.run_command(str(INSTALLER), str(project), "--force")
            self.assertEqual(0, installed.returncode, installed.stdout + installed.stderr)
            (project / "docs" / "WORK.md").unlink()
            (project / "docs" / "STATUS.md").unlink()

            checked = self.run_command(str(SYNC), "check", str(project))

            self.assertNotEqual(0, checked.returncode)
            self.assertIn("缺少 Project Document：docs/WORK.md", checked.stdout)
            self.assertIn("缺少 Project Document：docs/STATUS.md", checked.stdout)


if __name__ == "__main__":
    unittest.main()
