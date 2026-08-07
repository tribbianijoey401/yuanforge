from __future__ import annotations

import importlib.machinery
import importlib.util
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FRAMEWORK = ROOT / "framework"


def load_installer():
    loader = importlib.machinery.SourceFileLoader(
        "yuanforge_installer", str(ROOT / "bin" / "yuanforge-init")
    )
    spec = importlib.util.spec_from_loader(loader.name, loader)
    module = importlib.util.module_from_spec(spec)
    loader.exec_module(module)
    return module


class FrameworkContractTests(unittest.TestCase):
    def test_framework_contract_and_dangling_references(self):
        installer = load_installer()
        errors, warnings = installer.validate_framework(FRAMEWORK)
        self.assertEqual([], errors)
        self.assertEqual([], warnings)

    def test_preserves_mature_capability_content(self):
        agents = [
            path
            for path in (FRAMEWORK / "agents").glob("*.md")
            if path.name != "contract-template.md"
        ]
        skills = list((FRAMEWORK / "skills").glob("*.md"))
        skills += list((FRAMEWORK / "skills").glob("*/SKILL.md"))
        references = [
            path
            for path in (FRAMEWORK / "references").rglob("*.md")
            if path.name != "README.md"
        ]

        self.assertEqual(13, len(agents))
        self.assertGreaterEqual(len(skills), 17)
        self.assertGreaterEqual(len(references), 30)

        grilling = (FRAMEWORK / "skills" / "grilling" / "SKILL.md").read_text(
            encoding="utf-8"
        )
        debugging = (FRAMEWORK / "skills" / "systematic-debugging.md").read_text(
            encoding="utf-8"
        )
        test_integrity = (
            FRAMEWORK
            / "references"
            / "01-standards"
            / "test-integrity-anti-gaming.md"
        ).read_text(encoding="utf-8")

        for dimension in range(1, 6):
            self.assertIn(f"维度 {dimension}", grilling)
        for phase in range(1, 5):
            self.assertIn(f"Phase {phase}", debugging)
        self.assertIn("作弊行为目录", test_integrity)
        self.assertIn("验证手段", test_integrity)

    def test_agent_skill_paths_exist(self):
        for agent in (FRAMEWORK / "agents").glob("*.md"):
            if agent.name == "contract-template.md":
                continue
            text = agent.read_text(encoding="utf-8")
            assignment = next(
                line for line in text.splitlines() if "Skill Assignment" in line
            )
            paths = re.findall(r"`(skills/[^`]+)`", assignment)
            self.assertTrue(paths, f"{agent.name} 没有可解析的 Skill Assignment")
            for relative in paths:
                self.assertTrue(
                    (FRAMEWORK / relative).is_file(),
                    f"{agent.name} -> {relative} 不存在",
                )

    def test_no_active_v3_state_reference(self):
        forbidden = re.compile(
            r"\.yuan/specs|\.yuan/docs|TASK_BOARD|PROGRESS\.md|SESSION_LOG|"
            r"docs/YYYY|FEATURE\.md|BUG-NNN|ADR-NNN"
        )
        active_roots = ("agents", "skills", "policies", "templates", "workflows")
        failures = []
        for directory in active_roots:
            for path in (FRAMEWORK / directory).rglob("*.md"):
                match = forbidden.search(path.read_text(encoding="utf-8"))
                if match:
                    failures.append(f"{path.relative_to(FRAMEWORK)}: {match.group(0)}")
        self.assertEqual([], failures)

    def test_project_template_is_exactly_seven_documents(self):
        actual = {
            path.name for path in (FRAMEWORK / "templates" / "project").glob("*.md")
        }
        expected = {
            "PRODUCT.md",
            "ARCHITECTURE.md",
            "DECISIONS.md",
            "BACKLOG.md",
            "WORK.md",
            "STATUS.md",
            "MEMORY.md",
        }
        self.assertEqual(expected, actual)


if __name__ == "__main__":
    unittest.main()
