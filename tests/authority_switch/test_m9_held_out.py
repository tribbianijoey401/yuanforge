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
import pathlib
import shutil
import sys
import tempfile
import unittest


ROOT = pathlib.Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

import yuan_authority as authority
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
]
REVISION_SIX_RUN = "WORK-yuan-m8-m9-successor-r2-398b8aefe078"
REVISION_SIX_MANIFEST = (
    "e2bc36fc5d0213912e46073bf4ca2a8aa52091311e7870e34c1f1987a3b64abe"
)
R2_PROTOCOL = "b61422bd4f76033234908fb89c149cccc0ebffd5b502e21eea5e26cd82a9c3c3"
R2_CANDIDATE = "57a2acad6ba92d879785139e35548bdd20cd1edcafa3d7e8b554321504ec8b5e"
R2_DESCRIPTOR = "6f08c7e10bcd433e2341471bef463e0d37fe6b6c7356f400988868a1b129afe8"


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

    def restore_revision_six(self, repo: pathlib.Path) -> None:
        current = load_json(repo / ".yuan/authority/current")
        revision_seven = load_json(
            repo
            / ".yuan/authority/records"
            / f"{current['record_sha256']}.json"
        )
        self.assertEqual(7, revision_seven["revision"])
        runtime_state.atomic_write(
            repo / ".yuan/authority/current",
            runtime_state.canonical(
                {
                    "schema_version": "yuan.authority-current/v1",
                    "record_sha256": revision_seven["previous_record_sha256"],
                }
            ),
            digest(repo / ".yuan/authority/current"),
        )
        runtime_state.atomic_write(
            repo / ".yuan-run/active-run.json",
            runtime_state.canonical(
                {
                    "schema_version": "yuan.active-run/v1",
                    "run_id": REVISION_SIX_RUN,
                    "runtime_root": f".yuan-run/runs/{REVISION_SIX_RUN}",
                    "manifest_sha256": REVISION_SIX_MANIFEST,
                }
            ),
            digest(repo / ".yuan-run/active-run.json"),
        )
        history = repo / ".yuan/authority/core-history/r2-to-m9/blobs"
        (repo / ".yuan/core/0.1/protocol.md").write_bytes(
            (history / f"{R2_PROTOCOL}.blob").read_bytes()
        )
        (repo / ".yuan/core/0.1/candidate-manifest.json").write_bytes(
            (history / f"{R2_CANDIDATE}.blob").read_bytes()
        )
        (
            repo / ".yuan/authority/activation/yuan-core-0.1.json"
        ).write_bytes(
            (
                repo
                / ".yuan/authority/activation/history"
                / f"{R2_DESCRIPTOR}.blob"
            ).read_bytes()
        )
        for run in (
            "WORK-yuan-m8-m9-successor-g0002-80c48920a4b0",
            "WORK-yuan-m8-m9-successor-r3-24820e1e41b7",
        ):
            shutil.rmtree(repo / ".yuan-run/runs" / run, ignore_errors=True)
        shutil.rmtree(
            repo / ".yuan/authority/self-modification", ignore_errors=True
        )
        (
            repo
            / ".yuan/authority/transactions"
            / "c62e75b40584a24de0eadd1beb64d3747735c70d6b3a069836717cd7da99878f.json"
        ).unlink(missing_ok=True)
        self.assertEqual(6, authority.verify_authority(repo)["revision"])

    def test_protocol_and_manifest_state_one_unambiguous_or_rule(self) -> None:
        protocol = (ROOT / ".yuan/core/0.1/protocol.md").read_text(
            encoding="utf-8"
        ).lower()
        manifest = load_json(ROOT / ".yuan/core/0.1/candidate-manifest.json")
        requires = manifest["activation"]["requires"]
        protocol_is_or = (
            "previous-root or independent evidence" in protocol
            and "candidate conformance and\nself-attestation never activate core"
            in protocol
        )
        manifest_is_or = (
            isinstance(requires, dict)
            and str(requires.get("operator", "or")).lower() in {"or", "any-of"}
            and set(requires.get("any_of", []))
            == {"previous-root-proof", "independent-proof"}
        )
        self.assertTrue(protocol_is_or, "protocol must retain explicit OR semantics")
        self.assertTrue(
            manifest_is_or,
            "manifest activation.requires must encode the same OR rule explicitly; "
            "a two-item required list conventionally means AND",
        )
        self.assertEqual("inert-by-default", manifest["authority"])
        self.assertFalse(manifest["self_trust"])

    def test_prepared_proof_is_durable_and_predates_candidate_mutation(self) -> None:
        tx_root = ROOT / ".yuan/authority/self-modification/transactions"
        tx = next(path for path in tx_root.iterdir() if path.is_dir())
        prepared = load_json(tx / "attempt-prepared.json")
        proof = prepared["action"]["self_modification"]["proofs"][0]
        receipt = (
            ROOT
            / ".yuan/authority/self-modification/evidence/old-root-receipt-m9.json"
        )
        suite = (
            ROOT
            / ".yuan/authority/self-modification/evidence/old-root-manifest-m9.json"
        )
        receipt_value = load_json(receipt)
        prepared_at = parsed_time(prepared["journal"][0]["recorded_at"])
        receipt_at = parsed_time(receipt_value["created_at"])
        expected_bindings = {
            "receipt_sha256": digest(receipt),
            "manifest_sha256": digest(suite),
            "created_at": receipt_value["created_at"],
        }
        for field, expected in expected_bindings.items():
            with self.subTest(field=field):
                self.assertEqual(expected, proof.get(field))
        with self.subTest(field="causal_order"):
            self.assertLessEqual(
                receipt_at,
                prepared_at,
                "independent proof must exist before PREPARED authorizes mutation",
            )
        self.assertEqual(digest(suite), receipt_value["manifest_sha256"])

    def test_evidence_cannot_predate_the_receipt_it_claims(self) -> None:
        transaction = next(
            path
            for path in (
                ROOT / ".yuan/authority/self-modification/transactions"
            ).iterdir()
            if path.is_dir()
        )
        active, _, _ = runtime_state.resolve_runtime_root(ROOT)
        cases = (
            (
                "work2",
                load_json(transaction / "evidence.json"),
                ROOT
                / ".yuan/authority/self-modification/evidence"
                / "old-root-receipt-m9.json",
            ),
            (
                "work3",
                load_json(active / "evidence/0001.json"),
                ROOT
                / ".yuan/authority/self-modification/evidence"
                / "old-root-receipt-m9-work3.json",
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

    def test_work2_attempt_evidence_and_wait_auth_are_exactly_bound(self) -> None:
        tx = next(
            load_json(path)
            for path in (
                ROOT
                / ".yuan/authority/self-modification/transactions"
            ).glob("*/journal.json")
            if load_json(path).get("state") == "COMMITTED"
        )
        runtime = ROOT / tx["runtime_root"]
        work = load_json(next((runtime / "contracts").glob("*.json")))
        attempt = load_json(runtime / "attempts/0002.json")
        evidence = load_json(runtime / "evidence/0002.json")
        memory = load_json(runtime / "run-memory.json")
        self.assertEqual("2", work["revision"]["revision"])
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

    def test_work3_uses_fresh_execution_and_remains_wait_auth(self) -> None:
        active, _, _ = runtime_state.resolve_runtime_root(ROOT)
        work3 = load_json(next((active / "contracts").glob("*.json")))
        attempt3 = load_json(active / "attempts/0001.json")
        evidence3 = load_json(active / "evidence/0001.json")
        memory3 = load_json(active / "run-memory.json")
        committed = next(
            load_json(path)
            for path in (
                ROOT / ".yuan/authority/self-modification/transactions"
            ).glob("*/journal.json")
            if load_json(path).get("state") == "COMMITTED"
        )
        work2_runtime = ROOT / committed["runtime_root"]
        evidence2 = load_json(work2_runtime / "evidence/0002.json")
        self.assertEqual("3", work3["revision"]["revision"])
        self.assertNotEqual(evidence2["evidence_id"], evidence3["evidence_id"])
        self.assertNotEqual(
            evidence2["source_attempt_id"], evidence3["source_attempt_id"]
        )
        self.assertNotEqual(
            evidence2["logs"]["receipt_sha256"],
            evidence3["logs"]["receipt_sha256"],
        )
        self.assertEqual(work3["revision"], evidence3["work_binding"])
        self.assertEqual(work3["protocol_binding"], attempt3["protocol_binding"])
        self.assertEqual(work3["protocol_binding"], memory3["protocol_binding"])
        self.assertEqual("WAIT_AUTH", memory3["last_result"])
        self.assertEqual(
            "AC-M9-LEGACY-TOMBSTONE-WAIT-AUTH",
            memory3["legal_next_steps"][0]["ac_id"],
        )

    def test_revisions_one_through_six_are_frozen_and_seven_is_unique(self) -> None:
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
        self.assertEqual(list(range(1, 8)), [
            item[1]["revision"] for item in history
        ])
        self.assertEqual(
            ["legacy", "core", "legacy", "core", "core", "core", "core"],
            [item[1]["authority"] for item in history],
        )
        self.assertEqual(REVISION_HASHES[-2], history[-1][1][
            "previous_record_sha256"
        ])
        verified = authority.verify_authority(ROOT)
        self.assertEqual((7, 7), (
            verified["revision"], verified["history_length"]
        ))
        revision_six = ROOT / ".yuan-run/runs" / REVISION_SIX_RUN
        self.assertEqual(
            REVISION_SIX_MANIFEST,
            digest(revision_six / "runtime-manifest.json"),
        )
        runtime_state.verify_runtime_at(ROOT, revision_six)

    def test_bound_activation_artifacts_reject_post_hoc_tampering(self) -> None:
        targets = (
            ".yuan/core/0.1/protocol.md",
            ".yuan/core/0.1/candidate-manifest.json",
            ".yuan/authority/activation/yuan-core-0.1.json",
            ".yuan/authority/self-modification/evidence/old-root-manifest-m9.json",
            ".yuan/authority/self-modification/evidence/old-root-receipt-m9.json",
        )
        with tempfile.TemporaryDirectory(prefix="yuan-m9-held-tamper-") as name:
            repo = pathlib.Path(name)
            self.copy_runtime_repo(repo)
            for relative in targets:
                with self.subTest(relative=relative):
                    path = repo / relative
                    original = path.read_bytes()
                    path.write_bytes(original + b"\n")
                    with self.assertRaises(authority.AuthorityError):
                        authority.verify_authority(repo)
                    path.write_bytes(original)
                    self.assertEqual(7, authority.verify_authority(repo)["revision"])

    def test_wrong_root_and_candidate_proofs_are_rejected_pre_mutation(self) -> None:
        for attack in ("wrong-root", "wrong-candidate"):
            with self.subTest(attack=attack), tempfile.TemporaryDirectory(
                prefix=f"yuan-m9-held-{attack}-"
            ) as name:
                repo = pathlib.Path(name)
                self.copy_runtime_repo(repo)
                self.restore_revision_six(repo)
                before = (
                    digest(repo / ".yuan/core/0.1/protocol.md"),
                    digest(repo / ".yuan/core/0.1/candidate-manifest.json"),
                )
                with self.assertRaises(authority.AuthorityError):
                    m9.install(repo, proof_attack=attack)
                self.assertEqual(before, (
                    digest(repo / ".yuan/core/0.1/protocol.md"),
                    digest(repo / ".yuan/core/0.1/candidate-manifest.json"),
                ))
                self.assertEqual(6, authority.verify_authority(repo)["revision"])

    def test_protocol_crash_blocks_and_rollback_is_idempotent(self) -> None:
        with tempfile.TemporaryDirectory(prefix="yuan-m9-held-protocol-") as name:
            repo = pathlib.Path(name)
            self.copy_runtime_repo(repo)
            self.restore_revision_six(repo)
            before = (
                digest(repo / ".yuan/core/0.1/protocol.md"),
                digest(repo / ".yuan/core/0.1/candidate-manifest.json"),
            )
            with self.assertRaises(m9.MutationCrash) as caught:
                m9.install(repo, mutation_failure_after="protocol")
            with self.assertRaises(authority.AuthorityError):
                authority.verify_authority(repo)
            first = m9.recover_mutation(repo, caught.exception.transaction_id)
            second = m9.recover_mutation(repo, caught.exception.transaction_id)
            self.assertEqual(first, second)
            self.assertEqual("ROLLED_BACK", first["state"])
            self.assertEqual(before, (
                digest(repo / ".yuan/core/0.1/protocol.md"),
                digest(repo / ".yuan/core/0.1/candidate-manifest.json"),
            ))
            self.assertEqual(6, authority.verify_authority(repo)["revision"])

    def test_two_pointer_crash_blocks_and_recovery_is_idempotent(self) -> None:
        with tempfile.TemporaryDirectory(prefix="yuan-m9-held-pointers-") as name:
            repo = pathlib.Path(name)
            self.copy_runtime_repo(repo)
            self.restore_revision_six(repo)
            with self.assertRaises(runtime_transaction.InjectedCrash) as caught:
                m9.install(repo, failure_after="active-pointer")
            with self.assertRaises(authority.AuthorityError):
                authority.verify_authority(repo)
            first = runtime_transaction.recover_runtime_transaction(
                repo, caught.exception.transaction_id
            )
            second = runtime_transaction.recover_runtime_transaction(
                repo, caught.exception.transaction_id
            )
            self.assertEqual(first, second)
            self.assertEqual("COMMITTED", first["state"])
            verified = authority.verify_authority(repo)
            self.assertEqual((7, 7), (
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

    def test_m7_registry_and_all_three_deltas_remain_frozen(self) -> None:
        receipt = provenance.verify_frozen_and_delta(ROOT)
        self.assertEqual(
            "4e8d974409bf0ad2bd66df17039c8dee12b6fca03a0e2860ed5ac865615823d4",
            receipt["registry_sha256"],
        )
        self.assertEqual(9, receipt["delta_assertions"])
        self.assertEqual(18, receipt["r2_delta_assertions"])
        self.assertEqual(10, receipt["m9_delta_assertions"])

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
