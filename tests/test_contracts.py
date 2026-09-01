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

    def test_content_driven_interface_design_is_artifact_local_and_conditional(self):
        skill_root = FRAMEWORK / "skills" / "content-driven-interface-design"
        skill = (skill_root / "SKILL.md").read_text(encoding="utf-8")
        discovery = (skill_root / "references" / "evidence-driven-frontend-discovery.md").read_text(encoding="utf-8")
        architecture = (skill_root / "references" / "presentation-architecture.md").read_text(encoding="utf-8")
        metadata = (skill_root / "agents" / "openai.yaml").read_text(encoding="utf-8")

        for phrase in ("System Story", "Repository Capability Audit", "Content Model", "View Model", "Visual Language", "Liveness", "Verification", "Traceability Matrix", "provisional Presentation Contract", "不能被冻结", "不得创建、推断、重命名或铸造 canonical locator 或 fact ID。"):
            self.assertIn(phrase, skill)
        self.assertIn("状态是该设计 Artifact 的局部质量字段", skill)
        self.assertIn("Independent review verdict 是独立 Review Evidence，不是 Artifact freeze 的必要条件。", skill)
        self.assertIn("NEEDS_WORK 时 Contract 返回 UI Designer 修订并产生新的 frozen revision。", skill)
        self.assertNotIn("Observable acceptance、Non-goal 与 independent review verdict。", skill)
        self.assertIn("`project://docs/design/`", skill)
        self.assertIn("关键旅程", skill)
        self.assertIn("没有可复用设计", skill)
        self.assertIn("Data Capability Matrix", discovery)
        self.assertIn("page responsibility", discovery)
        self.assertIn("System Capability Evidence", discovery)
        for model in ("Queue", "Timeline", "Table", "Board", "Detail workspace"):
            self.assertIn(model, architecture)
        self.assertIn("$content-driven-interface-design", metadata)

        product = (FRAMEWORK / "agents" / "product-analyst.md").read_text(encoding="utf-8")
        designer = (FRAMEWORK / "agents" / "ui-designer.md").read_text(encoding="utf-8")
        reviewer = (FRAMEWORK / "agents" / "ux-reviewer.md").read_text(encoding="utf-8")
        frontend = (FRAMEWORK / "agents" / "frontend-dev.md").read_text(encoding="utf-8")
        routing = (FRAMEWORK / "policies" / "routing.md").read_text(encoding="utf-8")
        query = (FRAMEWORK / "skills" / "query-ux-pro-max" / "SKILL.md").read_text(encoding="utf-8")

        self.assertIn("Presentation Design Signal", product)
        self.assertIn("Repository Capability Audit", product)
        self.assertIn("content-driven-interface-design", designer)
        self.assertIn("`project://docs/design/`", designer)
        self.assertIn("Repository Capability Audit", designer)
        self.assertIn("Presentation Contract Traceability Review", reviewer)
        self.assertIn("Data Capability Matrix", reviewer)
        self.assertIn("不得以审查名义重做设计、替换 View Model 或另起一份视觉规范", reviewer)
        self.assertIn("Presentation Contract 消费边界", frontend)
        self.assertIn("稳定身份", frontend)
        self.assertIn("reduced-motion", frontend)
        self.assertIn("六类定向", frontend)
        self.assertIn("前端工程纪律", frontend)
        self.assertIn("Presentation Design Signal", routing)
        self.assertNotIn("UI Design Gate", routing)
        self.assertIn("Product Contract / Acceptance / Repository Fact → Presentation Architecture → Visual Absolutes → Project Design System → query", query)

        for workflow_name in ("new-feature.md", "large-project.md"):
            workflow = (FRAMEWORK / "workflows" / workflow_name).read_text(encoding="utf-8")
            self.assertIn("Presentation Design Signal", workflow)
            self.assertIn("Repository Capability Audit", workflow)
            self.assertIn("`project://docs/design/`", workflow)
            self.assertNotIn("presentation_contract", workflow)

        for path in (FRAMEWORK / "policies" / "state-contract.md", FRAMEWORK / "tools" / "state_guard.py", FRAMEWORK / "templates" / "project" / "STATUS.md"):
            self.assertNotIn("presentation_contract", path.read_text(encoding="utf-8"))

    def test_presentation_contract_freeze_uses_relocatable_canonical_references(self):
        skill = (FRAMEWORK / "skills" / "content-driven-interface-design" / "SKILL.md").read_text(encoding="utf-8")
        work_template = (FRAMEWORK / "templates" / "project" / "WORK.md").read_text(encoding="utf-8")

        for phrase in (
            "canonical source locator 必须真实存在",
            "stable fact ID 如果上游真实存在则必须复用",
            "明确、可重新定位的 section / item reference",
            "canonical source locator + section / item reference",
            "不得创建、推断、重命名或铸造 canonical locator 或 fact ID。",
            "derived decision anchor",
            "永远不是 canonical",
        ):
            self.assertIn(phrase, skill)
        self.assertNotIn("只有真实 canonical source 与稳定 canonical locator、fact ID 才允许冻结", skill)
        self.assertNotIn("Fact ID", work_template)
        self.assertIn("section / item reference", skill)

    def test_ui_designer_typography_is_project_native_first(self):
        designer = (FRAMEWORK / "agents" / "ui-designer.md").read_text(encoding="utf-8")

        for phrase in (
            "Project-native First",
            "Project Design System",
            "平台规范",
            "优先沿用",
            "Inter / Roboto / Arial 本身不是违规",
        ):
            self.assertIn(phrase, designer)
        self.assertNotIn("不要用 Inter/Roboto/Arial", designer)

    def test_engineering_context_compilation_is_project_native_and_bounded(self):
        skill = (
            FRAMEWORK / "skills" / "engineering-context-compilation" / "SKILL.md"
        ).read_text(encoding="utf-8")

        for phrase in (
            "Engineering Context Compilation",
            "Current Repository implementation/tests/config",
            "Project ARCHITECTURE / DECISIONS",
            "Project MEMORY",
            "Actual dependency/runtime/version facts",
            "Stack-specific Engineering Knowledge",
            "Yuan Universal Engineering Knowledge",
            "implementation_guidance",
            "required_reuse",
            "forbidden",
            "unknowns",
            "运行时 Dispatch Context",
            "不创建新的 Project Truth Source",
            "Project-native facts 必须优先",
            "transaction",
            "concurrency",
            "lifecycle",
        ):
            self.assertIn(phrase, skill)
        self.assertNotIn("一次性加载全部 Reference", skill)

    def test_engineering_context_product_truth_precedes_current_behavior(self):
        skill = (
            FRAMEWORK / "skills" / "engineering-context-compilation" / "SKILL.md"
        ).read_text(encoding="utf-8")

        ordered = (
            "Current confirmed Product Contract / Acceptance / explicit Task constraints",
            "Current Repository implementation/tests/config",
            "Project ARCHITECTURE / DECISIONS",
            "Project MEMORY",
            "Actual dependency/runtime/version facts",
            "Stack-specific Engineering Knowledge",
            "Yuan Universal Engineering Knowledge",
        )
        positions = [skill.index(item) for item in ordered]
        self.assertEqual(positions, sorted(positions))
        for phrase in (
            "desired_changes",
            "current_behavior",
            "不得把被明确改变的旧行为写成 invariant",
            "重复提交",
        ):
            self.assertIn(phrase, skill)

    def test_quality_v0_integrates_writers_and_contract_diff_review(self):
        backend = (FRAMEWORK / "agents" / "backend-dev.md").read_text(encoding="utf-8")
        frontend = (FRAMEWORK / "agents" / "frontend-dev.md").read_text(encoding="utf-8")
        conductor = (FRAMEWORK / "agents" / "conductor.md").read_text(encoding="utf-8")
        auditor = (FRAMEWORK / "agents" / "quality-auditor.md").read_text(encoding="utf-8")
        review_skill = (FRAMEWORK / "skills" / "requesting-code-review.md").read_text(encoding="utf-8")

        for writer in (backend, frontend):
            self.assertIn("engineering-context-compilation/SKILL.md", writer)
            self.assertIn("Engineering Context", writer)
            self.assertIn("Explore", writer)
            self.assertIn("Verification First", writer)
            self.assertIn("Project-native", writer)
            self.assertNotIn("单文件 >300 行", writer)
            self.assertNotIn("交付超 300 行", writer)
            self.assertIn("review_context", writer)
            self.assertIn("engineering_context", writer)
            self.assertIn("只要本 Task 使用 Engineering Context", writer)
            self.assertIn("始终返回", writer)
            self.assertNotIn("若本 Task 需要审查", writer)
        for text in (auditor, review_skill):
            self.assertIn("Contract → Diff Review", text)
            self.assertIn("Engineering Context", text)
            self.assertIn("未经解释的 deviation", text)
        self.assertNotIn("单文件 ≤300 行", auditor)
        self.assertNotIn("routes → controllers → services → repositories", auditor)
        self.assertIn("原样", conductor)
        self.assertIn("review_context", conductor)
        self.assertIn("不得写入 WORK / STATUS / Memory / Project Truth", conductor)
        self.assertIn("transient 接收", conductor)
        self.assertIn("最终 Actual Diff + Acceptance + Risk", conductor)
        self.assertIn("不需要 Reviewer → 立即丢弃", conductor)
        self.assertIn("Review 完成后立即丢弃", conductor)
        self.assertIn("不得重新编译", auditor)
        self.assertIn("实际使用", auditor)
        self.assertIn("review-context-missing protocol defect", auditor)
        self.assertIn("NEEDS_WORK", auditor)
        self.assertIn("legacy / non-Writer / 未使用 Engineering Context", auditor)

        for path in (
            FRAMEWORK / "policies" / "state-contract.md",
            FRAMEWORK / "tools" / "state_guard.py",
            FRAMEWORK / "templates" / "project" / "WORK.md",
            FRAMEWORK / "templates" / "project" / "STATUS.md",
        ):
            self.assertNotIn("review_context", path.read_text(encoding="utf-8"), path.name)
        for path in (ROOT / "docs" / "WORK.md", ROOT / "docs" / "STATUS.md", ROOT / "docs" / "MEMORY.md"):
            self.assertNotRegex(
                path.read_text(encoding="utf-8"), r"(?m)^review_context:\s*$", path.name
            )

    def test_review_selection_and_quality_audit_are_risk_driven(self):
        policy = (FRAMEWORK / "policies" / "review.md").read_text(encoding="utf-8")
        review_skill = (FRAMEWORK / "skills" / "requesting-code-review.md").read_text(encoding="utf-8")
        auditor = (FRAMEWORK / "agents" / "quality-auditor.md").read_text(encoding="utf-8")

        self.assertIn("Risk-driven", review_skill)
        self.assertIn("最小充分", review_skill)
        self.assertIn("极小机械修改", policy)
        self.assertNotIn("所有审查官同时启动", review_skill)
        self.assertNotIn("四个审查官同时启动", review_skill)
        self.assertIn("Task-relevant", auditor)
        self.assertIn("不要求固定五段", auditor)

    def test_quality_v0_benchmark_and_python_stack_reference_are_actionable(self):
        benchmark_root = FRAMEWORK / "benchmarks" / "quality-v0"
        protocol = (benchmark_root / "README.md").read_text(encoding="utf-8")
        scorecard = (benchmark_root / "scorecard.md").read_text(encoding="utf-8")
        stack = (FRAMEWORK / "references" / "stacks" / "python-unittest.md").read_text(
            encoding="utf-8"
        )

        for name in ("feature.md", "bug.md", "refactor.md"):
            self.assertTrue((benchmark_root / "tasks" / name).is_file(), name)
        fixtures = {
            "feature.md": "feature-config",
            "bug.md": "bug-cleanup",
            "refactor.md": "refactor-parser",
        }
        for task_name, fixture_name in fixtures.items():
            task = (benchmark_root / "tasks" / task_name).read_text(encoding="utf-8")
            fixture = benchmark_root / "fixtures" / fixture_name
            self.assertIn(fixture_name, task)
            self.assertTrue((fixture / "README.md").is_file(), fixture_name)
            self.assertTrue((fixture / "tests").is_dir(), fixture_name)
        for phrase in ("Bare Agent", "Current Yuan", "Quality Yuan", "同一个模型", "同一个任务", "实际 patch", "测试输出", "不得伪称"):
            self.assertIn(phrase, protocol)
        for phrase in (
            "5a42bbfafdddc7e0c81c8f74d4a88bd10f0fa543",
            "quality-v0.1.1",
            "immutable",
            "model-comparison-pending",
            "复杂多文件边界、生命周期、事务、状态或集成",
        ):
            self.assertIn(phrase, protocol)
        for dimension in (
            "Correctness",
            "Architecture Fit",
            "Code Quality",
            "Stack Correctness",
            "Robustness",
            "Overengineering Control",
        ):
            self.assertIn(dimension, scorecard)
        for phrase in ("目标 Repository", "generic", "version-specific", "unknowns", "unittest", "生命周期", "异常", "Version Anchor"):
            self.assertIn(phrase, stack)
        self.assertNotIn("Yuan 本仓库的 Evidence", stack)

    def test_quality_v0_shared_tasks_do_not_leak_engineering_answers(self):
        task_root = FRAMEWORK / "benchmarks" / "quality-v0" / "tasks"
        feature = (task_root / "feature.md").read_text(encoding="utf-8")
        bug = (task_root / "bug.md").read_text(encoding="utf-8")
        refactor = (task_root / "refactor.md").read_text(encoding="utf-8")

        for forbidden in ("ConfigError", "singleton", "重写配置格式", "既有错误 / 默认机制"):
            self.assertNotIn(forbidden, feature)
        for forbidden in ("TemporaryDirectory", "pathlib.Path"):
            self.assertNotIn(forbidden, bug)
        for forbidden in (
            "认知复杂度",
            "repository / service",
            "文件长度阈值",
            "frontmatter 解析",
            "state normalization",
            "rendering helper",
        ):
            self.assertNotIn(forbidden, refactor)

    def test_installer_records_framework_fingerprint(self):
        installer = load_installer()
        fingerprint = installer.framework_fingerprint(FRAMEWORK)
        self.assertRegex(fingerprint, r"^[0-9a-f]{64}$")
        self.assertEqual(fingerprint, installer.framework_fingerprint(FRAMEWORK))
        self.assertEqual("4.0.0-alpha.13", (FRAMEWORK / "VERSION").read_text(encoding="utf-8").strip())
        self.assertIn("version: 4.0.0-alpha.13", (ROOT / "SKILL.md").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
