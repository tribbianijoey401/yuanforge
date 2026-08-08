"""Yuan Insight Phase 3：Expected vs Observed Engine 测试。"""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "insight"))

from yuan_insight.registry import AgentContract, Registry, load_registry, _parse_skill_assignment  # noqa: E402
from yuan_insight.signals.aggregate import compute_signals, _extract_skills_applied  # noqa: E402
from yuan_insight.signals.expected_observed import (  # noqa: E402
    compute_missing_agents,
    compute_missing_skills,
    expected_from_workflow,
    observed_from_snapshot,
)


class RegistryTests(unittest.TestCase):
    def test_parse_skill_assignment_tiers(self):
        required, recommended, conditional = _parse_skill_assignment(
            "Required `skills/test-driven-development.md`；"
            "Conditional `skills/systematic-debugging.md`（仅 Bug 时）；"
            "Recommended `skills/writing-plans.md`"
        )
        self.assertEqual(required, ["test-driven-development"])
        self.assertEqual(conditional, ["systematic-debugging"])
        self.assertEqual(recommended, ["writing-plans"])

    def test_load_registry_from_framework(self):
        registry = load_registry(ROOT / "framework")
        self.assertGreaterEqual(len(registry.agents), 13)
        self.assertGreaterEqual(len(registry.skills), 17)
        self.assertGreaterEqual(len(registry.workflows), 4)
        self.assertIn("backend-dev", registry.agents)
        self.assertIn("test-driven-development", registry.agents["backend-dev"].required_skills)


class ExpectedObservedTests(unittest.TestCase):
    def test_expected_from_workflow_dedupes_writers(self):
        expected = expected_from_workflow(
            {
                "required_agents": ["conductor", "frontend-dev", "backend-dev", "tester"],
                "optional_agents": ["architect"],
            },
            Registry(),
        )
        # frontend-dev/backend-dev 是 writer 二选一，只保留一个
        writers = [agent for agent in expected.required if agent in ("frontend-dev", "backend-dev")]
        self.assertEqual(len(writers), 1)

    def test_observed_from_snapshot(self):
        observed = observed_from_snapshot(
            {"status": {"agent": {"id": "backend-dev", "state": "active"}}}
        )
        self.assertEqual(observed.observed_ids, ["backend-dev"])
        self.assertEqual(observed.coverage, "PARTIAL")

    def test_missing_requires_full_coverage(self):
        expected = expected_from_workflow(
            {"required_agents": ["tester"], "optional_agents": []},
            Registry(),
        )
        observed = observed_from_snapshot({"agent": {"id": "backend-dev", "state": "active"}})
        # PARTIAL coverage 不判 Missing
        signals = compute_missing_agents(expected, observed, coverage="PARTIAL")
        self.assertEqual(signals, [])
        # FULL coverage 且 tester 未出现 → Missing
        signals = compute_missing_agents(expected, observed, coverage="FULL")
        self.assertEqual(len(signals), 1)
        self.assertEqual(signals[0].signal_id, "MISSING-AGENT-tester")
        self.assertEqual(signals[0].why.expected_rule, "Workflow required_agents 声明 tester")

    def test_missing_skill_requires_observed_evidence(self):
        signals = compute_missing_skills(
            ["systematic-debugging"], [], coverage="FULL"
        )
        self.assertEqual(signals, [])  # 无 observed skills_applied 事实，不判 Missing
        signals = compute_missing_skills(
            ["systematic-debugging"], ["test-driven-development"], coverage="FULL"
        )
        self.assertEqual(len(signals), 1)
        self.assertEqual(signals[0].signal_id, "MISSING-SKILL-systematic-debugging")


class AggregateTests(unittest.TestCase):
    def test_extract_skills_applied_from_result(self):
        skills = _extract_skills_applied(
            "outcome: completed\nskills_applied:\n- systematic-debugging\n- test-driven-development\nnext: 回归测试"
        )
        self.assertEqual(skills, ["systematic-debugging", "test-driven-development"])

    def test_aggregate_unknown_coverage_no_signals(self):
        snapshot = {
            "work": {"has_active_work": True, "latest_result": "outcome: completed"},
            "status": {"agent": {"id": "backend-dev", "state": "active"}},
            "workflow": {
                "workflow_id": "complex-bug",
                "required_agents": ["tester"],
                "optional_agents": [],
                "required_skills": [],
            },
        }
        report = compute_signals(snapshot, Registry(), coverage="UNKNOWN")
        self.assertEqual(report.signals, [])
        self.assertEqual(report.coverage, "UNKNOWN")

    def test_aggregate_full_coverage_missing_signal(self):
        snapshot = {
            "work": {"has_active_work": True, "latest_result": "outcome: completed"},
            "status": {"agent": {"id": "backend-dev", "state": "active"}},
            "workflow": {
                "workflow_id": "complex-bug",
                "required_agents": ["tester"],
                "optional_agents": [],
                "required_skills": [],
            },
        }
        report = compute_signals(snapshot, Registry(), coverage="FULL")
        self.assertGreaterEqual(len(report.signals), 1)
        self.assertTrue(
            any(s.signal_id == "MISSING-AGENT-tester" for s in report.signals)
        )
        why = report.signals[0].why
        self.assertTrue(why.expected_rule)
        self.assertTrue(why.observed)
        self.assertTrue(why.derived)
        self.assertTrue(why.check)


if __name__ == "__main__":
    unittest.main()
