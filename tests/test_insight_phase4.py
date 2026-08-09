"""Yuan Insight Phase 4：First Signals 测试。"""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "insight"))

from yuan_insight.footprint import extract_context_refs  # noqa: E402
from yuan_insight.signals.aggregate import compute_signals  # noqa: E402
from yuan_insight.signals.bug_recurrence import (  # noqa: E402
    BugIdentityEvidence,
    compute_bug_recurrence,
)
from yuan_insight.signals.memory_effectiveness import (  # noqa: E402
    compute_memory_effectiveness,
    extract_memory_selection,
)
from yuan_insight.signals.repeated_review import (  # noqa: E402
    compute_repeated_review,
    extract_findings,
    extract_findings_from_transitions,
)


class RepeatedReviewTests(unittest.TestCase):
    def test_extract_findings_from_open_findings(self):
        findings = extract_findings(
            {
                "open_findings": [
                    "[ ] test-gap: 缺少回归测试",
                    "[ ] correctness: 逻辑缺陷",
                ],
                "latest_result": "",
            }
        )
        categories = [f.category for f in findings]
        self.assertIn("test-gap", categories)
        self.assertIn("correctness", categories)

    def test_same_round_findings_do_not_report_repeat(self):
        findings = extract_findings(
            {
                "open_findings": [
                    "test-gap: 缺测试 A",
                    "test-gap: 缺测试 B",
                    "correctness: 逻辑错",
                ],
                "latest_result": "",
            }
        )
        self.assertEqual(compute_repeated_review(findings), [])

    def test_repeated_finding_across_transitions_reports_fact_not_cause(self):
        findings = extract_findings_from_transitions(
            [
                {
                    "id": "T-1",
                    "facts": [
                        {"field": "work.latest_result", "to": "finding: test-gap: 缺测试 A"}
                    ],
                },
                {
                    "id": "T-2",
                    "facts": [
                        {"field": "work.latest_result", "to": "finding: test-gap: 缺测试 B"}
                    ],
                },
            ]
        )
        signals = compute_repeated_review(findings)
        self.assertEqual(len(signals), 1)
        self.assertEqual(signals[0].signal_id, "REPEATED-REVIEW-test-gap")
        self.assertEqual(signals[0].summary, "Repeated reviewer finding: test-gap × 2 rounds")
        self.assertNotIn("原因", signals[0].why.derived)  # 不自动解释根因

    def test_no_repeat_below_threshold(self):
        findings = extract_findings({"open_findings": ["test-gap: 一次"], "latest_result": ""})
        self.assertEqual(compute_repeated_review(findings), [])


class BugRecurrenceTests(unittest.TestCase):
    def test_unavailable_without_identity(self):
        signals = compute_bug_recurrence(BugIdentityEvidence(work_id="BUG-001"))
        self.assertEqual(signals[0].signal_id, "BUG-RECURRENCE-UNAVAILABLE")
        self.assertIn("UNAVAILABLE", signals[0].summary)

    def test_pending_with_linkage(self):
        signals = compute_bug_recurrence(
            BugIdentityEvidence(work_id="BUG-001", linked_memory_ids=["MEM-001"])
        )
        self.assertEqual(signals[0].signal_id, "BUG-RECURRENCE-PENDING")


class MemoryEffectivenessTests(unittest.TestCase):
    def test_selected_without_usage_is_unavailable(self):
        selection = extract_memory_selection(
            {"current_task": "context_refs: [docs/MEMORY.md, docs/ARCHITECTURE.md]", "latest_result": ""}
        )
        signals = compute_memory_effectiveness(selection)
        self.assertEqual(signals[0].signal_id, "MEMORY-USAGE-UNAVAILABLE")
        self.assertIn("UNAVAILABLE", signals[0].summary)

    def test_reported_used_shows_fact(self):
        selection = extract_memory_selection(
            {
                "current_task": "memory_refs: [MEM-001]",
                "latest_result": "outcome: completed\nmemory_used: MEM-001",
            }
        )
        signals = compute_memory_effectiveness(selection)
        self.assertEqual(signals[0].signal_id, "MEMORY-REPORTED-USED")

    def test_no_selection_no_signal(self):
        self.assertEqual(compute_memory_effectiveness(extract_memory_selection({"current_task": "", "latest_result": ""})), [])


class FootprintTests(unittest.TestCase):
    def test_context_footprint_counts_declared_refs(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "docs").mkdir()
            (root / "docs" / "ARCHITECTURE.md").write_text(
                "# Arch\n\n## Module A\n\n内容" * 3, encoding="utf-8"
            )
            footprint = extract_context_refs(
                {
                    "current_task": "context_refs:\n- docs/ARCHITECTURE.md\n- docs/MEMORY.md",
                    "latest_result": "",
                },
                root,
            )
            self.assertGreaterEqual(footprint.references, 2)
            self.assertGreaterEqual(footprint.documents, 1)
            self.assertGreater(footprint.characters, 0)
            self.assertGreater(footprint.sections, 0)
            self.assertIn("docs/ARCHITECTURE.md", footprint.per_document)
            self.assertEqual(footprint.references, 2)
            self.assertEqual(footprint.coverage, "PARTIAL")

    def test_missing_or_escaping_ref_is_partial_and_not_duplicated(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            footprint = extract_context_refs(
                {
                    "current_task": (
                        "context_refs:\n"
                        "  - docs/DOES_NOT_EXIST.md\n"
                        "  - ../../outside.md"
                    ),
                    "latest_result": "",
                },
                root,
            )
            self.assertEqual(footprint.references, 2)
            self.assertEqual(footprint.documents, 2)
            self.assertEqual(footprint.coverage, "PARTIAL")
            self.assertEqual(footprint.per_document, {})

    def test_no_refs_is_unknown_coverage(self):
        footprint = extract_context_refs({"current_task": "", "latest_result": ""}, Path("/tmp"))
        self.assertEqual(footprint.coverage, "UNKNOWN")
        self.assertEqual(footprint.references, 0)

    def test_logical_memory_id_is_not_counted_as_document(self):
        with tempfile.TemporaryDirectory() as temporary:
            footprint = extract_context_refs(
                {
                    "current_task": "memory_refs: [MEM-001]",
                    "latest_result": "",
                },
                Path(temporary),
            )
            self.assertEqual(footprint.references, 1)
            self.assertEqual(footprint.memory_refs, 1)
            self.assertEqual(footprint.documents, 0)
            self.assertEqual(footprint.coverage, "PARTIAL")

    def test_non_utf8_document_is_partial(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "docs").mkdir()
            (root / "docs" / "BAD.md").write_bytes(b"\xff\xfe")
            footprint = extract_context_refs(
                {
                    "current_task": "context_refs: [docs/BAD.md]",
                    "latest_result": "",
                },
                root,
            )
            self.assertEqual(footprint.coverage, "PARTIAL")
            self.assertEqual(footprint.per_document, {})


class AggregatePhase4Tests(unittest.TestCase):
    def test_aggregate_includes_phase4_signals(self):
        snapshot = {
            "work": {
                "has_active_work": True,
                "current_task": "context_refs: [docs/MEMORY.md]",
                "latest_result": "outcome: partial",
                "open_findings": ["test-gap: A", "correctness: B"],
            },
            "status": {
                "work_state": "completed",
                "agent": {"id": "backend-dev", "state": "active"},
            },
            "workflow": {
                "workflow_id": "complex-bug",
                "required_agents": ["tester"],
                "optional_agents": [],
            },
        }
        report = compute_signals(snapshot, object(), coverage="FULL")  # type: ignore[arg-type]
        signal_ids = {s.signal_id for s in report.signals}
        self.assertNotIn("REPEATED-REVIEW-test-gap", signal_ids)
        self.assertIn("BUG-RECURRENCE-UNAVAILABLE", signal_ids)
        self.assertIn("MEMORY-USAGE-UNAVAILABLE", signal_ids)


if __name__ == "__main__":
    unittest.main()
