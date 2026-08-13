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
    def test_logical_locators_are_unambiguous_in_runtime_contracts(self):
        adapter = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
        for locator in ("project://", "framework://", "skill://"):
            self.assertIn(locator, adapter)
        self.assertIn("不是目录名、环境变量或可直接传给 Tool 的 URL", adapter)
        self.assertIn("每次文件操作前", adapter)

        active_paths = []
        for directory in ("agents", "skills", "workflows", "adapters"):
            active_paths.extend((FRAMEWORK / directory).rglob("*.md"))
        active_paths.extend((FRAMEWORK / "policies").rglob("*.md"))

        ambiguous = re.compile(
            r"`((?:docs|policies|agents|skills|workflows|adapters|templates|references)/[^`]+)`"
        )
        failures = []
        for path in active_paths:
            for line_number, line in enumerate(
                path.read_text(encoding="utf-8").splitlines(), 1
            ):
                match = ambiguous.search(line)
                if match:
                    failures.append(
                        f"{path.relative_to(FRAMEWORK)}:{line_number}: {match.group(1)}"
                    )
        self.assertEqual([], failures)

    def test_specialist_skills_return_state_updates_to_conductor(self):
        for relative in (
            "systematic-debugging.md",
            "test-driven-development.md",
            "writing-plans.md",
            "project-memory.md",
            "distill-workspace.md",
        ):
            text = (FRAMEWORK / "skills" / relative).read_text(encoding="utf-8")
            self.assertIn("Conductor", text, relative)
            self.assertIn("work_updates", text, relative)

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
        self.assertGreaterEqual(len(skills), 18)
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

    def test_deep_requirement_discovery_is_complete_and_two_stage(self):
        discovery_path = (
            FRAMEWORK / "skills" / "deep-requirement-discovery" / "SKILL.md"
        )
        discovery = discovery_path.read_text(encoding="utf-8")
        self.assertIn("name: deep-requirement-discovery", discovery)
        self.assertGreaterEqual(len(discovery.splitlines()), 1000)
        for section in (
            "第一性原理",
            "证据纪律",
            "竞争性假设",
            "Reframe",
            "Cognitive Flow Design",
            "Depth Gate",
            "Decision Trail",
            "什么时候停止",
        ):
            self.assertIn(section, discovery)

        analyst = (FRAMEWORK / "agents" / "product-analyst.md").read_text(
            encoding="utf-8"
        )
        assignment = next(
            line for line in analyst.splitlines() if "Skill Assignment" in line
        )
        self.assertRegex(
            assignment,
            r"Conditional `framework://skills/deep-requirement-discovery/SKILL\.md`.*"
            r"Required `framework://skills/grilling/SKILL\.md`",
        )
        self.assertIn("deep-requirement-discovery → grilling", analyst)
        self.assertIn("不得从零重新访谈", analyst)

        large_project = (FRAMEWORK / "workflows" / "large-project.md").read_text(
            encoding="utf-8"
        )
        new_feature = (FRAMEWORK / "workflows" / "new-feature.md").read_text(
            encoding="utf-8"
        )
        self.assertNotIn("deep-requirement-discovery", large_project)
        self.assertNotIn("deep-requirement-discovery", new_feature)

    def test_agent_skill_paths_exist(self):
        for agent in (FRAMEWORK / "agents").glob("*.md"):
            if agent.name == "contract-template.md":
                continue
            text = agent.read_text(encoding="utf-8")
            assignment = next(
                line for line in text.splitlines() if "Skill Assignment" in line
            )
            paths = re.findall(r"`framework://(skills/[^`]+)`", assignment)
            self.assertTrue(paths, f"{agent.name} 没有可解析的 Skill Assignment")
            for relative in paths:
                self.assertTrue(
                    (FRAMEWORK / relative).is_file(),
                    f"{agent.name} -> {relative} 不存在",
                )

    def test_skill_assignment_uses_tiered_annotation(self):
        for agent in (FRAMEWORK / "agents").glob("*.md"):
            if agent.name == "contract-template.md":
                continue
            text = agent.read_text(encoding="utf-8")
            assignment = next(
                line for line in text.splitlines() if "Skill Assignment" in line
            )
            paths = re.findall(r"`framework://(skills/[^`]+)`", assignment)
            self.assertTrue(paths, f"{agent.name} 没有可解析的 Skill Assignment")
            for relative in paths:
                segments = re.split(r"[；;]", assignment)
                owner = next(
                    seg for seg in segments if f"`framework://{relative}`" in seg
                )
                self.assertTrue(
                    re.search(r"(Required|Recommended|Conditional)", owner),
                    f"{agent.name} -> {relative} 所在片段缺少 Required/Recommended/Conditional 标注",
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

    def test_workflow_frontmatter_declares_agents_only(self):
        required_fields = {
            "workflow",
            "stages",
            "required_agents",
            "required_agent_groups",
            "optional_agents",
        }
        agent_ids = {
            path.stem
            for path in (FRAMEWORK / "agents").glob("*.md")
            if path.name != "contract-template.md"
        }
        workflows = sorted((FRAMEWORK / "workflows").glob("*.md"))
        self.assertGreaterEqual(len(workflows), 4)
        for path in workflows:
            text = path.read_text(encoding="utf-8")
            self.assertTrue(text.startswith("---"), f"{path.name} 缺少 Frontmatter")
            body = text.split("---", 2)
            self.assertEqual(len(body), 3, f"{path.name} Frontmatter 不完整")
            frontmatter = body[1]
            declared_fields = set(re.findall(r"^(\w+):", frontmatter, re.M))
            self.assertTrue(
                required_fields <= declared_fields,
                f"{path.name} 缺少字段：{sorted(required_fields - declared_fields)}",
            )
            declared = load_installer().parse_frontmatter_lists(frontmatter)
            for field in ("required_agents", "optional_agents"):
                declared_ids = set(declared.get(field, []))
                self.assertTrue(
                    declared_ids <= agent_ids,
                    f"{path.name} {field} 声明了不存在的 Agent：{sorted(declared_ids - agent_ids)}",
                )
            for group in declared.get("required_agent_groups", []):
                members = {item for item in group.split("|") if item}
                self.assertGreaterEqual(len(members), 2, f"{path.name} one-of Group 至少两个 Agent")
                self.assertTrue(
                    members <= agent_ids,
                    f"{path.name} required_agent_groups 存在未知 Agent：{sorted(members - agent_ids)}",
                )
            self.assertNotIn(
                "required_skills",
                declared_fields,
                f"{path.name} 不得越级选择 Skill",
            )
            self.assertIn(
                "conductor", set(declared.get("required_agents", [])),
                f"{path.name} required_agents 必须包含 conductor",
            )

    def test_completion_contract_clears_active_state_after_distill(self):
        conductor = (FRAMEWORK / "agents" / "conductor.md").read_text(encoding="utf-8")
        adapter = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
        for text in (conductor, adapter):
            self.assertIn("Open Findings = 0", text)
            self.assertIn("Distill", text)
            self.assertIn("WORK.md", text)
            self.assertIn("STATUS.md", text)
            self.assertIn("no active work", text)

    def test_pause_contract_preserves_work_and_is_resumable(self):
        core = (FRAMEWORK / "policies" / "core.md").read_text(encoding="utf-8")
        documents = (FRAMEWORK / "policies" / "documents.md").read_text(encoding="utf-8")
        status_template = (FRAMEWORK / "templates" / "project" / "STATUS.md").read_text(
            encoding="utf-8"
        )
        work_template = (FRAMEWORK / "templates" / "project" / "WORK.md").read_text(
            encoding="utf-8"
        )
        adapter = (ROOT / "AGENTS.md").read_text(encoding="utf-8")

        for text in (core, documents, status_template, adapter):
            self.assertIn("paused", text)
        self.assertIn("暂停时保留全文", work_template)
        self.assertIn("不得归档", documents)
        self.assertIn("不得归档或清空", adapter)
        self.assertIn("Next Action", documents)

    def test_work_activation_writes_structured_status_checkpoint(self):
        conductor = (FRAMEWORK / "agents" / "conductor.md").read_text(encoding="utf-8")
        documents = (FRAMEWORK / "policies" / "documents.md").read_text(encoding="utf-8")
        adapter = (ROOT / "AGENTS.md").read_text(encoding="utf-8")

        for text in (conductor, documents, adapter):
            self.assertIn("同一逻辑步骤", text)
            self.assertIn("work_state: active", text)
            self.assertIn("Workflow", text)
            self.assertIn("Stage", text)
            self.assertIn("当前 Agent", text)

    def test_every_workflow_supports_user_requested_pause_and_resume(self):
        for workflow in sorted((FRAMEWORK / "workflows").glob("*.md")):
            text = workflow.read_text(encoding="utf-8")
            self.assertIn("## Pause / Resume", text, workflow.name)
            self.assertIn("work_state: paused", text, workflow.name)
            self.assertIn("Next Action", text, workflow.name)
            self.assertIn("当前 Stage", text, workflow.name)

        conductor = (FRAMEWORK / "agents" / "conductor.md").read_text(encoding="utf-8")
        for phrase in ("先离开", "挂起", "暂停"):
            self.assertIn(phrase, conductor)
        self.assertIn("停止继续派发", conductor)

    def test_conductor_is_the_only_formal_work_state_writer(self):
        conductor = (FRAMEWORK / "agents" / "conductor.md").read_text(encoding="utf-8")
        documents = (FRAMEWORK / "policies" / "documents.md").read_text(encoding="utf-8")
        core = (FRAMEWORK / "policies" / "core.md").read_text(encoding="utf-8")
        for text in (conductor, documents, core):
            self.assertIn("唯一正式 State Writer", text)
            self.assertIn("Conductor commit", text)

        for agent in (FRAMEWORK / "agents").glob("*.md"):
            if agent.name in {"conductor.md", "contract-template.md"}:
                continue
            text = agent.read_text(encoding="utf-8")
            self.assertIn("State Ownership", text, agent.name)
            self.assertIn("Conductor", text, agent.name)

        status_template = (FRAMEWORK / "templates" / "project" / "STATUS.md").read_text(
            encoding="utf-8"
        )
        self.assertNotRegex(status_template, r"(?im)^revision:")
        self.assertIn("不保存 visualization revision", documents)

    def test_state_commit_has_machine_checked_canonical_contract(self):
        adapter = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
        conductor = (FRAMEWORK / "agents" / "conductor.md").read_text(encoding="utf-8")
        coordination = (FRAMEWORK / "skills" / "vibecoding-workflow.md").read_text(
            encoding="utf-8"
        )
        contract = (FRAMEWORK / "policies" / "state-contract.md").read_text(
            encoding="utf-8"
        )
        guard = FRAMEWORK / "tools" / "state_guard.py"

        self.assertTrue(guard.is_file())
        for text in (adapter, conductor, coordination):
            self.assertIn("state-contract.md", text)
            self.assertIn("state_guard.py check", text)
            self.assertIn("校验通过", text)
            self.assertIn("不得继续 Dispatch", text)
        self.assertIn("agent.instance", contract)
        self.assertNotIn("activity", contract)
        self.assertIn("Workflow frontmatter", contract)
        self.assertIn("Agent Contract", contract)
        self.assertIn("文件名 stem", contract)
        self.assertIn("当前 Workflow", contract)

    def test_state_check_does_not_execute_python_from_arbitrary_project(self):
        installer = (ROOT / "bin" / "yuanforge-init").read_text(encoding="utf-8")
        insight_validation = (
            ROOT / "insight" / "yuan_insight" / "state_validation.py"
        ).read_text(encoding="utf-8")

        self.assertIn('SOURCE_FRAMEWORK / "tools" / "state_guard.py"', installer)
        self.assertIn("source_guard", insight_validation)
        self.assertIn("installed_yuan_root", insight_validation)
        self.assertIn("return None", insight_validation)

    def test_content_driven_interface_design_contract(self):
        skill_root = FRAMEWORK / "skills" / "content-driven-interface-design"
        skill = skill_root / "SKILL.md"
        reference = skill_root / "references" / "presentation-architecture.md"
        metadata = skill_root / "agents" / "openai.yaml"
        self.assertTrue(skill.is_file())
        self.assertTrue(reference.is_file())
        self.assertTrue(metadata.is_file())

        skill_text = skill.read_text(encoding="utf-8")
        reference_text = reference.read_text(encoding="utf-8")
        metadata_text = metadata.read_text(encoding="utf-8")
        for phrase in (
            "System Story",
            "Content Model",
            "View Model",
            "Visual Language",
            "Liveness",
            "Verification",
        ):
            self.assertIn(phrase, skill_text)
        self.assertEqual(1, skill_text.count("唯一 Product Truth Source"))
        self.assertIn(
            "canonical Product Contract / Acceptance / Repository Fact",
            skill_text,
        )
        self.assertIn(
            "不得创建、推断、重命名或铸造 canonical locator 或 fact ID。",
            skill_text,
        )
        self.assertIn("source: current user request", skill_text)
        self.assertIn("canonical ID unavailable", skill_text)
        self.assertIn("继续临时设计", skill_text)
        self.assertIn("provisional Presentation Contract", skill_text)
        self.assertIn("不能被冻结", skill_text)
        self.assertIn(
            "在 Yuan 场景中，将 identity gap 返回 Conductor", skill_text
        )
        self.assertIn(
            "在独立 Skill 场景中，在结果中披露 identity gap", skill_text
        )
        self.assertIn("derived decision anchor", skill_text)
        self.assertIn(
            "必须标明 derived；它永远不是 canonical", skill_text
        )
        self.assertIn(
            "不得把 prompt 改写成第二份 Product Truth Source", skill_text
        )
        self.assertIn(
            "只有真实 canonical source 与稳定 canonical locator、fact ID 才允许冻结。",
            skill_text,
        )
        self.assertNotIn(
            "infer a canonical locator when one is missing", skill_text
        )
        self.assertNotIn(
            "mint a canonical fact ID when one is missing", skill_text
        )
        self.assertNotIn("- Product facts and System Story.", skill_text)
        for required_story_field in (
            "user and context",
            "task and intended outcome",
            "key object old → new change",
            "why the user must perceive the change",
            "consequence if they do not",
            "truth source",
        ):
            self.assertIn(required_story_field, skill_text)
        for required_content_field in (
            "content and entity types",
            "volume",
            "relationships",
            "priority and co-visibility",
            "states and transitions",
            "change frequency and freshness",
            "key actions",
            "device",
            "context continuity",
        ):
            self.assertIn(required_content_field, skill_text)
        for decision_requirement in (
            "Primary View Model",
            "Secondary View Model",
            "rejected candidate",
            "Traceability Matrix",
            "Upstream fact reference",
        ):
            self.assertIn(decision_requirement, skill_text)
        for downstream_decision in (
            "Visual Language：引用决定",
            "Liveness：为每个",
            "Verification：引用上游 fact ID",
        ):
            self.assertIn(downstream_decision, skill_text)
        self.assertIn("presentation-architecture.md", skill_text)
        self.assertNotIn("Dashboard", skill_text)
        self.assertNotIn("Liveness Score", skill_text)
        self.assertIn('default_prompt: "使用 $content-driven-interface-design', metadata_text)

        for view_model in (
            "Queue",
            "Timeline",
            "Map",
            "Tree",
            "Table",
            "Board",
            "Calendar",
            "Feed",
            "Comparison",
            "Detail workspace",
        ):
            self.assertIn(view_model, reference_text)
        for phrase in (
            "Detail Strategy",
            "Context Continuity",
            "Anti-convergence",
            "Content Topology",
        ):
            self.assertIn(phrase, reference_text)

        ui_designer = (FRAMEWORK / "agents" / "ui-designer.md").read_text(
            encoding="utf-8"
        )
        reviewer = (FRAMEWORK / "agents" / "ux-reviewer.md").read_text(
            encoding="utf-8"
        )
        frontend = (FRAMEWORK / "agents" / "frontend-dev.md").read_text(
            encoding="utf-8"
        )
        query = (FRAMEWORK / "skills" / "query-ux-pro-max" / "SKILL.md").read_text(
            encoding="utf-8"
        )
        self.assertRegex(
            next(line for line in ui_designer.splitlines() if "Skill Assignment" in line),
            r"Required `framework://skills/content-driven-interface-design/SKILL\.md`.*Conditional `framework://skills/query-ux-pro-max/SKILL\.md`",
        )
        self.assertRegex(
            next(line for line in reviewer.splitlines() if "Skill Assignment" in line),
            r"Required `framework://skills/content-driven-interface-design/SKILL\.md`",
        )
        self.assertIn("Presentation Contract", ui_designer)
        self.assertIn("Presentation Contract", reviewer)
        self.assertIn(
            "不得以审查名义重做设计、替换 View Model 或另起一份视觉规范",
            reviewer,
        )
        self.assertNotIn(
            "不得以审查名义不重做设计、替换 View Model 或另起一份视觉规范",
            reviewer,
        )
        self.assertNotIn("content-driven-interface-design", frontend)
        for phrase in ("Presentation Contract", "稳定身份", "真实事件", "上下文", "reduced-motion"):
            self.assertIn(phrase, frontend)
        self.assertIn("可在 Project Design System 或平台约束要求时使用", ui_designer)
        for agent_name, contract in (
            ("ui-designer", ui_designer),
            ("ux-reviewer", reviewer),
            ("frontend-dev", frontend),
        ):
            self.assertGreaterEqual(
                contract.count("canonical Product Contract + frozen Presentation Contract"),
                2,
                agent_name,
            )
        self.assertIn("通过保存 canonical source locator 与 derived decision 编写 frozen Presentation Contract", ui_designer)
        self.assertIn("对照 canonical source locator 与实现证据审查同一份 frozen Presentation Contract", reviewer)
        self.assertIn("只消费同一份 frozen Presentation Contract", frontend)
        for review_dimension in (
            "Content / View Model Fit",
            "Detail Restraint / Stable-state Fatigue",
            "Liveness Truth Source / Recovery / Reduced-motion",
        ):
            self.assertIn(review_dimension, reviewer)
        self.assertIn(
            "Product Contract / Acceptance / Repository Fact → Presentation Architecture → Visual Absolutes → Project Design System → query",
            query,
        )
        self.assertIn("View Model 之后", query)

        for path in skill_root.rglob("*"):
            if not path.is_file():
                continue
            payload = path.read_bytes()
            self.assertNotIn(b"\r\n", payload, str(path))
            for line_number, line in enumerate(payload.splitlines(), 1):
                self.assertEqual(
                    line.rstrip(b" \t"),
                    line,
                    f"{path}:{line_number} trailing whitespace",
                )


if __name__ == "__main__":
    unittest.main()
