from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
FRAMEWORK = ROOT / "framework"


class VerificationBaselineContractTests(unittest.TestCase):
    def test_baseline_is_risk_scoped_not_universally_full_suite(self):
        skill = (FRAMEWORK / "skills" / "test-driven-development.md").read_text(
            encoding="utf-8"
        )
        discipline = (
            FRAMEWORK / "references" / "01-standards" / "test-discipline.md"
        ).read_text(encoding="utf-8")

        for text in (skill, discipline):
            self.assertIn("risk-scoped", text)
            self.assertIn("full suite", text)
            self.assertIn("blast radius", text)

        self.assertIn("27 不是 Yuan 的要求", skill)
        self.assertIn("不为了 baseline 跑无关 Test Suite", skill)
        self.assertIn("focused baseline 冒充 full-suite green", discipline)
        self.assertIn("无条件先跑全量测试", discipline)

    def test_refactor_still_requires_green_affected_behavior_baseline(self):
        skill = (FRAMEWORK / "skills" / "test-driven-development.md").read_text(
            encoding="utf-8"
        )
        discipline = (
            FRAMEWORK / "references" / "01-standards" / "test-discipline.md"
        ).read_text(encoding="utf-8")

        self.assertIn("受影响既有行为的 Test Baseline 必须 Passing", skill)
        self.assertIn("Refactor 必须先证明受影响旧行为为绿", discipline)

    def test_verification_claim_must_match_actual_scope(self):
        skill = (FRAMEWORK / "skills" / "test-driven-development.md").read_text(
            encoding="utf-8"
        )
        discipline = (
            FRAMEWORK / "references" / "01-standards" / "test-discipline.md"
        ).read_text(encoding="utf-8")

        self.assertIn("Verification claim 必须与实际 scope 一致", skill)
        self.assertRegex(discipline, r'未跑全量时不得声称[“"](?:整个|全)项目无回归[”"]')


if __name__ == "__main__":
    unittest.main()
