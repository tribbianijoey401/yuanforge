from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from config import ConfigError, load_settings


class LoadSettingsTests(unittest.TestCase):
    def test_loads_existing_required_setting(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "settings.json"
            path.write_text(json.dumps({"name": "worker"}), encoding="utf-8")
            self.assertEqual({"name": "worker"}, load_settings(path))

    def test_uses_project_error_for_invalid_shape(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "settings.json"
            path.write_text("{}", encoding="utf-8")
            with self.assertRaises(ConfigError):
                load_settings(path)
