"""Independent task-012 Hard Gate for the live-Core M9 dogfood.

This suite is intentionally separate from the author-owned
``test_m9_dogfood.py``.  It validates committed artifacts and exercises trust
boundaries that are not part of the author-visible suite.
"""

from __future__ import annotations

import copy
import datetime as dt
import hashlib
import json
import os
import pathlib
import shutil
import sys
import tempfile
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[2]
GATE_MODE = os.environ.get("YUAN_M9_GATE_MODE", "active")
CANDIDATE_ROOT = (
    pathlib.Path(os.environ["YUAN_R2_CANDIDATE"]).resolve()
    if "YUAN_R2_CANDIDATE" in os.environ
    else None
)
TESTS = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(TESTS))

import m9_revision_gate as revision_gate

ROOT, VALIDATION_ROOT = revision_gate.gate_configuration(
    ROOT,
    mode=GATE_MODE,
    candidate_root=CANDIDATE_ROOT,
)
SCRIPTS = VALIDATION_ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))
sys.path.insert(0, str(VALIDATION_ROOT / ".yuan/core/0.1"))

import yuan_authority as authority
import yuan_activation as activation
import yuan_m9_dogfood as m9
import yuan_provenance_history as provenance
import yuan_runtime_state as runtime_state
import yuan_runtime_transaction as runtime_transaction


REVISION_HASHES = [
    "41013c2695358479daf8e9756af2654dc867cbf407980f9bc4ff45a84dccf147",
    "55c5a0134ccafd73895619cb0278f618129e2fd81f2e79a5a2ed66c2534953a4",
    "6cceb906f2770460aabe66a83857d79173ec996bd7efe81e8a1d91a30193aa83",
    "9f5b3de9f561fe1ecc16405a7c21dcd24824e1b4735572928cc47aff468b8183",
    "4e5fd4ed37306990b535da9f5a2bc3a0158c104550c3497d36c5207eb1ab000d",
    "ee5b57d0dcc6f466ef0500e9005a0f72f9d461391400db1ce28e18baae7873a2",
    "cb65f3c1464fd4dc97e328752cd1075a026aba897ca637fbbaae296996c8c647",
    "70e534c875aee40777f3b1c72fdb01d7c82a7fe788d6dd7a5ee06a2bae11d1ec",
]
REVISION_SIX_RUN = "WORK-yuan-m8-m9-successor-r2-398b8aefe078"
REVISION_SIX_MANIFEST = (
    "e2bc36fc5d0213912e46073bf4ca2a8aa52091311e7870e34c1f1987a3b64abe"
)
R2_PROTOCOL = "b61422bd4f76033234908fb89c149cccc0ebffd5b502e21eea5e26cd82a9c3c3"
R2_CANDIDATE = "57a2acad6ba92d879785139e35548bdd20cd1edcafa3d7e8b554321504ec8b5e"
R2_DESCRIPTOR = "6f08c7e10bcd433e2341471bef463e0d37fe6b6c7356f400988868a1b129afe8"
REVISION_SEVEN_RUN = "WORK-yuan-m8-m9-successor-r3-24820e1e41b7"
REVISION_SEVEN_MANIFEST = (
    "a135a77f8b6dddad29554e9145c79b8fe689ba1932bc44eea02c48a0940c1447"
)
REVISION_SEVEN_DESCRIPTOR = (
    "f6e35cfafc8dc50aa743dece471b1b4c5b40aa7467c6d8e79f391b9666d7143d"
)


def load_json(path: pathlib.Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def digest(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def parsed_time(value: str) -> dt.datetime:
    return dt.datetime.fromisoformat(value.replace("Z", "+00:00"))


class M9HeldOut(unittest.TestCase):
    maxDiff = None

    def copy_runtime_repo(self, destination: pathlib.Path) -> None:
        for relative in (".yuan", ".yuan-run", "scripts", "tests"):
            shutil.copytree(ROOT / relative, destination / relative)

    def validation_root_in(self, repo: pathlib.Path) -> pathlib.Path:
        if GATE_MODE == "active":
            return repo
        assert CANDIDATE_ROOT is not None
        try:
            relative = CANDIDATE_ROOT.relative_to(ROOT)
        except ValueError as error:
            raise revision_gate.GateError(
                "candidate-mode clones require the candidate under the repo"
            ) from error
        return repo / relative

    def committed_r1(
        self, repo: pathlib.Path = ROOT
    ) -> tuple[pathlib.Path, dict, dict, dict]:
        descriptor = load_json(
            repo / ".yuan/authority/activation/yuan-core-0.1.json"
        )
        for journal_path in (
            repo / ".yuan/authority/self-modification/transactions"
        ).glob("*/journal.json"):
            journal = load_json(journal_path)
            prepared_path = journal_path.parent / "attempt-prepared.json"
            if (
                journal.get("schema_version")
                != "yuan.self-modification-transaction/v2"
                or journal.get("state") != "COMMITTED"
                or not prepared_path.is_file()
            ):
                continue
            prepared = load_json(prepared_path)
            proof = prepared["action"]["self_modification"]["proofs"][0]
            if (
                proof.get("receipt_sha256")
                == descriptor.get("independent_evidence_sha256")
                and journal.get("candidate_manifest_sha256")
                == descriptor.get("candidate_manifest_sha256")
            ):
                return journal_path.parent, journal, prepared, proof
        self.fail("current rev8 activation has no unique committed r1 transaction")

    def restore_revision_seven(self, repo: pathlib.Path) -> None:
        current = load_json(repo / ".yuan/authority/current")
        revision_eight = load_json(
            repo
            / ".yuan/authority/records"
            / f"{current['record_sha256']}.json"
        )
        self.assertEqual(8, revision_eight["revision"])
        runtime_state.atomic_write(
            repo / ".yuan/authority/current",
            runtime_state.canonical(
                {
                    "schema_version": "yuan.authority-current/v1",
                    "record_sha256": revision_eight["previous_record_sha256"],
                }
            ),
            digest(repo / ".yuan/authority/current"),
        )
        runtime_state.atomic_write(
            repo / ".yuan-run/active-run.json",
            runtime_state.canonical(
                {
                    "schema_version": "yuan.active-run/v1",
                    "run_id": REVISION_SEVEN_RUN,
                    "runtime_root": f".yuan-run/runs/{REVISION_SEVEN_RUN}",
                    "manifest_sha256": REVISION_SEVEN_MANIFEST,
                }
            ),
            digest(repo / ".yuan-run/active-run.json"),
        )
        _, journal, _, _ = self.committed_r1(repo)
        for entry in journal["files"]:
            (repo / entry["path"]).write_bytes(
                (repo / entry["retained_blob"]).read_bytes()
            )
        (
            repo / ".yuan/authority/activation/yuan-core-0.1.json"
        ).write_bytes(
            (
                repo
                / ".yuan/authority/activation/history"
                / f"{REVISION_SEVEN_DESCRIPTOR}.blob"
            ).read_bytes()
        )
        self.assertEqual(7, authority.load_current(repo)["record"]["revision"])

    def test_protocol_and_manifest_state_one_unambiguous_or_rule(self) -> None:
        protocol = (ROOT / ".yuan/core/0.1/protocol.md").read_text(
            encoding="utf-8"
        ).lower()
        manifest = load_json(ROOT / ".yuan/core/0.1/candidate-manifest.json")
        expected = {
            "operator": "any_of",
            "accepted": ["previous-root-proof", "independent-proof"],
        }
        self.assertIn("explicit **any-of** semantics", protocol)
        self.assertIn(
            "previous immutable trust root **or** an independent held-out verifier",
            protocol,
        )
        self.assertIn(
            "candidate conformance, self-attestation,\n"
            "and an ambiguous or and-style proof list never activate core",
            protocol,
        )
        self.assertEqual(expected, manifest["activation"]["proof_policy"])
        self.assertNotIn("requires", manifest["activation"])
        self.assertTrue(activation.activation_policy_valid(manifest))
        invalid_policies = (
            {"requires": expected["accepted"]},
            {"proof_policy": {"operator": "all_of", "accepted": expected["accepted"]}},
            {"proof_policy": {"operator": "any_of", "accepted": []}},
            {"proof_policy": {"operator": "any_of", "accepted": ["unknown"]}},
            {
                "proof_policy": {
                    "operator": "any_of",
                    "accepted": ["previous-root-proof"],
                }
            },
        )
        for policy in invalid_policies:
            with self.subTest(policy=policy):
                candidate = copy.deepcopy(manifest)
                candidate["activation"] = {
                    "mode": "external-content-addressed-authority",
                    **policy,
                }
                self.assertFalse(activation.activation_policy_valid(candidate))
        self.assertEqual("inert-by-default", manifest["authority"])
        self.assertFalse(manifest["self_trust"])

    def test_prepared_proof_is_durable_and_predates_candidate_mutation(self) -> None:
        tx, journal, prepared, proof = self.committed_r1()
        receipt = ROOT / proof["receipt_path"]
        suite = ROOT / proof["suite_manifest_path"]
        verifier = ROOT / proof["verifier_path"]
        closure_path = ROOT / proof["closure_index_path"]
        closure = load_json(closure_path)
        full_candidate = ROOT / closure["full_candidate_manifest_path"]
        receipt_value = load_json(receipt)
        prepared_at = parsed_time(prepared["journal"][0]["recorded_at"])
        receipt_at = parsed_time(receipt_value["created_at"])
        expected_bindings = {
            "receipt_sha256": digest(receipt),
            "suite_manifest_sha256": digest(suite),
            "verifier_sha256": digest(verifier),
            "closure_index_sha256": digest(closure_path),
            "full_candidate_manifest_sha256": digest(full_candidate),
            "candidate_manifest_sha256": digest(
                ROOT / ".yuan/core/0.1/candidate-manifest.json"
            ),
            "receipt_created_at": receipt_value["created_at"],
            "transaction_id": tx.name,
        }
        for field, expected in expected_bindings.items():
            with self.subTest(field=field):
                self.assertEqual(expected, proof.get(field))
        self.assertEqual(digest(suite), receipt_value["manifest_sha256"])
        self.assertEqual(proof["receipt_path"], closure["receipt_path"])
        self.assertEqual(proof["suite_manifest_path"], closure["suite_manifest_path"])
        self.assertEqual(proof["verifier_path"], closure["verifier_path"])
        self.assertEqual(
            proof["candidate_manifest_sha256"],
            closure["candidate_manifest_sha256"],
        )
        self.assertEqual("previous-root-proof", closure["proof_route"])
        self.assertEqual(
            journal["prepared_attempt_sha256"], digest(tx / "attempt-prepared.json")
        )
        with self.subTest(field="causal_order"):
            self.assertLessEqual(
                receipt_at,
                prepared_at,
                "independent proof must exist before PREPARED authorizes mutation",
            )
        historical = revision_gate.verify_rev8_history(
            ROOT,
            mode=GATE_MODE,
            candidate_root=CANDIDATE_ROOT,
        )
        self.assertEqual(42, historical["full_candidate_entries"])
        self.assertEqual(
            (
                sorted(revision_gate.R2_REPLACED_PATHS)
                if GATE_MODE == "candidate"
                else []
            ),
            historical["candidate_differences"],
        )

    def test_evidence_cannot_predate_the_receipt_it_claims(self) -> None:
        transaction, journal, prepared, proof = self.committed_r1()
        active, _, _ = runtime_state.resolve_runtime_root(ROOT)
        work3_evidence = load_json(transaction / "evidence.json")
        work4_evidence = load_json(active / "evidence/0001.json")
        work4_receipt_path = next(
            path
            for path in (
                ROOT / ".yuan/authority/self-modification/evidence/work4"
            ).glob("*/receipt.json")
            if digest(path) == work4_evidence["logs"]["receipt_sha256"]
        )
        cases = (
            (
                "work3-r1",
                work3_evidence,
                ROOT / proof["receipt_path"],
            ),
            (
                "work4",
                work4_evidence,
                work4_receipt_path,
            ),
        )
        for name, evidence, receipt_path in cases:
            with self.subTest(work=name):
                receipt = load_json(receipt_path)
                self.assertEqual(
                    digest(receipt_path), evidence["logs"]["receipt_sha256"]
                )
                self.assertLessEqual(
                    parsed_time(receipt["created_at"]),
                    parsed_time(evidence["created_at"]),
                    "Evidence freshness cannot be earlier than its "
                    "independent receipt",
                )
                self.assertEqual(
                    receipt["created_at"], evidence["proof_receipt_created_at"]
                )
        committed_attempt = load_json(ROOT / journal["runtime_root"] / "attempts/0002.json")
        journal_times = [
            parsed_time(item["recorded_at"])
            for item in committed_attempt["journal"]
        ]
        self.assertEqual(journal_times, sorted(journal_times))
        self.assertLessEqual(
            parsed_time(proof["receipt_created_at"]),
            parsed_time(prepared["journal"][0]["recorded_at"]),
        )
        self.assertLessEqual(
            parsed_time(prepared["journal"][0]["recorded_at"]),
            next(
                parsed_time(item["recorded_at"])
                for item in committed_attempt["journal"]
                if item["state"] == "COMMITTED"
            ),
        )
        self.assertLessEqual(
            next(
                parsed_time(item["recorded_at"])
                for item in committed_attempt["journal"]
                if item["state"] == "COMMITTED"
            ),
            parsed_time(work3_evidence["created_at"]),
        )

    def test_work3_attempt_evidence_and_wait_auth_are_exactly_bound(self) -> None:
        _, tx, _, _ = self.committed_r1()
        runtime = ROOT / tx["runtime_root"]
        work = load_json(next((runtime / "contracts").glob("*.json")))
        attempt = load_json(runtime / "attempts/0002.json")
        evidence = load_json(runtime / "evidence/0002.json")
        memory = load_json(runtime / "run-memory.json")
        self.assertEqual("3", work["revision"]["revision"])
        self.assertEqual(2, attempt["sequence"])
        self.assertEqual(
            ["PREPARED", "EXECUTING", "OBSERVED", "COMMITTED"],
            [item["state"] for item in attempt["journal"]],
        )
        self.assertEqual("COMMITTED", attempt["side_effect_state"])
        self.assertTrue(attempt["postcondition"]["satisfied"])
        self.assertTrue(attempt["action"]["self_modification"]["proofs"])
        self.assertEqual(work["revision"], evidence["work_binding"])
        self.assertEqual(attempt["attempt_id"], evidence["source_attempt_id"])
        self.assertEqual("AC-M9-SELF-MODIFICATION-DOGFOOD", evidence["ac_id"])
        self.assertEqual(
            digest(ROOT / ".yuan/core/0.1/candidate-manifest.json"),
            evidence["artifact_binding"]["sha256"],
        )
        self.assertEqual(work["harness_binding"], evidence["harness_binding"])
        self.assertGreaterEqual(evidence["assertions"], 30)
        runtime_state.validate_runtime_evidence(
            ROOT, runtime, attempt, evidence
        )
        self.assertEqual("WAIT_AUTH", memory["last_result"])

    def test_work4_uses_fresh_execution_and_remains_wait_auth(self) -> None:
        active, _, _ = runtime_state.resolve_runtime_root(ROOT)
        work4 = load_json(next((active / "contracts").glob("*.json")))
        attempt4 = load_json(active / "attempts/0001.json")
        evidence4 = load_json(active / "evidence/0001.json")
        memory4 = load_json(active / "run-memory.json")
        _, committed, _, _ = self.committed_r1()
        work3_runtime = ROOT / committed["runtime_root"]
        evidence3 = load_json(work3_runtime / "evidence/0002.json")
        self.assertEqual("4", work4["revision"]["revision"])
        self.assertNotEqual(evidence3["evidence_id"], evidence4["evidence_id"])
        self.assertNotEqual(
            evidence3["source_attempt_id"], evidence4["source_attempt_id"]
        )
        self.assertNotEqual(
            evidence3["logs"]["receipt_sha256"],
            evidence4["logs"]["receipt_sha256"],
        )
        self.assertEqual(work4["revision"], evidence4["work_binding"])
        self.assertEqual(work4["protocol_binding"], attempt4["protocol_binding"])
        self.assertEqual(work4["protocol_binding"], memory4["protocol_binding"])
        self.assertEqual("0.1.1", work4["protocol_binding"]["revision"])
        self.assertEqual("WAIT_AUTH", memory4["last_result"])
        self.assertEqual(
            "AC-M9-LEGACY-TOMBSTONE-WAIT-AUTH",
            memory4["legal_next_steps"][0]["ac_id"],
        )

    def test_revisions_one_through_seven_are_frozen_and_eight_is_unique(self) -> None:
        current = load_json(ROOT / ".yuan/authority/current")
        record_sha = current["record_sha256"]
        history = []
        while record_sha:
            record = load_json(
                ROOT / ".yuan/authority/records" / f"{record_sha}.json"
            )
            self.assertEqual(record_sha, hashlib.sha256(
                authority.canonical(record)
            ).hexdigest())
            history.append((record_sha, record))
            record_sha = record["previous_record_sha256"]
        history.reverse()
        self.assertEqual(REVISION_HASHES, [item[0] for item in history])
        self.assertEqual(list(range(1, 9)), [
            item[1]["revision"] for item in history
        ])
        self.assertEqual(
            ["legacy", "core", "legacy", "core", "core", "core", "core", "core"],
            [item[1]["authority"] for item in history],
        )
        self.assertEqual(REVISION_HASHES[-2], history[-1][1][
            "previous_record_sha256"
        ])
        verified = authority.verify_authority(ROOT)
        self.assertEqual((8, 8), (
            verified["revision"], verified["history_length"]
        ))
        descriptor = load_json(
            ROOT / ".yuan/authority/activation/yuan-core-0.1.json"
        )
        self.assertEqual("legacy", descriptor["accepted_by_authority"])
        self.assertEqual(
            digest(ROOT / descriptor["older_root_verifier_path"]),
            descriptor["older_root_verifier_sha256"],
        )
        self.assertNotEqual(
            REVISION_HASHES[-2],
            descriptor["older_root_receipt_sha256"],
            "rev7 remains history continuity, not rev8's trust root",
        )
        revision_seven = ROOT / ".yuan-run/runs" / REVISION_SEVEN_RUN
        self.assertEqual(
            REVISION_SEVEN_MANIFEST,
            digest(revision_seven / "runtime-manifest.json"),
        )
        runtime_state.verify_runtime_at(ROOT, revision_seven)
        revision_six = ROOT / ".yuan-run/runs" / REVISION_SIX_RUN
        self.assertEqual(
            REVISION_SIX_MANIFEST,
            digest(revision_six / "runtime-manifest.json"),
        )
        runtime_state.verify_runtime_at(ROOT, revision_six)

    def test_bound_activation_artifacts_reject_post_hoc_tampering(self) -> None:
        descriptor = load_json(
            ROOT / ".yuan/authority/activation/yuan-core-0.1.json"
        )
        targets = {
            ".yuan/core/0.1/protocol.md",
            ".yuan/core/0.1/candidate-manifest.json",
            ".yuan/authority/activation/yuan-core-0.1.json",
            descriptor["independent_evidence_path"],
            descriptor["activated_older_root_manifest_path"],
            descriptor["proof_closure_index_path"],
            next(
                item["verifier_path"]
                for item in [
                    load_json(ROOT / descriptor["proof_closure_index_path"])
                ]
            ),
        }
        with tempfile.TemporaryDirectory(prefix="yuan-m9-held-tamper-") as name:
            repo = pathlib.Path(name)
            self.copy_runtime_repo(repo)
            for relative in targets:
                with self.subTest(relative=relative):
                    path = repo / relative
                    original = path.read_bytes()
                    path.write_bytes(original + b"\n")
                    with self.assertRaises(
                        (authority.AuthorityError, revision_gate.GateError)
                    ):
                        if GATE_MODE == "candidate":
                            authority.verify_authority(repo)
                        else:
                            revision_gate.verify_rev8_history(
                                repo, mode="active"
                            )
                    path.write_bytes(original)
                    if GATE_MODE == "candidate":
                        self.assertEqual(
                            8, authority.verify_authority(repo)["revision"]
                        )
                    else:
                        self.assertEqual(
                            revision_gate.REV8_RECORD_SHA256,
                            revision_gate.verify_rev8_history(
                                repo, mode="active"
                            )["record_sha256"],
                        )

    def test_full_candidate_closure_rejects_replace_and_delete(self) -> None:
        descriptor = load_json(
            ROOT / ".yuan/authority/activation/yuan-core-0.1.json"
        )
        closure = load_json(ROOT / descriptor["proof_closure_index_path"])
        relative = closure["full_candidate_manifest_path"]
        with tempfile.TemporaryDirectory(prefix="yuan-m9-held-full-") as name:
            repo = pathlib.Path(name)
            self.copy_runtime_repo(repo)
            path = repo / relative
            original = path.read_bytes()
            for attack in ("replace", "delete"):
                with self.subTest(attack=attack, verifier="authority"):
                    if attack == "replace":
                        path.write_bytes(original + b"\n")
                    else:
                        path.unlink()
                    try:
                        with self.assertRaises(
                            (authority.AuthorityError, revision_gate.GateError)
                        ):
                            if GATE_MODE == "candidate":
                                authority.verify_authority(repo)
                            else:
                                revision_gate.verify_rev8_history(
                                    repo, mode="active"
                                )
                    finally:
                        path.write_bytes(original)
                with self.subTest(attack=attack, verifier="runtime"):
                    if attack == "replace":
                        path.write_bytes(original + b"\n")
                    else:
                        path.unlink()
                    try:
                        active, _, _ = runtime_state.resolve_runtime_root(repo)
                        attempt = load_json(active / "attempts/0001.json")
                        evidence = load_json(active / "evidence/0001.json")
                        with self.assertRaises(
                            (authority.AuthorityError, revision_gate.GateError)
                        ):
                            if GATE_MODE == "candidate":
                                runtime_state.validate_runtime_evidence(
                                    repo, active, attempt, evidence
                                )
                            else:
                                revision_gate.verify_rev8_history(
                                    repo, mode="active"
                                )
                    finally:
                        path.write_bytes(original)

    def test_wrong_root_and_candidate_proofs_are_rejected_pre_mutation(self) -> None:
        for attack in (
            "missing-receipt",
            "future-receipt",
            "replace-suite",
            "replace-candidate",
            "wrong-root",
            "wrong-candidate",
        ):
            with self.subTest(attack=attack), tempfile.TemporaryDirectory(
                prefix=f"yuan-m9-held-{attack}-"
            ) as name:
                repo = pathlib.Path(name)
                self.copy_runtime_repo(repo)
                self.restore_revision_seven(repo)
                before = (
                    digest(repo / ".yuan/core/0.1/protocol.md"),
                    digest(repo / ".yuan/core/0.1/candidate-manifest.json"),
                    digest(repo / ".yuan/authority/current"),
                    digest(repo / ".yuan-run/active-run.json"),
                )
                with self.assertRaises(authority.AuthorityError):
                    m9.install(repo, proof_attack=attack, candidate_root=ROOT)
                self.assertEqual(before, (
                    digest(repo / ".yuan/core/0.1/protocol.md"),
                    digest(repo / ".yuan/core/0.1/candidate-manifest.json"),
                    digest(repo / ".yuan/authority/current"),
                    digest(repo / ".yuan-run/active-run.json"),
                ))
                self.assertEqual(
                    7, authority.load_current(repo)["record"]["revision"]
                )

    def test_protocol_crash_blocks_and_rollback_is_idempotent(self) -> None:
        with tempfile.TemporaryDirectory(prefix="yuan-m9-held-protocol-") as name:
            repo = pathlib.Path(name)
            self.copy_runtime_repo(repo)
            before = (
                digest(repo / ".yuan/core/0.1/protocol.md"),
                digest(repo / ".yuan/core/0.1/candidate-manifest.json"),
            )
            transaction_id = (
                "2a396d6ea6187e0144e0883aa4db2581c2217eb4f832c091181fc6e13a37c989"
            )
            first = m9.recover_mutation(repo, transaction_id)
            second = m9.recover_mutation(repo, transaction_id)
            self.assertEqual(first, second)
            self.assertEqual("ROLLED_BACK", first["state"])
            self.assertEqual(before, (
                digest(repo / ".yuan/core/0.1/protocol.md"),
                digest(repo / ".yuan/core/0.1/candidate-manifest.json"),
            ))
            self.assertEqual(8, authority.verify_authority(repo)["revision"])

    def test_two_pointer_crash_blocks_and_recovery_is_idempotent(self) -> None:
        with tempfile.TemporaryDirectory(prefix="yuan-m9-held-pointers-") as name:
            repo = pathlib.Path(name)
            self.copy_runtime_repo(repo)
            transaction_id = (
                "743e0ba65eefe77be90ad03308b3407bcb0d5c111953a9a2dc18af278fbb8123"
            )
            first = runtime_transaction.recover_runtime_transaction(
                repo, transaction_id
            )
            second = runtime_transaction.recover_runtime_transaction(
                repo, transaction_id
            )
            self.assertEqual(first, second)
            self.assertEqual("COMMITTED", first["state"])
            verified = authority.verify_authority(repo)
            self.assertEqual((8, 8), (
                verified["revision"], verified["history_length"]
            ))

    def test_tombstone_has_no_grant_and_legacy_writes_are_rejected(self) -> None:
        runtime, _, _ = runtime_state.resolve_runtime_root(ROOT)
        work = load_json(next((runtime / "contracts").glob("*.json")))
        memory = load_json(runtime / "run-memory.json")
        tombstone = next(
            item
            for item in work["acceptance_criteria"]
            if item["id"] == "AC-M9-LEGACY-TOMBSTONE-WAIT-AUTH"
        )
        self.assertEqual("human-judgment", tombstone["type"])
        self.assertFalse(any(
            "docs" in grant["scopes"]
            for grant in work["authorization"]["grants"]
        ))
        self.assertEqual("WAIT_AUTH", memory["last_result"])
        self.assertIsNone(
            memory["legal_next_steps"][0]["authorization_grant_id"]
        )
        with self.assertRaisesRegex(authority.AuthorityError, "inactive"):
            authority.assert_write_allowed(
                ROOT,
                "legacy",
                "docs/PROGRESS.md",
                digest(ROOT / "docs/PROGRESS.md"),
            )
        with self.assertRaises(authority.AuthorityError):
            authority.assert_write_allowed(
                ROOT,
                "core",
                "docs/PROGRESS.md",
                digest(ROOT / "docs/PROGRESS.md"),
            )

    def test_public_dogfood_verifier_accepts_rev8_work4(self) -> None:
        if GATE_MODE == "candidate":
            verified = m9.verify_dogfood(ROOT)
            self.assertEqual(8, verified["authority"]["revision"])
            self.assertEqual("4", verified["work"]["revision"]["revision"])
        else:
            verified = revision_gate.verify_pointer_driven_rev8(ROOT)
            self.assertEqual(8, verified["authority_revision"])
            self.assertEqual("4", verified["work_revision"])

    def test_failed_promotion_journals_are_recoverable(self) -> None:
        failures = list(
            (
                ROOT / ".yuan/authority/self-modification/failures"
            ).glob("*.json")
        )
        self.assertTrue(failures)
        promotion_failure = next(
            load_json(path)
            for path in failures
            if load_json(path).get("transaction_id")
            == "262321e82c8950c3ea2b52b093e3591e8909c064b1f187959f5cda8a84c16b56"
        )
        self.assertEqual("FAILED", promotion_failure["promotion_state"])
        self.assertEqual("COMMITTED", promotion_failure["mutation_state"])
        self.assertFalse(promotion_failure["trusted"])
        failed_tx = load_json(
            ROOT
            / ".yuan/authority/self-modification/transactions"
            / promotion_failure["transaction_id"]
            / "journal.json"
        )
        self.assertEqual("COMMITTED", failed_tx["state"])
        self.assertEqual(
            "ROLLED_BACK_TO_REVISION_7",
            promotion_failure["compensation"]["state"],
        )
        self.assertEqual("PASS", promotion_failure["compensation"]["authority_after"])
        self.assertEqual("FORBIDDEN", promotion_failure["promotion"])

    def test_revision_gate_modes_are_explicit_and_confusion_fails(self) -> None:
        staging = (
            ROOT
            / ".yuan/authority/self-modification/staging"
            / "task-012-r2/candidate"
        )
        with self.assertRaises(revision_gate.GateError):
            revision_gate.gate_configuration(
                ROOT, mode="active", candidate_root=staging
            )
        with self.assertRaises(revision_gate.GateError):
            revision_gate.gate_configuration(
                ROOT, mode="candidate", candidate_root=None
            )
        with self.assertRaises(revision_gate.GateError):
            revision_gate.gate_configuration(
                ROOT, mode="candidate", candidate_root=ROOT
            )
        with self.assertRaises(revision_gate.GateError):
            revision_gate.gate_configuration(
                ROOT, mode="unknown", candidate_root=None
            )

    def test_rev8_archive_manifest_and_blobs_fail_closed(self) -> None:
        bundle_root = (
            ".yuan/authority/validator-bundles/"
            f"{revision_gate.REV8_VALIDATOR_BUNDLE_SHA256}"
        )
        manifest = (
            f"{bundle_root}/"
            f"{revision_gate.REV8_VALIDATOR_BUNDLE_SHA256}.manifest.json"
        )
        bundle = revision_gate.verify_validator_bundle(ROOT)
        targets = [manifest, *(path.relative_to(ROOT).as_posix() for path in bundle.values())]
        with tempfile.TemporaryDirectory(prefix="yuan-m9-held-archive-") as name:
            repo = pathlib.Path(name)
            self.copy_runtime_repo(repo)
            candidate = self.validation_root_in(repo)
            for relative in targets:
                for attack in ("replace", "delete"):
                    with self.subTest(relative=relative, attack=attack):
                        path = repo / relative
                        original = path.read_bytes()
                        if attack == "replace":
                            path.write_bytes(original + b"\n")
                        else:
                            path.unlink()
                        try:
                            with self.assertRaises(revision_gate.GateError):
                                revision_gate.verify_rev8_history(
                                    repo,
                                    mode=GATE_MODE,
                                    candidate_root=(
                                        candidate
                                        if GATE_MODE == "candidate"
                                        else None
                                    ),
                                )
                        finally:
                            path.write_bytes(original)

    def test_mode_specific_candidate_closure_is_complete_and_fail_closed(
        self,
    ) -> None:
        if GATE_MODE == "active":
            result = revision_gate.verify_rev8_history(ROOT, mode="active")
            self.assertEqual([], result["candidate_differences"])
            self.assertEqual(42, result["full_candidate_entries"])
            return
        with tempfile.TemporaryDirectory(prefix="yuan-m9-held-r2-") as name:
            repo = pathlib.Path(name)
            self.copy_runtime_repo(repo)
            candidate = self.validation_root_in(repo)
            arguments, artifacts = revision_gate.build_candidate_closure(
                repo,
                candidate,
                repo / "tests/authority_switch/test_m9_held_out.py",
            )
            revision_gate.assert_candidate_matches_full_manifest(
                candidate, artifacts["full"]
            )
            revision_gate.verify_candidate_validator_bundle(
                repo,
                candidate,
                artifacts["full"],
                arguments["candidate_manifest_sha256"],
            )
            verified = activation.verify_preflight_closure(repo, **arguments)
            self.assertEqual(
                "yuan.preflight-proof-closure/v2",
                verified["schema_version"],
            )
            self.assertEqual(55, len(artifacts["full"]["files"]))
            for label in (
                "index_path",
                "receipt_path",
                "suite_path",
                "verifier_path",
                "full_path",
                "prepared_path",
            ):
                path = artifacts[label]
                original = path.read_bytes()
                for attack in ("replace", "delete"):
                    with self.subTest(label=label, attack=attack):
                        if attack == "replace":
                            path.write_bytes(original + b"\n")
                        else:
                            path.unlink()
                        try:
                            with self.assertRaises(authority.AuthorityError):
                                activation.verify_preflight_closure(
                                    repo, **arguments
                                )
                        finally:
                            path.write_bytes(original)
            candidate_bundle_targets = [
                artifacts["bundle_path"],
                *(
                    artifacts["bundle_path"].parent
                    / f"{entry['sha256']}.blob"
                    for entry in artifacts["bundle"]["files"]
                ),
            ]
            for path in candidate_bundle_targets:
                original = path.read_bytes()
                for attack in ("replace", "delete"):
                    with self.subTest(
                        label="candidate-bundle",
                        path=path.name,
                        attack=attack,
                    ):
                        if attack == "replace":
                            path.write_bytes(original + b"\n")
                        else:
                            path.unlink()
                        try:
                            with self.assertRaises(revision_gate.GateError):
                                revision_gate.verify_candidate_validator_bundle(
                                    repo,
                                    candidate,
                                    artifacts["full"],
                                    arguments["candidate_manifest_sha256"],
                                )
                        finally:
                            path.write_bytes(original)
            for missing in (
                "archived_bundle_manifest_path",
                "archived_bundle_manifest_sha256",
            ):
                confused = dict(arguments)
                confused[missing] = None
                with self.subTest(label="archive-binding-pair", missing=missing):
                    with self.assertRaises(authority.AuthorityError):
                        activation.verify_preflight_closure(repo, **confused)
            archived_blob = next(
                iter(revision_gate.verify_validator_bundle(repo).values())
            )
            original_blob = archived_blob.read_bytes()
            archived_blob.unlink()
            try:
                with self.assertRaises(authority.AuthorityError):
                    activation.verify_preflight_closure(repo, **arguments)
            finally:
                archived_blob.write_bytes(original_blob)
            changed = candidate / "scripts/yuan_activation.py"
            original_candidate = changed.read_bytes()
            changed.write_bytes(original_candidate + b"\n")
            try:
                with self.assertRaises(revision_gate.GateError):
                    revision_gate.assert_candidate_matches_full_manifest(
                        candidate, artifacts["full"]
                    )
                with self.assertRaises(authority.AuthorityError):
                    activation.verify_preflight_closure(repo, **arguments)
            finally:
                changed.write_bytes(original_candidate)

    def test_m7_registry_and_all_four_deltas_remain_frozen(self) -> None:
        receipt = provenance.verify_frozen_and_delta(ROOT)
        self.assertEqual(
            "4e8d974409bf0ad2bd66df17039c8dee12b6fca03a0e2860ed5ac865615823d4",
            receipt["registry_sha256"],
        )
        self.assertEqual(9, receipt["delta_assertions"])
        self.assertEqual(18, receipt["r2_delta_assertions"])
        self.assertEqual(10, receipt["m9_delta_assertions"])
        self.assertEqual(22, receipt["r1_fix_delta_assertions"])

    def test_original_dirty_bytes_remain_protected(self) -> None:
        tracked = {}
        for row in (
            ROOT
            / "docs/20260726-yuan-core-01-upgrade/evidence/m0a/tracked-dirty.tsv"
        ).read_text(encoding="utf-8").splitlines()[1:]:
            path, expected, *_ = row.split("\t")
            tracked[path] = expected
        untracked = {}
        for row in (
            ROOT
            / "docs/20260726-yuan-core-01-upgrade/evidence/m0a/untracked-files.tsv"
        ).read_text(encoding="utf-8").splitlines()[1:]:
            path, expected, *_ = row.split("\t")
            untracked[path] = expected
        for path, expected in {**tracked, **untracked}.items():
            if path == "AGENTS.md":
                # The desktop injects the active repository instructions into
                # this file; the original bytes remain retained by M7.
                continue
            self.assertEqual(expected, digest(ROOT / path), path)


if __name__ == "__main__":
    unittest.main()
