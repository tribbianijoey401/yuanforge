from __future__ import annotations

import copy
import json
import math
import os
import sys
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import yuan.runtime as runtime_module
from yuan.artifacts import build_manifest, diff_manifests
from yuan.adapters import validate_adapter_descriptor
from yuan.canonical import canonical_bytes, digest, digest_bytes
from yuan.capabilities import (
    available_profiles,
    capability_manifest,
    installed_catalog,
    resolve_capabilities,
    route_capabilities,
    routing_plan,
)
from yuan.cli import attempt_template, init_repository, parser as cli_parser, work_template
from yuan.errors import IntegrityError, ValidationError
from yuan.identity import harness_digest
from yuan.ledger import Ledger, atomic_write, exclusive_lock
from yuan.memory import (
    checkpoint_memory,
    memory_context,
    memory_resume,
    memory_status,
    memory_template,
    rebuild_memory,
    record_memory,
)
from yuan.ports import ExecutableBinding, ReferencePort
from yuan.project import (
    BOOTSTRAP_END,
    BOOTSTRAP_START,
    agent_guidance,
    install_project,
    project_status,
    update_project,
)
from yuan.release import build_runtime_zipapp, build_zipapp, verify_release
from yuan.reducer import reduce_projection
from yuan.runtime import (
    accept_work,
    active_ledger,
    add_evidence,
    begin_attempt,
    dispatch_attempt,
    handoff_template,
    load_config,
    observe_attempt,
    list_runs,
    predecessor_binding,
    replay,
    rebuild,
    record_reduction,
    record_handoff,
    mark_attempt_unknown,
    resolve_attempt,
    run_verifier,
    start_successor,
    state_root,
    supersede_work,
    verify_work_verifiers,
)
from yuan.validate import validate_evidence, validate_work, with_digest
from yuan.workflow import confirm_intake, confirm_work, intake_decision, intake_template


ZERO = "0" * 64


def confirmed_intake(request: str, *, risk: str = "R2", signals: list[str] | None = None) -> dict:
    value = intake_template(request)
    value["risk"] = {"level": risk, "rationale": f"测试固定为 {risk}。"}
    value["signals"] = list(signals or [])
    value = with_digest(value)
    return confirm_intake(value, "测试用户确认需求、答案、假设与风险")


def core_routing(*, risk: str = "R2", signals: list[str] | None = None) -> dict:
    return with_digest({
        "schema_version": "yuan.routing/v1",
        "profile_id": "core",
        "profile_digest": digest({"profile": "core"}),
        "risk": risk,
        "signals": list(signals or []),
        "agents": [],
        "skills": [],
        "handoff_agents": [],
        "artifact_review_agents": [],
    })


def release_context_for_digest(artifact_digest: str) -> dict:
    report = {
        "schema_version": "yuan.conformance-report/v1",
        "status": "PASS",
        "harness_digest": harness_digest(),
        "checks": {
            "unit_tests": {"status": "PASS"},
            "schemas": {"status": "PASS"},
            "adapter": {"status": "PASS"},
            "bootstrap": {"status": "PASS"},
            "capability_profile": {"status": "PASS"},
            "automation": {"status": "PASS"},
            "size_budget": {"status": "PASS"},
            "reproducible_release": {"status": "PASS", "artifact_digest": artifact_digest},
        },
    }
    source = with_digest({
        "schema_version": "yuan.release-source/v1",
        "kind": "test",
        "revision": "TEST",
        "dirty": False,
    })
    return {"report": report, "source": source}


def current_release_context() -> dict:
    with tempfile.TemporaryDirectory() as temporary:
        artifact = build_runtime_zipapp(Path(temporary) / "yuan.pyz")
    return release_context_for_digest(artifact["digest"])


def altered_candidate(marker: bytes) -> tuple[dict, object]:
    with tempfile.TemporaryDirectory() as temporary:
        path = Path(temporary) / "yuan.pyz"
        base = build_runtime_zipapp(path)
        payload = path.read_bytes() + marker
    artifact = copy.deepcopy(base)
    artifact.update(path="yuan.pyz", digest=digest_bytes(payload), bytes=len(payload))
    artifact["manifest"]["artifact"] = {"path": "yuan.pyz", "digest": artifact["digest"], "bytes": len(payload)}
    artifact["manifest"]["digest"] = digest(artifact["manifest"], ("digest",))

    def build(output: Path) -> dict:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(payload)
        value = copy.deepcopy(artifact)
        value["path"] = output.name
        value["manifest"]["digest"] = digest(value["manifest"], ("digest",))
        return value

    return release_context_for_digest(artifact["digest"]), build


class RuntimeCase(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        (self.root / "src").mkdir()
        (self.root / "tests").mkdir()
        (self.root / "src" / "app.py").write_text("VALUE = 1\n", encoding="utf-8")
        (self.root / "tests" / "verify_value.py").write_text(
            "import json, pathlib, sys\n"
            "text = (pathlib.Path(sys.argv[1]) / 'src' / 'app.py').read_text()\n"
            "passed = 'VALUE = 2' in text\n"
            "print(json.dumps({'status': 'PASS' if passed else 'FAIL', 'assertions': [{'id': 'value-is-two', 'passed': passed}]}))\n"
            "raise SystemExit(0 if passed else 1)\n",
            encoding="utf-8",
        )
        (self.root / "README.md").write_text("demo\n", encoding="utf-8")
        init_repository(self.root, "AUDITED", "RUN-TEST")
        self.config = load_config(self.root)
        self.work = self.make_work()
        accept_work(self.root, self.work)

    def tearDown(self) -> None:
        self.temp.cleanup()

    def make_work(self, *, grants: list[dict] | None = None, budgets: dict | None = None) -> dict:
        verifier_files = [{
            "path": "tests/verify_value.py",
            "digest": digest_bytes((self.root / "tests" / "verify_value.py").read_bytes()),
        }]
        work = {
            "schema_version": "yuan.work/v2",
            "work_id": "WORK-TEST",
            "revision": 1,
            "goal": "修改 VALUE 并证明结果。",
            "profile": "AUDITED",
            "protocol": self.config["protocol"],
            "harness": self.config["harness"],
            "intake": confirmed_intake("修改 VALUE 并证明结果。"),
            "routing": core_routing(),
            "confirmation": None,
            "artifact": {
                "root": ".",
                "include": ["**"],
                "exclude": [".git/**", ".yuan/**", ".yuan-run/**", "__pycache__/**", "*.pyc"],
                "environment": self.config["environment"],
            },
            "acceptance_criteria": [{
                "id": "AC-VALUE",
                "description": "VALUE 等于二。",
                "required": True,
                "verifier": {
                    "id": "test.value",
                    "revision": "1",
                    "digest": digest({"kind": "python-script", "entrypoint": "tests/verify_value.py", "files": verifier_files}),
                    "kind": "python-script",
                    "entrypoint": "tests/verify_value.py",
                    "timeout_seconds": 10,
                    "files": verifier_files,
                },
                "min_assertions": 1,
                "independence": "independent",
            }],
            "safety_invariants": [{"id": "SAFE-VALUE", "description": "Value Verifier 通过。", "criterion_id": "AC-VALUE"}],
            "grants": grants if grants is not None else [{
                "id": "GRANT-SRC",
                "action_types": ["file-write"],
                "side_effect_classes": ["filesystem"],
                "scopes": ["src"],
            }],
            "budgets": budgets or {"ticks": 20, "attempts": 10, "tool_calls": 20, "command_seconds": 100},
            "predecessor": None,
            "created_at": "2026-08-02T00:00:00Z",
        }
        return confirm_work(work, "测试用户确认完整 Work Contract")

    def proposal(self, *, attempt_id: str = "ATT-001", path: str = "src") -> dict:
        return {
            "attempt_id": attempt_id,
            "strategy": "修改 VALUE",
            "hypothesis": {"claim": "修改 VALUE 可以满足 AC。", "falsification": "Verifier 观察到其他值。"},
            "relevant_inputs": [{"path": "src/app.py", "digest": digest_bytes((self.root / "src" / "app.py").read_bytes())}],
            "action": {
                "type": "file-write",
                "mutating": True,
                "side_effect_class": "filesystem",
                "paths": [path],
                "grant_id": "GRANT-SRC",
                "high_impact": False,
            },
            "budget_charge": {"ticks": 1, "attempts": 1, "tool_calls": 1, "command_seconds": 1},
        }

    def reconciliation_proposal(self, target: str = "ATT-001") -> dict:
        return {
            "attempt_id": "REC-001",
            "strategy": "独立检查 UNKNOWN 后的当前 Artifact",
            "hypothesis": {"claim": "当前 Artifact 可以解析原 Attempt。", "falsification": "Probe 无法证明明确终态。"},
            "relevant_inputs": [{"path": "src/app.py", "digest": digest_bytes((self.root / "src" / "app.py").read_bytes())}],
            "action": {
                "type": "reconcile",
                "mutating": False,
                "side_effect_class": "none",
                "paths": ["src"],
                "grant_id": None,
                "high_impact": False,
            },
            "reconciliation": {"target_attempt_id": target},
            "budget_charge": {"ticks": 1, "attempts": 1, "tool_calls": 1, "command_seconds": 1},
        }

    def commit_change(self) -> None:
        begin_attempt(self.root, self.proposal())
        dispatch_attempt(self.root, "ATT-001")
        (self.root / "src" / "app.py").write_text("VALUE = 2\n", encoding="utf-8")
        result = observe_attempt(self.root, "ATT-001", {"kind": "agent-platform", "status": "OK"})
        self.assertEqual(result["decision"]["result"], "CONTINUE")

    def start_routed_successor(self) -> dict:
        supersede_work(self.root, reason="用户改变了验收范围", request="修改 VALUE 并完成独立测试交接。")
        _, ledger = active_ledger(self.root)
        projection = rebuild(self.root, write=False)
        successor = copy.deepcopy(self.work)
        successor["revision"] = 2
        successor["goal"] = "修改 VALUE 并完成独立测试交接。"
        successor["intake"] = confirmed_intake(successor["goal"])
        successor["routing"] = with_digest({
            "schema_version": "yuan.routing/v1",
            "profile_id": "core",
            "profile_digest": digest({"profile": "core"}),
            "risk": "R2",
            "signals": [],
            "agents": ["backend-developer", "tester"],
            "skills": [],
            "handoff_agents": ["backend-developer", "tester"],
            "artifact_review_agents": ["backend-developer", "tester"],
        })
        successor["predecessor"] = predecessor_binding(ledger, projection)
        successor = confirm_work(successor, "用户确认变更后的完整 Work Contract")
        start_successor(self.root, successor, "RUN-TEST-R2")
        self.work = successor
        return successor

    def evidence(self, status: str = "PASS") -> dict:
        artifact = build_manifest(
            self.root,
            include=self.work["artifact"]["include"],
            exclude=self.work["artifact"]["exclude"],
        )
        return with_digest({
            "schema_version": "yuan.evidence/v1",
            "evidence_id": "EVD-001",
            "work": {"id": self.work["work_id"], "revision": self.work["revision"], "digest": self.work["digest"]},
            "attempt_id": "ATT-001",
            "criterion_id": "AC-VALUE",
            "artifact": {"scope": ".", "digest": artifact["digest"]},
            "environment": self.work["artifact"]["environment"],
            "harness": self.work["harness"],
            "verifier": self.work["acceptance_criteria"][0]["verifier"],
            "status": status,
            "assertions": [{"id": "value-is-two", "passed": status == "PASS"}],
            "receipt": {"tool": "2" * 64, "stdout": "3" * 64, "stderr": "4" * 64},
            "independence": "independent",
            "created_at": "2026-08-02T00:01:00Z",
        })

    def test_happy_path_completes_and_rebuild_is_equivalent(self) -> None:
        self.commit_change()
        result = run_verifier(self.root, "AC-VALUE", "ATT-001")
        self.assertEqual(result["decision"]["result"], "COMPLETE")
        first = rebuild(self.root)
        (self.root / ".yuan-run" / "runs" / "RUN-TEST" / "run-memory.json").unlink()
        second = rebuild(self.root)
        self.assertEqual(first["digest"], second["digest"])

    def test_failed_evidence_is_trusted_refutation_not_completion(self) -> None:
        self.commit_change()
        result = add_evidence(self.root, self.evidence("FAIL"))
        self.assertEqual(result["decision"]["result"], "CORRECT")

    def test_unauthorized_action_waits_for_authority(self) -> None:
        proposal = self.proposal(path="README.md")
        result = begin_attempt(self.root, proposal)
        self.assertEqual(result["decision"]["result"], "WAIT_AUTH")

    def test_oversized_charge_produces_budget_exit_without_attempt(self) -> None:
        proposal = self.proposal()
        proposal["budget_charge"]["tool_calls"] = 21
        result = begin_attempt(self.root, proposal)
        self.assertEqual(result["decision"]["result"], "BUDGET_EXIT")
        self.assertEqual(result["event"]["type"], "BUDGET_EXHAUSTED")
        self.assertEqual(rebuild(self.root)["attempt_order"], [])

    def test_replay_rejects_prepared_attempt_over_budget(self) -> None:
        _, ledger = active_ledger(self.root)
        projection = rebuild(self.root, write=False)
        manifest = runtime_module.artifact_for(self.root, self.work)
        proposal = self.proposal()
        proposal["budget_charge"]["tool_calls"] = self.work["budgets"]["tool_calls"] + 1
        blob = ledger.put_blob(canonical_bytes(manifest))
        ledger.append(
            "ATTEMPT_PREPARED",
            {
                "attempt_id": proposal["attempt_id"],
                "sequence": 1,
                "work_digest": self.work["digest"],
                "strategy_fingerprint": digest({"strategy": proposal["strategy"], "inputs": proposal["relevant_inputs"]}),
                "artifact_before": manifest["digest"],
                "manifest_before_blob": blob,
                "proposal": proposal,
            },
            expected_head=projection["source_head"],
        )
        invalid = rebuild(self.root)
        self.assertEqual(invalid["decision"]["result"], "BLOCKED")
        self.assertIn("Attempt Budget Charge 超出 Work Maximum", " ".join(invalid["errors"]))

    def test_attempt_transitions_scan_artifact_once_each(self) -> None:
        original = runtime_module.artifact_for
        with mock.patch.object(runtime_module, "artifact_for", wraps=original) as scan:
            begin_attempt(self.root, self.proposal())
            self.assertEqual(scan.call_count, 1)
        with mock.patch.object(runtime_module, "artifact_for", wraps=original) as scan:
            dispatch_attempt(self.root, "ATT-001")
            self.assertEqual(scan.call_count, 1)
        (self.root / "src" / "app.py").write_text("VALUE = 2\n", encoding="utf-8")
        with mock.patch.object(runtime_module, "artifact_for", wraps=original) as scan:
            observe_attempt(self.root, "ATT-001", {"kind": "agent-platform", "status": "OK"})
            self.assertEqual(scan.call_count, 1)

    def test_relevant_input_must_match_current_bytes(self) -> None:
        proposal = self.proposal()
        proposal["relevant_inputs"][0]["digest"] = "9" * 64
        with self.assertRaises(ValidationError):
            begin_attempt(self.root, proposal)

    def test_attempt_template_binds_current_input_digest(self) -> None:
        proposal = attempt_template(
            self.root,
            attempt_id="ATT-TEMPLATE",
            strategy="修改当前值",
            claim="修改后满足 AC",
            falsification="Verifier 仍失败",
            inputs=["src/app.py"],
            action_type="file-write",
            paths=["src"],
            side_effect_class="filesystem",
            grant_id="GRANT-SRC",
            read_only=False,
            high_impact=False,
            tool_calls=1,
            command_seconds=1,
        )
        self.assertEqual(proposal["relevant_inputs"][0]["digest"], digest_bytes((self.root / "src" / "app.py").read_bytes()))

    def test_attempt_template_cli_accepts_reconciliation_action(self) -> None:
        args = cli_parser().parse_args([
            "--root", str(self.root), "attempt", "template",
            "--attempt-id", "ATT-RECONCILE-TEMPLATE",
            "--strategy", "只读探测", "--claim", "状态可确定", "--falsification", "状态仍不明确",
            "--action-type", "reconcile", "--side-effect-class", "none", "--read-only",
        ])
        self.assertEqual(args.action_type, "reconcile")

    def test_undeclared_mutation_becomes_unknown_and_blocked(self) -> None:
        begin_attempt(self.root, self.proposal())
        dispatch_attempt(self.root, "ATT-001")
        (self.root / "src" / "app.py").write_text("VALUE = 2\n", encoding="utf-8")
        (self.root / "README.md").write_text("corrupted\n", encoding="utf-8")
        result = observe_attempt(self.root, "ATT-001", {"status": "OK"})
        self.assertEqual(result["decision"]["result"], "BLOCKED")
        self.assertEqual(result["event"]["type"], "ATTEMPT_UNKNOWN")

    def test_unknown_can_be_reconciled_as_committed_with_independent_evidence(self) -> None:
        begin_attempt(self.root, self.proposal())
        dispatch_attempt(self.root, "ATT-001")
        (self.root / "src" / "app.py").write_text("VALUE = 2\n", encoding="utf-8")
        self.assertEqual(mark_attempt_unknown(self.root, "ATT-001", "模拟 Receipt 丢失")["decision"]["result"], "BLOCKED")
        begin_attempt(self.root, self.reconciliation_proposal())
        verified = run_verifier(self.root, "AC-VALUE", "REC-001")
        evidence_id = verified["event"]["payload"]["evidence_id"]
        resolved = resolve_attempt(self.root, "ATT-001", "REC-001", "COMMITTED", evidence_id)
        self.assertEqual(resolved["decision"]["result"], "COMPLETE")
        self.assertEqual(rebuild(self.root)["attempts"]["ATT-001"]["outcome"], "COMMITTED")

    def test_unknown_can_be_reconciled_as_no_effect_by_manifest_equality(self) -> None:
        begin_attempt(self.root, self.proposal())
        dispatch_attempt(self.root, "ATT-001")
        mark_attempt_unknown(self.root, "ATT-001", "模拟 Dispatch 后崩溃但未写入")
        begin_attempt(self.root, self.reconciliation_proposal())
        resolved = resolve_attempt(self.root, "ATT-001", "REC-001", "NO_EFFECT")
        self.assertEqual(resolved["decision"]["result"], "CONTINUE")
        self.assertEqual(rebuild(self.root)["attempts"]["ATT-001"]["outcome"], "NO_EFFECT")

    def test_observed_crash_can_be_marked_unknown_and_reconciled(self) -> None:
        begin_attempt(self.root, self.proposal())
        dispatch_attempt(self.root, "ATT-001")
        (self.root / "src" / "app.py").write_text("VALUE = 2\n", encoding="utf-8")
        _, ledger = active_ledger(self.root)
        projection = rebuild(self.root, write=False)
        before = json.loads(ledger.get_blob(projection["attempts"]["ATT-001"]["manifest_before_blob"]))
        after = build_manifest(
            self.root,
            include=self.work["artifact"]["include"],
            exclude=self.work["artifact"]["exclude"],
        )
        receipt = {"status": "OK"}
        ledger.append("ATTEMPT_OBSERVED", {
            "attempt_id": "ATT-001",
            "artifact_after": after["digest"],
            "manifest_after_blob": ledger.put_blob(canonical_bytes(after)),
            "diff": diff_manifests(before, after),
            "receipt_blob": ledger.put_blob(canonical_bytes(receipt)),
            "receipt_digest": digest(receipt),
        })
        result = mark_attempt_unknown(self.root, "ATT-001", "模拟 Observation 后、Commit 前崩溃")
        self.assertEqual(result["decision"]["result"], "BLOCKED")
        begin_attempt(self.root, self.reconciliation_proposal())
        verified = run_verifier(self.root, "AC-VALUE", "REC-001")
        resolved = resolve_attempt(
            self.root,
            "ATT-001",
            "REC-001",
            "COMMITTED",
            verified["event"]["payload"]["evidence_id"],
        )
        self.assertEqual(resolved["decision"]["result"], "COMPLETE")

    def test_unresolved_reconciliation_remains_blocked(self) -> None:
        begin_attempt(self.root, self.proposal())
        dispatch_attempt(self.root, "ATT-001")
        mark_attempt_unknown(self.root, "ATT-001", "模拟不明确的副作用")
        result = begin_attempt(self.root, self.reconciliation_proposal())
        self.assertEqual(result["decision"]["result"], "BLOCKED")
        self.assertEqual(rebuild(self.root)["attempts"]["ATT-001"]["state"], "UNKNOWN")

    def test_unknown_run_cannot_escape_through_generic_successor(self) -> None:
        begin_attempt(self.root, self.proposal())
        dispatch_attempt(self.root, "ATT-001")
        mark_attempt_unknown(self.root, "ATT-001", "模拟未解析副作用")
        _, ledger = active_ledger(self.root)
        projection = rebuild(self.root, write=False)
        successor = copy.deepcopy(self.work)
        successor["revision"] = 2
        successor["predecessor"] = predecessor_binding(ledger, projection)
        successor = confirm_work(successor, "用户确认候选继任契约")
        with self.assertRaisesRegex(ValidationError, "WORK_SUPERSEDED"):
            start_successor(self.root, successor, "RUN-UNKNOWN-ESCAPE")

    def test_reconciliation_refuses_changes_outside_original_scope(self) -> None:
        begin_attempt(self.root, self.proposal())
        dispatch_attempt(self.root, "ATT-001")
        (self.root / "src" / "app.py").write_text("VALUE = 2\n", encoding="utf-8")
        (self.root / "README.md").write_text("越权修改\n", encoding="utf-8")
        mark_attempt_unknown(self.root, "ATT-001", "模拟未知副作用")
        begin_attempt(self.root, self.reconciliation_proposal())
        verified = run_verifier(self.root, "AC-VALUE", "REC-001")
        evidence_id = verified["event"]["payload"]["evidence_id"]
        with self.assertRaises(ValidationError):
            resolve_attempt(self.root, "ATT-001", "REC-001", "COMMITTED", evidence_id)
        self.assertEqual(rebuild(self.root)["attempts"]["ATT-001"]["state"], "UNKNOWN")

    def test_out_of_band_change_is_detected_after_commit(self) -> None:
        self.commit_change()
        (self.root / "README.md").write_text("outside attempt\n", encoding="utf-8")
        projection = rebuild(self.root)
        self.assertEqual(projection["decision"]["result"], "BLOCKED")
        self.assertIn("检测到 Attempt 之外的 Artifact 修改", projection["errors"])

    def test_tampered_ledger_fails_closed(self) -> None:
        _, ledger = active_ledger(self.root)
        first = sorted(ledger.events_root.glob("*.json"))[0]
        value = json.loads(first.read_text(encoding="utf-8"))
        value["payload"]["goal"] = "tampered"
        first.write_text(json.dumps(value), encoding="utf-8")
        with self.assertRaises(IntegrityError):
            ledger.events()

    def test_stale_or_fake_evidence_is_rejected(self) -> None:
        self.commit_change()
        evidence = self.evidence()
        evidence["verifier"] = {"id": "fake", "revision": "1", "digest": "9" * 64}
        evidence = with_digest(evidence)
        with self.assertRaises(ValidationError):
            add_evidence(self.root, evidence)

    def test_verifier_is_hash_bound(self) -> None:
        self.commit_change()
        (self.root / "tests" / "verify_value.py").write_text("print('fake')\n", encoding="utf-8")
        with self.assertRaises(IntegrityError):
            run_verifier(self.root, "AC-VALUE", "ATT-001")

    def test_verifier_timeout_fails_closed(self) -> None:
        self.commit_change()
        with mock.patch("yuan.runtime.subprocess.run", side_effect=subprocess.TimeoutExpired(["python"], 10)):
            with self.assertRaisesRegex(IntegrityError, "Verifier 执行超时"):
                run_verifier(self.root, "AC-VALUE", "ATT-001")

    def test_work_rejects_unbound_verifier_closure(self) -> None:
        work = copy.deepcopy(self.work)
        work["acceptance_criteria"][0]["verifier"]["files"][0]["digest"] = "9" * 64
        with self.assertRaises(ValidationError):
            verify_work_verifiers(self.root, work)

    def test_ledger_head_can_recover_after_interrupted_advance(self) -> None:
        _, ledger = active_ledger(self.root)
        events = ledger.events()
        stale = {"sequence": 1, "event_digest": events[0]["digest"]}
        atomic_write(ledger.head_path, canonical_bytes(stale))
        with self.assertRaises(IntegrityError):
            ledger.events()
        receipt = ledger.recover_head()
        self.assertEqual(receipt["status"], "RECOVERED")
        self.assertEqual(len(ledger.events()), 2)

    def test_ledger_transition_compare_and_swap_rejects_stale_head(self) -> None:
        _, ledger = active_ledger(self.root)
        projection = rebuild(self.root, write=False)
        event = ledger.append(
            "RESULT_REDUCED",
            {"result": projection["decision"]["result"], "projection_digest": projection["digest"]},
            expected_head=projection["source_head"],
        )
        self.assertEqual(event["previous"], projection["source_head"])
        with self.assertRaisesRegex(IntegrityError, "Ledger Head CAS 失败"):
            ledger.append(
                "RESULT_REDUCED",
                {"result": "CONTINUE", "projection_digest": projection["digest"]},
                expected_head=projection["source_head"],
            )

    def test_replay_blocks_incomplete_work_acceptance_transition(self) -> None:
        config = load_config(self.root)
        incomplete = Ledger(state_root(self.root, config), "RUN-INCOMPLETE-WORK")
        incomplete.append("WORK_ACCEPTED", self.work, expected_head=None)
        projection = replay(incomplete)
        self.assertEqual(projection["decision"]["result"], "BLOCKED")
        self.assertIn("Work 缺少 ARTIFACT_BASELINED Event", projection["errors"])

    def test_selected_protocol_is_verified_on_every_command(self) -> None:
        (self.root / ".yuan" / "protocol.md").write_text("tampered\n", encoding="utf-8")
        with self.assertRaises(IntegrityError):
            rebuild(self.root)

    def test_selected_protocol_revision_is_verified(self) -> None:
        config_path = self.root / ".yuan" / "config.json"
        config = json.loads(config_path.read_text(encoding="utf-8"))
        config["protocol"]["revision"] = "0.2"
        atomic_write(config_path, canonical_bytes(with_digest(config)))
        with self.assertRaisesRegex(IntegrityError, "Protocol revision"):
            load_config(self.root)

    def test_wait_auth_can_continue_in_bound_successor_work_revision(self) -> None:
        proposal = self.proposal(path="README.md")
        self.assertEqual(begin_attempt(self.root, proposal)["decision"]["result"], "WAIT_AUTH")
        _, ledger = active_ledger(self.root)
        projection = rebuild(self.root, write=False)
        successor = copy.deepcopy(self.work)
        successor["revision"] = 2
        successor["predecessor"] = predecessor_binding(ledger, projection)
        successor["grants"][0]["scopes"].append("README.md")
        successor = confirm_work(successor, "用户确认扩展后的授权范围")
        result = start_successor(self.root, successor, "RUN-TEST-R2")
        self.assertEqual(result["status"], "SUCCESSOR_ACTIVE")
        self.assertEqual(result["projection"]["work"]["revision"], 2)
        runs = list_runs(self.root)
        self.assertEqual(runs["current_run_id"], "RUN-TEST-R2")
        self.assertEqual(len(runs["runs"]), 2)
        retried = self.proposal(attempt_id="ATT-002", path="README.md")
        self.assertEqual(begin_attempt(self.root, retried)["event"]["type"], "ATTEMPT_PREPARED")

    def test_successor_rejects_wrong_predecessor_without_switching_pointer(self) -> None:
        begin_attempt(self.root, self.proposal(path="README.md"))
        _, ledger = active_ledger(self.root)
        projection = rebuild(self.root, write=False)
        successor = copy.deepcopy(self.work)
        successor["revision"] = 2
        successor["predecessor"] = predecessor_binding(ledger, projection)
        successor["predecessor"]["head_digest"] = "9" * 64
        successor = confirm_work(successor, "用户确认错误前任测试契约")
        with self.assertRaises(ValidationError):
            start_successor(self.root, successor, "RUN-BAD-R2")
        self.assertEqual(active_ledger(self.root)[1].run_id, "RUN-TEST")

    def test_nonterminal_run_cannot_be_replaced(self) -> None:
        _, ledger = active_ledger(self.root)
        projection = rebuild(self.root, write=False)
        successor = copy.deepcopy(self.work)
        successor["revision"] = 2
        successor["predecessor"] = predecessor_binding(ledger, projection)
        successor = confirm_work(successor, "用户确认非终态继任测试契约")
        with self.assertRaises(ValidationError):
            start_successor(self.root, successor, "RUN-EARLY-R2")

    def test_work_cannot_start_without_final_user_confirmation(self) -> None:
        unconfirmed = copy.deepcopy(self.work)
        unconfirmed["confirmation"] = None
        unconfirmed = with_digest(unconfirmed)
        with self.assertRaisesRegex(ValidationError, "尚未获得用户最终确认"):
            accept_work(self.root, unconfirmed)

    def test_unresolved_attempt_prevents_mid_work_requirement_change(self) -> None:
        begin_attempt(self.root, self.proposal())
        with self.assertRaisesRegex(ValidationError, "存在未解析 Attempt"):
            supersede_work(self.root, reason="用户改变范围", request="新的需求")

    def test_unresolved_attempt_prevents_role_handoff(self) -> None:
        begin_attempt(self.root, self.proposal())
        with self.assertRaisesRegex(ValidationError, "存在未解析 Attempt"):
            handoff_template(
                self.root,
                handoff_id="HANDOFF-UNSTABLE",
                agent_id="tester",
                to_agent_id="user",
                phase="verification",
                status="READY",
                summary="错误地在未解析 Attempt 上交接。",
                evidence_ids=[],
            )

    def test_mid_work_change_closes_old_work_and_starts_confirmed_successor(self) -> None:
        successor = self.start_routed_successor()
        self.assertEqual(successor["revision"], 2)
        self.assertEqual(rebuild(self.root)["decision"]["result"], "CONTINUE")
        runs = list_runs(self.root)
        self.assertEqual(runs["current_run_id"], "RUN-TEST-R2")
        self.assertEqual(len(runs["runs"]), 2)

    def test_required_role_handoff_gates_completion(self) -> None:
        self.start_routed_successor()
        self.commit_change()
        verified = run_verifier(self.root, "AC-VALUE", "ATT-001")
        self.assertEqual(verified["decision"]["result"], "CONTINUE")
        self.assertIn("tester", " ".join(verified["decision"]["reasons"]))
        evidence_id = verified["event"]["payload"]["evidence_id"]
        with self.assertRaisesRegex(ValidationError, "必须引用当前 Evidence"):
            handoff_template(
                self.root,
                handoff_id="HANDOFF-TESTER-EMPTY",
                agent_id="tester",
                to_agent_id="user",
                phase="verification",
                status="READY",
                summary="没有引用 Evidence 的无效审查。",
                evidence_ids=[],
            )
        tester_handoff = handoff_template(
            self.root,
            handoff_id="HANDOFF-TESTER-001",
            agent_id="tester",
            to_agent_id="user",
            phase="verification",
            status="READY",
            summary="独立验证通过，边界与失败路径均已检查。",
            evidence_ids=[evidence_id],
        )
        with self.assertRaisesRegex(ValidationError, "前序 Agent 尚未 READY"):
            record_handoff(self.root, tester_handoff)
        developer_handoff = handoff_template(
            self.root,
            handoff_id="HANDOFF-BACKEND-001",
            agent_id="backend-developer",
            to_agent_id="tester",
            phase="implementation",
            status="READY",
            summary="实现增量及其验证线索已交给 Tester。",
            evidence_ids=[evidence_id],
        )
        self.assertEqual(record_handoff(self.root, developer_handoff)["decision"]["result"], "CONTINUE")
        recorded = record_handoff(self.root, tester_handoff)
        self.assertEqual(recorded["decision"]["result"], "COMPLETE")

    def test_replay_rejects_out_of_order_role_handoff_event(self) -> None:
        self.start_routed_successor()
        self.commit_change()
        verified = run_verifier(self.root, "AC-VALUE", "ATT-001")
        tester_handoff = handoff_template(
            self.root,
            handoff_id="HANDOFF-OUT-OF-ORDER",
            agent_id="tester",
            to_agent_id="user",
            phase="verification",
            status="READY",
            summary="绕过 Writer Guard 的倒序交接。",
            evidence_ids=[verified["event"]["payload"]["evidence_id"]],
        )
        _, ledger = active_ledger(self.root)
        ledger.append("ROLE_HANDOFF_RECORDED", tester_handoff)
        projection = rebuild(self.root)
        self.assertEqual(projection["decision"]["result"], "BLOCKED")
        self.assertIn("前序 Agent 尚未 READY", " ".join(projection["errors"]))


class PureKernelTests(unittest.TestCase):
    def test_intake_blocks_on_unanswered_question_and_requires_confirmation(self) -> None:
        intake = intake_template("实现一个尚未明确权限边界的功能。")
        intake["questions"] = [{
            "id": "Q-AUTH",
            "question": "哪些角色可以执行此操作？",
            "blocking": True,
            "answer": None,
        }]
        intake = with_digest(intake)
        self.assertEqual(intake_decision(intake)["reason_code"], "NEEDS_INPUT")
        with self.assertRaisesRegex(ValidationError, "未回答的阻塞问题"):
            confirm_intake(intake, "确认")
        intake["questions"][0]["answer"] = "仅管理员。"
        intake = with_digest(intake)
        self.assertEqual(intake_decision(intake)["reason_code"], "NEEDS_CONFIRMATION")
        confirmed = confirm_intake(intake, "用户确认需求、答案、假设和风险")
        self.assertEqual(intake_decision(confirmed)["reason_code"], "INTAKE_CONFIRMED")

    def test_stale_or_negative_role_handoff_cannot_complete(self) -> None:
        projection = self.projection()
        projection["work"]["routing"] = {
            "handoff_agents": ["tester"],
            "artifact_review_agents": ["tester"],
        }
        projection["criterion_evidence"] = {"AC": {"status": "PASS", "current": True}}
        projection["agent_handoffs"] = {
            "tester": {"agent_id": "tester", "status": "READY", "current": False},
        }
        self.assertEqual(reduce_projection(projection)["result"], "CONTINUE")
        projection["agent_handoffs"]["tester"] = {
            "agent_id": "tester", "status": "NEEDS_WORK", "current": True,
        }
        projection["latest_handoff"] = projection["agent_handoffs"]["tester"]
        self.assertEqual(reduce_projection(projection)["result"], "CORRECT")

    def test_six_role_handoff_chain_requires_every_predecessor(self) -> None:
        agents = [f"agent-{index}" for index in range(6)]
        work = {"routing": {"handoff_agents": agents, "artifact_review_agents": agents[2:5]}}
        projection = {"agent_handoffs": {}}
        for agent_id in agents:
            runtime_module._validate_handoff_order(projection, work, {"agent_id": agent_id})
            projection["agent_handoffs"][agent_id] = {"status": "READY", "current": True}
        projection["agent_handoffs"]["agent-3"]["current"] = False
        with self.assertRaisesRegex(ValidationError, "agent-3"):
            runtime_module._validate_handoff_order(projection, work, {"agent_id": "agent-5"})

    def test_canonical_json_is_stable_and_rejects_nan(self) -> None:
        self.assertEqual(canonical_bytes({"b": 2, "a": "元"}), b'{"a":"\xe5\x85\x83","b":2}')
        with self.assertRaises(ValidationError):
            canonical_bytes({"bad": math.nan})

    def test_bundled_profile_is_discoverable_and_catalog_is_complete(self) -> None:
        self.assertIn("vibe-coding", available_profiles())
        manifest = capability_manifest("vibe-coding")
        self.assertEqual(manifest["schema_version"], "yuan.capability-profile/v2")
        self.assertGreaterEqual(len(manifest["required_rules"]), 5)
        self.assertGreaterEqual(len(manifest["agents"]), 13)
        self.assertGreaterEqual(len(manifest["skills"]), 10)
        self.assertIn("project-lifecycle", {item["id"] for item in manifest["skills"]})
        self.assertIn("verifier-authoring", {item["id"] for item in manifest["skills"]})

    def projection(self) -> dict:
        work = {
            "budgets": {"ticks": 5},
            "acceptance_criteria": [{"id": "AC", "required": True}],
            "safety_invariants": [{"criterion_id": "AC"}],
            "routing": {"handoff_agents": [], "artifact_review_agents": []},
        }
        return {
            "work": work,
            "errors": [],
            "attempts": {"ATT": {"state": "COMMITTED"}},
            "authorization_required": None,
            "budgets_used": {"ticks": 1},
            "criterion_evidence": {},
            "latest_evidence": None,
            "legal_next_step": True,
        }

    def test_all_six_reducer_results(self) -> None:
        base = self.projection()
        self.assertEqual(reduce_projection(base)["result"], "CONTINUE")
        value = copy.deepcopy(base)
        value["latest_evidence"] = {"status": "FAIL", "evidence_id": "E"}
        self.assertEqual(reduce_projection(value)["result"], "CORRECT")
        value = copy.deepcopy(base)
        value["criterion_evidence"] = {"AC": {"status": "PASS", "current": True}}
        self.assertEqual(reduce_projection(value)["result"], "COMPLETE")
        value = copy.deepcopy(base)
        value["errors"] = ["broken"]
        self.assertEqual(reduce_projection(value)["result"], "BLOCKED")
        value = copy.deepcopy(base)
        value["authorization_required"] = {"action": "x"}
        self.assertEqual(reduce_projection(value)["result"], "WAIT_AUTH")
        value = copy.deepcopy(base)
        value["budgets_used"]["_exhausted"] = True
        self.assertEqual(reduce_projection(value)["result"], "BUDGET_EXIT")


class PortAndAdapterTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        (self.root / "data").mkdir()
        (self.root / "data" / "a.txt").write_text("甲\n", encoding="utf-8")
        executable = Path(sys.executable).resolve()
        self.port = ReferencePort(
            self.root,
            executables=[ExecutableBinding(
                "python",
                executable,
                digest_bytes(executable.read_bytes()),
                ("-I", "-B", "-c"),
            )],
            proposer=lambda request: {"echo": request},
        )

    def tearDown(self) -> None:
        self.temp.cleanup()

    def test_scoped_read_and_atomic_write_cas(self) -> None:
        payload, receipt = self.port.read_bytes("data/a.txt")
        self.assertEqual(payload.decode("utf-8").splitlines(), ["甲"])
        written = self.port.atomic_write("data/a.txt", "乙\n".encode(), expected_before=receipt["digest"])
        self.assertEqual(written["status"], "COMMITTED")
        with self.assertRaises(IntegrityError):
            self.port.atomic_write("data/a.txt", b"bad", expected_before=receipt["digest"])
        with self.assertRaises(ValidationError):
            self.port.read_bytes("../escape.txt")

    def test_bounded_command_has_no_shell_and_requires_binding(self) -> None:
        receipt = self.port.run_command("python", ["-I", "-B", "-c", "print('ok')"], timeout_seconds=5)
        self.assertEqual(receipt["status"], "OBSERVED")
        self.assertEqual(receipt["exit_code"], 0)
        with self.assertRaises(ValidationError):
            self.port.run_command("missing", [], timeout_seconds=1)

    def test_bounded_command_timeout_is_a_typed_receipt(self) -> None:
        receipt = self.port.run_command(
            "python",
            ["-I", "-B", "-c", "import time; time.sleep(2)"],
            timeout_seconds=1,
        )
        self.assertEqual(receipt["status"], "TIMEOUT")
        self.assertIsNone(receipt["exit_code"])

    def test_llm_proposal_is_receipt_only(self) -> None:
        receipt = self.port.propose({"goal": "检查"})
        self.assertEqual(receipt["status"], "PROPOSED")
        self.assertEqual(receipt["proposal"], {"echo": {"goal": "检查"}})

    def test_codex_descriptor_is_honest_and_false_enforced_is_rejected(self) -> None:
        repo = Path(__file__).resolve().parents[1]
        descriptor = json.loads((repo / "adapters" / "codex-audited.json").read_text(encoding="utf-8"))
        self.assertEqual(validate_adapter_descriptor(descriptor, repo)["profile"], "AUDITED")
        false_claim = copy.deepcopy(descriptor)
        false_claim["profile"] = "ENFORCED"
        false_claim = with_digest(false_claim)
        with self.assertRaises(ValidationError):
            validate_adapter_descriptor(false_claim, repo)

    def test_stale_process_lock_is_recovered_and_live_process_lock_is_respected(self) -> None:
        lock = self.root / "ledger.lock"
        lock.write_text("99999999", encoding="ascii")
        with exclusive_lock(lock, timeout=0.1):
            self.assertTrue(lock.exists())
        self.assertFalse(lock.exists())

        repo = Path(__file__).resolve().parents[1]
        environment = dict(os.environ)
        environment["PYTHONPATH"] = str(repo / "src")
        script = (
            "import sys,time\n"
            "from pathlib import Path\n"
            "from yuan.ledger import exclusive_lock\n"
            "with exclusive_lock(Path(sys.argv[1])):\n"
            " print('READY', flush=True)\n"
            " time.sleep(1)\n"
        )
        process = subprocess.Popen(
            [sys.executable, "-B", "-c", script, str(lock)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=environment,
        )
        try:
            self.assertEqual(process.stdout.readline().strip(), "READY")
            with self.assertRaisesRegex(IntegrityError, "Lock 超时"):
                with exclusive_lock(lock, timeout=0.1):
                    pass
        finally:
            process.communicate(timeout=5)

    def test_adapter_check_and_seal_work_through_cli(self) -> None:
        repo = Path(__file__).resolve().parents[1]
        environment = dict(os.environ)
        environment["PYTHONPATH"] = str(repo / "src")
        adapter = subprocess.run(
            [sys.executable, "-B", "-m", "yuan", "--root", str(repo), "adapter", "check", "adapters/codex-audited.json"],
            cwd=repo,
            env=environment,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            timeout=10,
        )
        self.assertEqual(adapter.returncode, 0, adapter.stderr.decode(errors="replace"))
        self.assertEqual(json.loads(adapter.stdout)["status"], "PASS")
        draft = self.root / "draft.json"
        draft.write_text('{"value":1}', encoding="utf-8")
        sealed = subprocess.run(
            [sys.executable, "-B", "-m", "yuan", "--root", str(self.root), "seal", str(draft)],
            cwd=repo,
            env=environment,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            timeout=10,
        )
        self.assertEqual(sealed.returncode, 0, sealed.stderr.decode(errors="replace"))
        self.assertEqual(json.loads(sealed.stdout)["digest"], digest({"value": 1}))


class ReleaseTests(unittest.TestCase):
    def test_zipapp_build_is_byte_reproducible_and_self_contained(self) -> None:
        repo = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            first = root / "first" / "yuan.pyz"
            second = root / "second" / "yuan.pyz"
            first.parent.mkdir()
            second.parent.mkdir()
            manifest_a = build_zipapp(repo, first)
            manifest_b = build_zipapp(repo, second)
            self.assertEqual(first.read_bytes(), second.read_bytes())
            self.assertEqual(manifest_a, manifest_b)
            self.assertEqual(verify_release(manifest_a, first, repo_root=repo)["status"], "PASS")
            result = subprocess.run(
                [sys.executable, "-B", str(first), "--help"],
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=20,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr.decode(errors="replace"))

    def test_release_tamper_is_rejected(self) -> None:
        repo = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as temporary:
            artifact = Path(temporary) / "yuan.pyz"
            manifest = build_zipapp(repo, artifact)
            artifact.write_bytes(artifact.read_bytes() + b"tamper")
            with self.assertRaises(IntegrityError):
                verify_release(manifest, artifact)

    def test_installed_runtime_matches_repository_release(self) -> None:
        repo = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source_artifact = root / "source" / "yuan.pyz"
            installed_artifact = root / "installed" / "yuan.pyz"
            build_zipapp(repo, source_artifact)
            build_runtime_zipapp(installed_artifact)
            self.assertEqual(source_artifact.read_bytes(), installed_artifact.read_bytes())


class ProjectInstallerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.release_context = current_release_context()
        (self.root / "AGENTS.md").write_text("# 项目原有规则\n", encoding="utf-8")
        (self.root / ".gitignore").write_text("node_modules/\n", encoding="utf-8")

    def tearDown(self) -> None:
        self.temp.cleanup()

    def record_memory_and_handoff(
        self,
        evidence_id: str,
        *,
        memory_id: str = "MEM-TEST-001",
        bind_paths: list[str] | None = None,
    ) -> dict:
        memory = memory_template(
            self.root,
            memory_id=memory_id,
            kind="feature",
            title="测试长期记忆",
            summary="当前 Work 已由 PASS Evidence 验证。",
            details="该记录用于证明 Memory 与 Work/Evidence/Handoff 闭环。",
            tags=["test"],
            bind_paths=bind_paths,
        )
        recorded = record_memory(self.root, memory)
        handoff = handoff_template(
            self.root,
            handoff_id=f"HO-MEMORY-{memory_id}",
            agent_id="memory-curator",
            to_agent_id="conductor",
            phase="handoff",
            status="READY",
            summary=f"Memory Curator 已记录 {memory_id}。",
            evidence_ids=[evidence_id],
        )
        result = record_handoff(self.root, handoff)
        return {"memory": memory, "recorded": recorded, "handoff": result}

    def test_sync_script_prints_machine_result_and_agent_guidance(self) -> None:
        repo = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as evidence:
            report = Path(evidence) / "conformance.json"
            report.write_bytes(canonical_bytes(self.release_context["report"]))
            completed = subprocess.run(
                [
                    sys.executable,
                    "-B",
                    str(repo / "scripts" / "sync_project.py"),
                    "install",
                    str(self.root),
                    "--run-id",
                    "RUN-SCRIPT-GUIDANCE",
                    "--conformance-report",
                    str(report),
                ],
                cwd=repo,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
                timeout=60,
            )
        result = json.loads(completed.stdout.decode("utf-8"))
        guidance = completed.stderr.decode("utf-8")
        self.assertEqual(completed.returncode, 0, guidance)
        self.assertEqual(result["status"], "INSTALLED")
        self.assertIn("agent_guidance", result)
        self.assertIn("Yuan 下一步", guidance)
        self.assertIn("开始新工作时发送", guidance)
        self.assertIn("继续未完成工作时发送", guidance)

    def test_install_pins_runtime_merges_bootstrap_and_updates(self) -> None:
        installed = install_project(self.root, release_context=self.release_context, run_id="RUN-INSTALL-TEST")
        self.assertEqual(installed["status"], "INSTALLED")
        self.assertEqual(installed["agent_guidance"], agent_guidance(self.root))
        self.assertIn("AGENTS.md", installed["agent_guidance"]["start_prompt"])
        self.assertIn("继续未完成的 Work", installed["agent_guidance"]["continue_prompt"])
        runtime = self.root / ".yuan" / "bin" / "yuan.pyz"
        self.assertTrue(runtime.is_file())
        config = json.loads((self.root / ".yuan" / "config.json").read_text(encoding="utf-8"))
        self.assertEqual(config["protocol"]["revision"], "0.3")
        manifest = json.loads((self.root / ".yuan" / "extensions" / "manifest.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["profile_id"], "vibe-coding")
        self.assertEqual(manifest["schema_version"], "yuan.capability-profile/v2")
        self.assertTrue((self.root / ".yuan" / "extensions" / "vibe-coding" / "rules" / "01-workflow.md").is_file())
        self.assertTrue((self.root / ".yuan" / "extensions" / "vibe-coding" / "agents" / "conductor.md").is_file())
        self.assertTrue((self.root / ".yuan" / "extensions" / "vibe-coding" / "skills" / "systematic-debugging" / "SKILL.md").is_file())
        for relative in ("INDEX.md", "CURRENT.md", "PROJECT.md", "views/DECISIONS.md", "views/PITFALLS.md"):
            self.assertTrue((self.root / "docs" / "memory" / relative).is_file())
        custom = self.root / ".yuan" / "extensions" / "custom" / "project-rule.md"
        custom.write_text("# 项目自定义规则\n", encoding="utf-8")
        agents = (self.root / "AGENTS.md").read_text(encoding="utf-8")
        self.assertIn("# 项目原有规则", agents)
        self.assertEqual(agents.count(BOOTSTRAP_START), 1)
        self.assertEqual(agents.count(BOOTSTRAP_END), 1)
        ignored = (self.root / ".gitignore").read_text(encoding="utf-8")
        self.assertIn("node_modules/", ignored)
        self.assertIn(".yuan-run/", ignored)
        status = subprocess.run(
            [sys.executable, "-B", str(runtime), "--root", str(self.root), "status"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            timeout=30,
        )
        self.assertEqual(status.returncode, 0, status.stderr.decode(errors="replace"))
        self.assertIsNone(json.loads(status.stdout)["work"])
        forced = update_project(self.root, release_context=self.release_context)
        self.assertEqual(forced["status"], "UPDATED")
        self.assertTrue(forced["memory_preserved"])
        self.assertEqual((self.root / "AGENTS.md").read_text(encoding="utf-8").count(BOOTSTRAP_START), 1)

        previous_bytes = runtime.read_bytes()
        previous_digest = digest_bytes(previous_bytes)
        next_context, builder = altered_candidate(b"next-release")
        with mock.patch("yuan.project.build_runtime_zipapp", side_effect=builder):
            updated = update_project(self.root, release_context=next_context)
        self.assertEqual(updated["status"], "UPDATED")
        self.assertNotEqual(digest_bytes(runtime.read_bytes()), previous_digest)
        self.assertTrue(updated["memory_preserved"])
        self.assertFalse((self.root / ".yuan" / "releases" / previous_digest / "snapshot.json").exists())
        self.assertEqual(custom.read_text(encoding="utf-8"), "# 项目自定义规则\n")

    def test_install_never_overwrites_existing_project_memory(self) -> None:
        memory = self.root / "docs" / "memory" / "CURRENT.md"
        memory.parent.mkdir(parents=True)
        memory.write_text("# 人工维护的历史交接\n", encoding="utf-8")
        installed = install_project(self.root, release_context=self.release_context, run_id="RUN-EXISTING-MEMORY")
        self.assertFalse(installed["memory_scaffolded"])
        self.assertEqual(memory.read_text(encoding="utf-8"), "# 人工维护的历史交接\n")
        self.assertFalse((self.root / "docs" / "memory" / "index.json").exists())

    def test_installed_runtime_lists_and_resolves_capabilities(self) -> None:
        install_project(self.root, release_context=self.release_context, run_id="RUN-CAPABILITY-CLI")
        runtime = self.root / ".yuan" / "bin" / "yuan.pyz"
        listed = subprocess.run(
            [sys.executable, "-B", str(runtime), "--root", str(self.root), "capability", "list"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            timeout=30,
        )
        self.assertEqual(listed.returncode, 0, listed.stderr.decode(errors="replace"))
        catalog = json.loads(listed.stdout)
        self.assertIn("conductor", {item["id"] for item in catalog["agents"]})
        self.assertIn("project-lifecycle", {item["id"] for item in catalog["skills"]})
        resolved = subprocess.run(
            [
                sys.executable, "-B", str(runtime), "--root", str(self.root),
                "capability", "resolve", "--agent", "conductor", "--skill", "project-lifecycle",
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            timeout=30,
        )
        self.assertEqual(resolved.returncode, 0, resolved.stderr.decode(errors="replace"))
        selection = json.loads(resolved.stdout)
        self.assertEqual(selection["status"], "RESOLVED")
        self.assertEqual(len(selection["rules"]), len(catalog["required_rules"]))
        self.assertEqual(selection["agents"][0]["id"], "conductor")
        self.assertEqual(selection["skills"][0]["id"], "project-lifecycle")
        routed = subprocess.run(
            [
                sys.executable, "-B", str(runtime), "--root", str(self.root),
                "capability", "route", "--risk", "R1", "--signal", "backend",
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            timeout=30,
        )
        self.assertEqual(routed.returncode, 0, routed.stderr.decode(errors="replace"))
        route = json.loads(routed.stdout)
        self.assertEqual(route["status"], "ROUTED")
        self.assertEqual(
            route["routing"]["agents"],
            ["conductor", "backend-developer", "spec-reviewer", "tester", "memory-curator"],
        )
        assignments = {item["agent_id"]: item["skills"] for item in route["assignments"]}
        self.assertIn("test-driven-development", assignments["backend-developer"])
        self.assertIn("code-review", assignments["spec-reviewer"])
        self.assertEqual(
            set(route["routing"]["skills"]),
            {skill_id for skill_ids in assignments.values() for skill_id in skill_ids},
        )
        debugging = route_capabilities(self.root, risk="R2", signals=["debugging"])
        self.assertIn("debugger", debugging["routing"]["agents"])
        self.assertIn("runtime-maintainer", debugging["routing"]["agents"])
        self.assertIn("systematic-debugging", debugging["routing"]["skills"])
        self.assertIn("runtime-recovery", debugging["routing"]["skills"])
        signal_ids = list(catalog["workflow"]["signal_routes"])
        for risk in ("R0", "R1", "R2"):
            for signals in [[], *[[signal_id] for signal_id in signal_ids]]:
                candidate = route_capabilities(self.root, risk=risk, signals=signals)
                assigned = {
                    skill_id
                    for assignment in candidate["assignments"]
                    for skill_id in assignment["skills"]
                }
                self.assertEqual(set(candidate["routing"]["skills"]), assigned)

    def test_custom_extension_can_be_bound_discovered_and_isolated(self) -> None:
        install_project(self.root, release_context=self.release_context, run_id="RUN-CUSTOM-EXTENSION")
        extension = self.root / ".yuan" / "extensions" / "custom" / "team"
        rule = extension / "rules" / "release.md"
        agent = extension / "agents" / "release-owner.md"
        skill = extension / "skills" / "deploy-review" / "SKILL.md"
        rule.parent.mkdir(parents=True)
        agent.parent.mkdir(parents=True)
        skill.parent.mkdir(parents=True)
        rule.write_text("# 团队发布规则\n", encoding="utf-8")
        agent.write_text("# 团队发布负责人\n", encoding="utf-8")
        skill.write_text("# 团队发布审查\n", encoding="utf-8")
        draft = {
            "schema_version": "yuan.custom-extension/v1",
            "extension_id": "team",
            "description": "团队工程规则。",
            "rules": [{
                "id": "release-rule",
                "path": "rules/release.md",
                "description": "团队发布规则。",
                "use_when": ["发布前"],
            }],
            "agents": [{
                "id": "release-owner",
                "path": "agents/release-owner.md",
                "description": "团队发布负责人。",
                "use_when": ["发布前"],
            }],
            "skills": [{
                "id": "deploy-review",
                "path": "skills/deploy-review/SKILL.md",
                "description": "团队发布前审查。",
                "use_when": ["发布前"],
            }],
        }
        (extension / "extension.json").write_text(json.dumps(draft, ensure_ascii=False), encoding="utf-8")
        runtime = self.root / ".yuan" / "bin" / "yuan.pyz"
        bound = subprocess.run(
            [
                sys.executable, "-B", str(runtime), "--root", str(self.root),
                "capability", "bind-custom", ".yuan/extensions/custom/team", "--write",
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
            timeout=30,
        )
        self.assertEqual(bound.returncode, 0, bound.stderr.decode(errors="replace"))
        self.assertEqual(json.loads(bound.stdout)["status"], "CUSTOM_BOUND")
        catalog = installed_catalog(self.root)
        self.assertEqual(catalog["custom_errors"], [])
        self.assertIn("team:release-rule", {item["id"] for item in catalog["custom_rules"]})
        self.assertIn("team:release-owner", {item["id"] for item in catalog["agents"]})
        self.assertIn("team:deploy-review", {item["id"] for item in catalog["skills"]})
        selection = resolve_capabilities(
            self.root,
            rules=["team:release-rule"],
            agents=["team:release-owner"],
            skills=["team:deploy-review"],
        )
        self.assertEqual(selection["rules"][-1]["source"], "custom")
        self.assertEqual(selection["agents"][-1]["source"], "custom")
        self.assertEqual(selection["skills"][0]["source"], "custom")
        skill.write_text("tampered\n", encoding="utf-8")
        catalog = installed_catalog(self.root)
        self.assertEqual(catalog["agents"][0]["id"], "conductor")
        self.assertEqual(catalog["custom_errors"][0]["extension_id"], "team")

    def test_first_work_template_uses_non_artifact_verifier_draft(self) -> None:
        install_project(self.root, release_context=self.release_context, run_id="RUN-FIRST-WORK-TEMPLATE")
        work = work_template(self.root, intake=confirmed_intake("创建首个测试 Work。"))
        verifier = work["acceptance_criteria"][0]["verifier"]
        self.assertTrue(verifier["entrypoint"].startswith(".yuan/drafts/verifiers/"))
        self.assertIn(verifier["entrypoint"], {item["path"] for item in verifier["files"]})
        self.assertEqual(validate_work(work), work)

    def test_empty_project_can_follow_bootstrap_to_complete_first_work(self) -> None:
        install_project(self.root, release_context=self.release_context, run_id="RUN-LLM-BOOTSTRAP")
        initial = project_status(self.root)
        self.assertEqual(initial["decision"], {"result": "BLOCKED", "reasons": ["没有 Active Work"]})
        selection = route_capabilities(self.root, risk="R2", signals=[])
        self.assertEqual(selection["status"], "ROUTED")
        self.assertEqual(selection["routing"]["agents"], ["conductor", "tester", "memory-curator"])

        work = work_template(self.root, intake=confirmed_intake("创建内容为 hello 的 app.txt。"))
        # 模拟由旧 Runtime 创建、尚未声明长期记忆排除项的历史 Work。
        work["artifact"]["exclude"].remove("docs/memory/**")
        verifier_path = self.root / work["acceptance_criteria"][0]["verifier"]["entrypoint"]
        verifier_path.parent.mkdir(parents=True)
        verifier_path.write_text(
            "import json, pathlib, sys\n"
            "passed = (pathlib.Path(sys.argv[1]) / 'app.txt').read_text(encoding='utf-8') == 'hello\\n'\n"
            "print(json.dumps({'status': 'PASS' if passed else 'FAIL', 'assertions': [{'id': 'app-content', 'passed': passed}]}))\n",
            encoding="utf-8",
        )
        work["goal"] = "创建内容为 hello 的 app.txt。"
        criterion = work["acceptance_criteria"][0]
        criterion["description"] = "app.txt 的内容严格等于 hello 加换行。"
        criterion["verifier"]["id"] = "verify.app-content"
        files = criterion["verifier"]["files"]
        files[0]["digest"] = digest_bytes(verifier_path.read_bytes())
        criterion["verifier"]["digest"] = digest({
            "kind": criterion["verifier"]["kind"],
            "entrypoint": criterion["verifier"]["entrypoint"],
            "files": files,
        })
        work["safety_invariants"] = []
        work["grants"][0]["action_types"] = ["file-write"]
        work["grants"][0]["side_effect_classes"] = ["filesystem"]
        work["grants"][0]["scopes"] = ["app.txt"]
        work = confirm_work(work, "用户确认 app.txt 的完整 Work Contract")
        under_routed = copy.deepcopy(work)
        for field in ("agents", "handoff_agents", "artifact_review_agents"):
            under_routed["routing"][field].remove("tester")
        under_routed["routing"] = with_digest(under_routed["routing"])
        under_routed = confirm_work(under_routed, "测试用户确认被错误降级的 Routing")
        with self.assertRaisesRegex(ValidationError, "Routing 与已安装 Capability Workflow 不匹配"):
            accept_work(self.root, under_routed)
        accepted = accept_work(self.root, work)
        self.assertEqual(accepted["decision"]["result"], "CONTINUE")

        decision = memory_template(
            self.root,
            memory_id="MEM-DECISION-001",
            kind="decision",
            title="采用追加式项目记忆",
            summary="用户确认的 Work 可在 PASS 前保存决策。",
            details="决策事实来源于已确认 Work，而不是伪装成实现验证。",
        )
        self.assertEqual(decision["confidence"], "decided")
        self.assertEqual(decision["source"]["evidence_ids"], [])
        record_memory(self.root, decision)
        checkpoint_memory(
            self.root,
            summary="已接受 Work，尚未执行实现。",
            details="该检查点证明项目连续性不依赖 PASS Evidence。",
            completed=["需求与 Work 已确认"],
            next_steps=["创建 app.txt"],
            resume_commands=["python -B .yuan/bin/yuan.pyz --root . status"],
        )
        resumed = memory_resume(self.root, "追加式项目记忆")
        self.assertEqual(resumed["current"]["memory_id"], "CURRENT")
        self.assertEqual(resumed["current"]["data"]["next_steps"], ["创建 app.txt"])
        self.assertIn("创建 app.txt", (self.root / "docs" / "memory" / "CURRENT.md").read_text(encoding="utf-8"))
        self.assertIn("MEM-DECISION-001", (self.root / "docs" / "memory" / "views" / "DECISIONS.md").read_text(encoding="utf-8"))

        proposal = attempt_template(
            self.root,
            attempt_id="ATT-FIRST-WORK",
            strategy="创建目标文件",
            claim="写入目标内容后 Criterion 成立",
            falsification="Verifier 观察到缺失或不同内容",
            inputs=[],
            action_type="file-write",
            paths=["app.txt"],
            side_effect_class="filesystem",
            grant_id="GRANT-001",
            read_only=False,
            high_impact=False,
            tool_calls=1,
            command_seconds=0,
        )
        begin_attempt(self.root, proposal)
        dispatch_attempt(self.root, "ATT-FIRST-WORK")
        (self.root / "app.txt").write_text("hello\n", encoding="utf-8")
        observed = observe_attempt(self.root, "ATT-FIRST-WORK", {"kind": "agent-platform", "status": "OK"})
        self.assertEqual(observed["decision"]["result"], "CONTINUE")
        verified = run_verifier(self.root, "AC-001", "ATT-FIRST-WORK")
        self.assertEqual(verified["decision"]["result"], "CONTINUE")
        handoff = handoff_template(
            self.root,
            handoff_id="HO-TESTER-FIRST",
            agent_id="tester",
            to_agent_id="conductor",
            phase="verification",
            status="READY",
            summary="Tester 已验证 app.txt 的当前 Artifact。",
            evidence_ids=[verified["event"]["payload"]["evidence_id"]],
        )
        self.assertEqual(record_handoff(self.root, handoff)["decision"]["result"], "CONTINUE")
        memory_result = self.record_memory_and_handoff(
            verified["event"]["payload"]["evidence_id"],
            bind_paths=["app.txt"],
        )
        self.assertEqual(memory_result["handoff"]["decision"]["result"], "COMPLETE")
        self.assertEqual(record_reduction(self.root)["decision"]["result"], "COMPLETE")
        legacy = memory_template(
            self.root,
            memory_id="MEM-V1-COMPAT",
            kind="module",
            title="v1 兼容记录",
            summary="旧版路径与字段仍然可读。",
            details="发行升级不能丢弃已有项目 Memory。",
        )
        legacy["schema_version"] = "yuan.memory/v1"
        legacy.pop("data")
        legacy["source"].pop("attempt_ids")
        legacy = with_digest(legacy)
        recorded_legacy = record_memory(self.root, legacy)
        self.assertEqual(recorded_legacy["record"], "docs/memory/records/module/MEM-V1-COMPAT/000001.json")
        second = memory_template(
            self.root,
            memory_id="MEM-TEST-001",
            kind="feature",
            title="测试长期记忆第二版",
            summary="同一 Memory ID 通过追加 Revision 演进。",
            details="旧 Revision 保持不变，新 Revision 绑定当前 Work/Evidence。",
            tags=["test", "revision"],
            bind_paths=["app.txt"],
        )
        self.assertEqual(second["revision"], 2)
        self.assertEqual(second["supersedes"], memory_result["memory"]["digest"])
        record_memory(self.root, second)
        heads = {item["memory_id"]: item for item in rebuild_memory(self.root, write=False)["heads"]}
        self.assertEqual(heads["MEM-TEST-001"]["revision"], 2)
        context = memory_context(self.root, "长期 追加 Revision")
        self.assertEqual(context["memories"][0]["record"]["memory_id"], "MEM-TEST-001")
        self.assertTrue({"长期", "追加", "revision"} <= set(context["memories"][0]["matched_terms"]))
        self.assertEqual(memory_status(self.root)["stale"], 0)
        (self.root / "app.txt").write_text("changed\n", encoding="utf-8")
        self.assertEqual(memory_status(self.root)["stale"], 1)

    def test_capability_tamper_fails_installation_verification(self) -> None:
        install_project(self.root, release_context=self.release_context, run_id="RUN-CAPABILITY-TAMPER")
        rule = self.root / ".yuan" / "extensions" / "vibe-coding" / "rules" / "00-boundary.md"
        rule.write_text(rule.read_text(encoding="utf-8") + "篡改\n", encoding="utf-8")
        with self.assertRaises(IntegrityError):
            project_status(self.root)

    def test_runtime_rejects_config_capability_binding_drift(self) -> None:
        install_project(self.root, release_context=self.release_context, run_id="RUN-CAPABILITY-BINDING")
        config_path = self.root / ".yuan" / "config.json"
        config = json.loads(config_path.read_text(encoding="utf-8"))
        config["capability"]["digest"] = "0" * 64
        atomic_write(config_path, canonical_bytes(with_digest(config)))
        with self.assertRaisesRegex(IntegrityError, "Capability Profile Binding 不匹配"):
            load_config(self.root)

    def test_update_force_activates_candidate_while_work_is_nonterminal(self) -> None:
        install_project(self.root, release_context=self.release_context, run_id="RUN-STAGE-TEST")
        (self.root / "tests").mkdir()
        verifier_path = self.root / "tests" / "verify.py"
        verifier_path.write_text(
            "import json\nprint(json.dumps({'status':'FAIL','assertions':[{'id':'pending','passed':False}]}))\n",
            encoding="utf-8",
        )
        config = load_config(self.root)
        files = [{"path": "tests/verify.py", "digest": digest_bytes(verifier_path.read_bytes())}]
        verifier = {
            "id": "test.pending",
            "revision": "1",
            "digest": digest({"kind": "python-script", "entrypoint": "tests/verify.py", "files": files}),
            "kind": "python-script",
            "entrypoint": "tests/verify.py",
            "timeout_seconds": 10,
            "files": files,
        }
        intake = confirmed_intake("保持非终态以验证 Candidate Staging。")
        work = {
            "schema_version": "yuan.work/v2",
            "work_id": "WORK-STAGE",
            "revision": 1,
            "goal": "保持非终态以验证 Candidate Staging。",
            "profile": config["profile"],
            "protocol": config["protocol"],
            "harness": config["harness"],
            "intake": intake,
            "routing": routing_plan(self.root, risk="R2", signals=[]),
            "confirmation": None,
            "artifact": {
                "root": ".",
                "include": ["**"],
                "exclude": [".git/**", ".yuan/**", ".yuan-run/**", "__pycache__/**", "*.pyc"],
                "environment": config["environment"],
            },
            "acceptance_criteria": [{
                "id": "AC-PENDING",
                "description": "测试保持未完成。",
                "required": True,
                "verifier": verifier,
                "min_assertions": 1,
                "independence": "independent",
            }],
            "safety_invariants": [],
            "grants": [],
            "budgets": {"ticks": 2, "attempts": 2, "tool_calls": 2, "command_seconds": 2},
            "predecessor": None,
            "created_at": "2026-08-02T00:00:00Z",
        }
        work = confirm_work(work, "用户确认 Candidate Staging 测试契约")
        accept_work(self.root, work)
        current = (self.root / ".yuan" / "bin" / "yuan.pyz").read_bytes()
        memory_before = {path.relative_to(self.root).as_posix(): path.read_bytes() for path in (self.root / ".yuan-run").rglob("*") if path.is_file()}
        next_context, builder = altered_candidate(b"candidate-release")
        with mock.patch("yuan.project.build_runtime_zipapp", side_effect=builder):
            updated = update_project(self.root, release_context=next_context)
        self.assertEqual(updated["status"], "UPDATED")
        self.assertEqual(updated["agent_guidance"], agent_guidance(self.root))
        self.assertNotEqual((self.root / ".yuan" / "bin" / "yuan.pyz").read_bytes(), current)
        self.assertTrue(updated["memory_preserved"])
        self.assertEqual(project_status(self.root)["staged"], [])
        memory_after = {path.relative_to(self.root).as_posix(): path.read_bytes() for path in (self.root / ".yuan-run").rglob("*") if path.is_file()}
        self.assertEqual(memory_after, memory_before)

    def test_complete_work_allows_verified_update(self) -> None:
        (self.root / "src").mkdir()
        (self.root / "tests").mkdir()
        (self.root / "src" / "app.py").write_text("VALUE = 1\n", encoding="utf-8")
        verifier_path = self.root / "tests" / "verify.py"
        verifier_path.write_text(
            "import json\nprint(json.dumps({'status':'PASS','assertions':[{'id':'ok','passed':True}]}))\n",
            encoding="utf-8",
        )
        install_project(self.root, release_context=self.release_context, run_id="RUN-COMPLETE-UPDATE")
        work = work_template(self.root, intake=confirmed_intake("验证完成态更新。"))
        files = [{"path": "tests/verify.py", "digest": digest_bytes(verifier_path.read_bytes())}]
        verifier = work["acceptance_criteria"][0]["verifier"]
        verifier.update(id="test.complete-update", entrypoint="tests/verify.py", files=files)
        verifier["digest"] = digest({"kind": verifier["kind"], "entrypoint": verifier["entrypoint"], "files": files})
        work = confirm_work(work, "用户确认完成态更新 Work")
        accept_work(self.root, work)
        proposal = attempt_template(
            self.root,
            attempt_id="ATT-COMPLETE-UPDATE",
            strategy="只读验证",
            claim="Verifier 通过",
            falsification="Verifier 失败",
            inputs=["src/app.py"],
            action_type="file-read",
            paths=["src"],
            side_effect_class="none",
            grant_id="GRANT-001",
            read_only=True,
            high_impact=False,
            tool_calls=1,
            command_seconds=0,
        )
        begin_attempt(self.root, proposal)
        verified = run_verifier(self.root, "AC-001", "ATT-COMPLETE-UPDATE")
        handoff = handoff_template(
            self.root,
            handoff_id="HO-TESTER-UPDATE",
            agent_id="tester",
            to_agent_id="conductor",
            phase="verification",
            status="READY",
            summary="Tester 已验证完成态更新的当前 Artifact。",
            evidence_ids=[verified["event"]["payload"]["evidence_id"]],
        )
        record_handoff(self.root, handoff)
        self.record_memory_and_handoff(verified["event"]["payload"]["evidence_id"], memory_id="MEM-UPDATE-001")
        self.assertEqual(record_reduction(self.root)["decision"]["result"], "COMPLETE")
        next_context, builder = altered_candidate(b"complete-update")
        with mock.patch("yuan.project.build_runtime_zipapp", side_effect=builder):
            updated = update_project(self.root, release_context=next_context)
        self.assertEqual(updated["status"], "UPDATED")
        self.assertEqual(updated["diagnostics"]["decision"]["result"], "COMPLETE")

    def test_forced_update_repairs_corrupt_install_and_preserves_memory(self) -> None:
        install_project(self.root, release_context=self.release_context, run_id="RUN-FORCE-REPAIR")
        long_term = self.root / "docs" / "memory" / "keep.txt"
        long_term.parent.mkdir(parents=True, exist_ok=True)
        long_term.write_text("project memory\n", encoding="utf-8")
        custom = self.root / ".yuan" / "extensions" / "custom" / "keep.txt"
        custom.write_text("custom capability\n", encoding="utf-8")
        ledger_before = {
            path.relative_to(self.root).as_posix(): path.read_bytes()
            for path in (self.root / ".yuan-run").rglob("*") if path.is_file()
        }
        (self.root / ".yuan" / "bin" / "yuan.pyz").write_bytes(b"broken runtime")
        (self.root / ".yuan" / "config.json").write_text("not-json", encoding="utf-8")
        (self.root / ".yuan" / "install.json").write_text("not-json", encoding="utf-8")
        agents = (self.root / "AGENTS.md").read_text(encoding="utf-8").replace(BOOTSTRAP_END, "")
        (self.root / "AGENTS.md").write_text(agents, encoding="utf-8")

        updated = update_project(self.root)

        self.assertEqual(updated["status"], "UPDATED")
        self.assertTrue(updated["memory_preserved"])
        self.assertEqual(long_term.read_text(encoding="utf-8"), "project memory\n")
        self.assertEqual(custom.read_text(encoding="utf-8"), "custom capability\n")
        ledger_after = {
            path.relative_to(self.root).as_posix(): path.read_bytes()
            for path in (self.root / ".yuan-run").rglob("*") if path.is_file()
        }
        self.assertEqual(ledger_after, ledger_before)
        self.assertEqual((self.root / "AGENTS.md").read_text(encoding="utf-8").count(BOOTSTRAP_START), 1)
        self.assertEqual(project_status(self.root)["status"], "PASS")

    def test_forced_update_bootstraps_project_without_old_install(self) -> None:
        updated = update_project(self.root)
        self.assertEqual(updated["status"], "UPDATED")
        self.assertTrue(updated["memory_preserved"])
        self.assertIsNotNone(updated["memory_initialized_run"])
        self.assertTrue((self.root / ".yuan" / "bin" / "yuan.pyz").is_file())
        self.assertEqual(project_status(self.root)["decision"], {"result": "BLOCKED", "reasons": ["没有 Active Work"]})

    def test_failed_install_restores_original_project(self) -> None:
        original_agents = (self.root / "AGENTS.md").read_bytes()
        original_ignore = (self.root / ".gitignore").read_bytes()
        with self.assertRaises(ValidationError):
            install_project(self.root, release_context=self.release_context, run_id="invalid run id")
        self.assertEqual((self.root / "AGENTS.md").read_bytes(), original_agents)
        self.assertEqual((self.root / ".gitignore").read_bytes(), original_ignore)
        self.assertFalse((self.root / ".yuan" / "config.json").exists())
        installed = install_project(self.root, release_context=self.release_context, run_id="RUN-RETRY")
        self.assertEqual(installed["status"], "INSTALLED")

    def test_install_rejects_unbound_conformance_without_residue(self) -> None:
        context = copy.deepcopy(self.release_context)
        context["report"]["checks"]["reproducible_release"]["artifact_digest"] = "0" * 64
        with self.assertRaises(IntegrityError):
            install_project(self.root, release_context=context, run_id="RUN-BAD-REPORT")
        self.assertFalse((self.root / ".yuan" / "config.json").exists())
        self.assertFalse((self.root / ".yuan" / "bin" / "yuan.pyz").exists())
        self.assertEqual(list((self.root / ".yuan" / "candidates").glob("*.pyz")), [])

    def test_deployment_lock_rejects_concurrent_install(self) -> None:
        lock = self.root / ".yuan" / ".deployment.lock"
        with exclusive_lock(lock):
            with mock.patch("yuan.project.DEPLOYMENT_LOCK_TIMEOUT", 0.01):
                with self.assertRaises(IntegrityError):
                    install_project(self.root, release_context=self.release_context, run_id="RUN-LOCKED")


if __name__ == "__main__":
    unittest.main()
