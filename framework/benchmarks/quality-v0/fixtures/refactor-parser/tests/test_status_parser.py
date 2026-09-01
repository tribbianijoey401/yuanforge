from __future__ import annotations

import unittest

from status_parser import parse_status


class ParseStatusTests(unittest.TestCase):
    def test_parses_known_state_and_summary(self) -> None:
        document = "---\nwork_state: active\nagent: backend-dev\n---\nCurrent task"
        self.assertEqual(
            {"work_state": "active", "agent": "backend-dev", "summary": "Current task"},
            parse_status(document),
        )

    def test_preserves_unknown_for_invalid_or_missing_frontmatter(self) -> None:
        self.assertEqual(
            {"work_state": "UNKNOWN", "agent": None, "summary": "not a document"},
            parse_status("not a document"),
        )
