from __future__ import annotations

import hashlib
import importlib.util
import json
import pathlib
import subprocess
import sys
import tempfile
import unittest


REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
MODULE_PATH = REPO_ROOT / "scripts" / "yuan_shadow_migrate.py"
CLI_PATH = REPO_ROOT / "scripts" / "yuan-shadow-migrate.py"


def load_module():
    spec = importlib.util.spec_from_file_location("yuan_shadow_migrate", MODULE_PATH)
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load shadow migration module")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def sha256(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path: pathlib.Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8", newline="\n")


class ShadowMigrationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.module = load_module()
        self.temp = tempfile.TemporaryDirectory()
        self.root = pathlib.Path(self.temp.name)
        write(
            self.root / "docs" / "PROGRESS.md",
            """# Progress

| **当前会话** | [`20260726-活动`](./20260726-活动/) |
""",
        )
        write(
            self.root / "docs" / "20260726-活动" / "FEATURE.md",
            """# FEATURE: 活动升级

## 用户意图

保持中文目标不丢失。

## Clean-room 验收标准

| AC | 验收条件 | 必需证据 |
|----|----------|----------|
| AC-01 | 输出可重建 | 测试 |
""",
        )
        write(
            self.root / "docs" / "20260726-活动" / "PLAN.md",
            """# Plan: 活动升级

- **目标**: 保持中文目标不丢失。
""",
        )
        write(
            self.root / "docs" / "20260726-活动" / "TASK_BOARD.md",
            """# 任务板

| ID | 任务 | 状态 |
|----|------|------|
| task-001 | 已完成步骤 | ✅ 完成 |
| task-002 | 未决步骤 | ❌ 阻塞 |
""",
        )
        write(
            self.root / "docs" / "20260726-活动" / "SESSION_LOG.md",
            "# 会话日志\n\n## 完成\n\n- 已完成步骤。\n",
        )
        write(
            self.root
            / "docs"
            / "archive"
            / "20260717-历史"
            / "TASK_BOARD.md",
            "# 任务板\n\n| ID | 任务 | 状态 |\n|---|---|---|\n| T01 | 历史任务 | ✅完成 |\n",
        )
        write(
            self.root / "docs" / "events" / "20260726" / "events.jsonl",
            json.dumps(
                {
                    "type": "TASK_STATUS_CHANGED",
                    "timestamp": "2026-07-26T10:00:00Z",
                    "session": "20260726-活动",
                    "actor": "tester",
                    "payload": {
                        "task_id": "task-001",
                        "change_type": "COMPLETE",
                        "evidence": "tests/",
                    },
                },
                ensure_ascii=False,
            )
            + "\n",
        )
        self.source_hashes = {
            path.relative_to(self.root).as_posix(): sha256(path)
            for path in (self.root / "docs").rglob("*")
            if path.is_file()
        }

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_discovery_uses_progress_for_active_and_marks_partial_history(self) -> None:
        scan = self.module.discover_legacy(self.root)
        by_id = {item.workspace_id: item for item in scan.workspaces}
        self.assertEqual("20260726-活动", scan.active_workspace_id)
        self.assertEqual("active", by_id["20260726-活动"].kind)
        self.assertEqual("archive", by_id["20260717-历史"].kind)
        self.assertIn("FEATURE.md", by_id["20260726-活动"].documents)
        self.assertTrue(
            any(
                item["code"] == "MISSING_PLAN"
                for item in by_id["20260717-历史"].unresolved
            )
        )

    def test_dry_run_writes_nothing_and_reports_coverage(self) -> None:
        shadow = self.root / ".yuan-shadow"
        report = self.module.migrate(self.root, shadow, dry_run=True)
        self.assertFalse(shadow.exists())
        self.assertEqual("DRY_RUN", report["operation"])
        self.assertGreater(report["covered_sources"], 0)
        self.assertGreater(report["unresolved_count"], 0)

    def test_migration_is_read_only_core_valid_and_rebuildable(self) -> None:
        shadow = self.root / ".yuan-shadow"
        report = self.module.migrate(self.root, shadow)
        self.assertEqual("MIGRATED", report["operation"])
        after = {
            path.relative_to(self.root).as_posix(): sha256(path)
            for path in (self.root / "docs").rglob("*")
            if path.is_file()
        }
        self.assertEqual(self.source_hashes, after)

        active = shadow / "workspaces" / "20260726-活动"
        work = json.loads((active / "work-contract.json").read_text(encoding="utf-8"))
        memory = json.loads((active / "run-memory.json").read_text(encoding="utf-8"))
        self.assertEqual("yuan.work-contract/v1", work["schema_version"])
        self.assertEqual("BLOCKED", memory["last_result"])
        self.assertIn("保持中文目标不丢失", work["intent"]["goal"])
        self.assertTrue((active / "attempts" / "0001.json").is_file())
        self.assertTrue((active / "evidence" / "0001.json").is_file())
        replay = json.loads(
            (active / "replay-report.json").read_text(encoding="utf-8")
        )
        self.assertGreaterEqual(replay["replayed_record_count"], 3)
        self.assertEqual([], report["validation_errors"])
        verification = self.module.verify(self.root, shadow)
        self.assertEqual("PASS", verification["status"])
        self.assertEqual(2, verification["assertions"])

    def test_repeat_run_has_identical_content_digest(self) -> None:
        first = self.root / ".yuan-shadow-a"
        second = self.root / ".yuan-shadow-b"
        first_report = self.module.migrate(self.root, first)
        second_report = self.module.migrate(self.root, second)
        self.assertEqual(
            first_report["projection_digest"], second_report["projection_digest"]
        )
        self.assertEqual(
            json.loads((first / "report.json").read_text(encoding="utf-8"))[
                "projection_digest"
            ],
            json.loads((second / "report.json").read_text(encoding="utf-8"))[
                "projection_digest"
            ],
        )

    def test_writer_guard_rejects_cross_lane_and_stale_cas(self) -> None:
        pointer = {
            "schema_version": "yuan.authority-pointer/v1",
            "revision": 1,
            "authority": "legacy",
            "legacy_root": "docs",
            "shadow_root": ".yuan-shadow",
            "legacy_snapshot_sha256": "0" * 64,
        }
        self.module.assert_write_allowed(
            self.root, pointer, "shadow", ".yuan-shadow/new.json", None
        )
        with self.assertRaises(self.module.GuardError):
            self.module.assert_write_allowed(
                self.root, pointer, "shadow", "docs/PROGRESS.md", None
            )
        with self.assertRaises(self.module.GuardError):
            self.module.assert_write_allowed(
                self.root, pointer, "legacy", ".yuan-shadow/new.json", None
            )
        with self.assertRaises(self.module.GuardError):
            self.module.assert_write_allowed(
                self.root,
                pointer,
                "legacy",
                "docs/PROGRESS.md",
                "f" * 64,
            )

    def test_path_safety_rejects_legacy_or_repository_as_shadow(self) -> None:
        for unsafe in (self.root, self.root / "docs", self.root.parent / "outside"):
            with self.subTest(unsafe=unsafe):
                with self.assertRaises(self.module.MigrationError):
                    self.module.migrate(self.root, unsafe)

    def test_empty_legacy_repository_fails_closed(self) -> None:
        empty = self.root / "empty"
        write(empty / "docs" / "PROGRESS.md", "# no active workspace\n")
        with self.assertRaises(self.module.MigrationError):
            self.module.migrate(empty, empty / ".yuan-shadow")

    def test_rollback_removes_only_verified_shadow_and_preserves_legacy(self) -> None:
        shadow = self.root / ".yuan-shadow"
        self.module.migrate(self.root, shadow)
        receipt_path = self.root / "rollback-receipt.json"
        receipt = self.module.rollback(self.root, shadow, receipt_path)
        self.assertFalse(shadow.exists())
        self.assertEqual("ROLLED_BACK", receipt["status"])
        self.assertEqual(
            receipt["legacy_before_sha256"], receipt["legacy_after_sha256"]
        )
        after = {
            path.relative_to(self.root).as_posix(): sha256(path)
            for path in (self.root / "docs").rglob("*")
            if path.is_file()
        }
        self.assertEqual(self.source_hashes, after)

    def test_rollback_fails_closed_when_shadow_contains_unknown_file(self) -> None:
        shadow = self.root / ".yuan-shadow"
        self.module.migrate(self.root, shadow)
        write(shadow / "foreign.txt", "do not delete")
        with self.assertRaises(self.module.MigrationError):
            self.module.rollback(
                self.root, shadow, self.root / "rollback-receipt.json"
            )
        self.assertTrue(shadow.is_dir())
        self.assertTrue((shadow / "foreign.txt").is_file())

    def test_cli_emits_utf8_json(self) -> None:
        shadow = self.root / ".yuan-shadow"
        result = subprocess.run(
            [
                sys.executable,
                str(CLI_PATH),
                "migrate",
                "--repo",
                str(self.root),
                "--shadow-root",
                str(shadow),
                "--dry-run",
            ],
            check=False,
            capture_output=True,
        )
        self.assertEqual(0, result.returncode, result.stderr.decode("utf-8"))
        payload = json.loads(result.stdout.decode("utf-8"))
        self.assertEqual("DRY_RUN", payload["operation"])


if __name__ == "__main__":
    unittest.main()
