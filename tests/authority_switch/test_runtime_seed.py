"""TDD for flattening a verified shadow projection into .yuan-run."""

from __future__ import annotations

import importlib.util
import json
import pathlib
import shutil
import sys
import tempfile
import unittest
from unittest import mock


ROOT = pathlib.Path(__file__).resolve().parents[2]
MODULE_PATH = ROOT / "scripts/yuan_runtime_seed.py"


class RuntimeSeedTests(unittest.TestCase):
    def test_only_active_verified_projection_becomes_sealed_runtime(self) -> None:
        spec = importlib.util.spec_from_file_location("yuan_runtime_seed", MODULE_PATH)
        assert spec and spec.loader
        sys.path.insert(0, str(MODULE_PATH.parent))
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        with tempfile.TemporaryDirectory(prefix="yuan-m8-seed-") as name:
            repo = pathlib.Path(name)
            shutil.copytree(ROOT / ".yuan/core", repo / ".yuan/core")
            shadow = repo / ".projection"
            active = shadow / "workspaces" / "w-active"
            inactive = shadow / "workspaces" / "w-old"
            fixtures = ROOT / ".yuan/core/0.1/fixtures/valid"
            for root in (active, inactive):
                (root / "attempts").mkdir(parents=True)
                (root / "evidence").mkdir()
                shutil.copyfile(fixtures / "work-contract.json", root / "work-contract.json")
                shutil.copyfile(fixtures / "attempt.json", root / "attempts/0001.json")
                shutil.copyfile(fixtures / "evidence.json", root / "evidence/0001.json")
            (shadow / "report.json").write_text(
                json.dumps(
                    {
                        "active_workspace_id": "w-active",
                        "legacy_snapshot_sha256": "1" * 64,
                        "projection_digest": "2" * 64,
                    }
                ),
                encoding="utf-8",
            )
            verified = {
                "status": "PASS",
                "legacy_snapshot_sha256": "1" * 64,
                "projection_digest": "2" * 64,
            }
            with mock.patch.object(
                module, "verify_shadow_projection", return_value=verified
            ):
                receipt = module.seed_verified_projection(repo, shadow)
            runtime = repo / ".yuan-run"
            self.assertEqual("w-active", receipt["active_workspace_id"])
            self.assertTrue((runtime / "contracts/w-active.json").is_file())
            self.assertTrue((runtime / "attempts/0001.json").is_file())
            self.assertTrue((runtime / "evidence/0001.json").is_file())
            self.assertTrue((runtime / "runtime-manifest.json").is_file())
            self.assertFalse((runtime / "contracts/w-old.json").exists())
            module.verify_runtime(repo)


if __name__ == "__main__":
    unittest.main()
