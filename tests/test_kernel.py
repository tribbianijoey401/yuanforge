from __future__ import annotations

import copy
import json
import math
import sys
import subprocess
import tempfile
import unittest
from pathlib import Path

from yuan.artifacts import build_manifest, diff_manifests
from yuan.adapters import validate_adapter_descriptor
from yuan.canonical import canonical_bytes, digest, digest_bytes
from yuan.cli import init_repository
from yuan.errors import IntegrityError, ValidationError
from yuan.ledger import Ledger, atomic_write
from yuan.ports import ExecutableBinding, ReferencePort
from yuan.release import build_zipapp, verify_release
from yuan.reducer import reduce_projection
from yuan.runtime import (
    accept_work,
    active_ledger,
    add_evidence,
    begin_attempt,
    dispatch_attempt,
    load_config,
    observe_attempt,
    list_runs,
    predecessor_binding,
    rebuild,
    mark_attempt_unknown,
    resolve_attempt,
    run_verifier,
    start_successor,
    verify_work_verifiers,
)
from yuan.validate import validate_evidence, with_digest


ZERO = "0" * 64


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
            "schema_version": "yuan.work/v1",
            "work_id": "WORK-TEST",
            "revision": 1,
            "goal": "修改 VALUE 并证明结果。",
            "profile": "AUDITED",
            "protocol": self.config["protocol"],
            "harness": self.config["harness"],
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
        return with_digest(work)

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

    def test_relevant_input_must_match_current_bytes(self) -> None:
        proposal = self.proposal()
        proposal["relevant_inputs"][0]["digest"] = "9" * 64
        with self.assertRaises(ValidationError):
            begin_attempt(self.root, proposal)

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

    def test_selected_protocol_is_verified_on_every_command(self) -> None:
        (self.root / ".yuan" / "protocol.md").write_text("tampered\n", encoding="utf-8")
        with self.assertRaises(IntegrityError):
            rebuild(self.root)

    def test_wait_auth_can_continue_in_bound_successor_work_revision(self) -> None:
        proposal = self.proposal(path="README.md")
        self.assertEqual(begin_attempt(self.root, proposal)["decision"]["result"], "WAIT_AUTH")
        _, ledger = active_ledger(self.root)
        projection = rebuild(self.root, write=False)
        successor = copy.deepcopy(self.work)
        successor["revision"] = 2
        successor["predecessor"] = predecessor_binding(ledger, projection)
        successor["grants"][0]["scopes"].append("README.md")
        successor = with_digest(successor)
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
        successor = with_digest(successor)
        with self.assertRaises(ValidationError):
            start_successor(self.root, successor, "RUN-BAD-R2")
        self.assertEqual(active_ledger(self.root)[1].run_id, "RUN-TEST")

    def test_nonterminal_run_cannot_be_replaced(self) -> None:
        _, ledger = active_ledger(self.root)
        projection = rebuild(self.root, write=False)
        successor = copy.deepcopy(self.work)
        successor["revision"] = 2
        successor["predecessor"] = predecessor_binding(ledger, projection)
        successor = with_digest(successor)
        with self.assertRaises(ValidationError):
            start_successor(self.root, successor, "RUN-EARLY-R2")


class PureKernelTests(unittest.TestCase):
    def test_canonical_json_is_stable_and_rejects_nan(self) -> None:
        self.assertEqual(canonical_bytes({"b": 2, "a": "元"}), b'{"a":"\xe5\x85\x83","b":2}')
        with self.assertRaises(ValidationError):
            canonical_bytes({"bad": math.nan})

    def projection(self) -> dict:
        work = {
            "budgets": {"ticks": 5},
            "acceptance_criteria": [{"id": "AC", "required": True}],
            "safety_invariants": [{"criterion_id": "AC"}],
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


if __name__ == "__main__":
    unittest.main()
