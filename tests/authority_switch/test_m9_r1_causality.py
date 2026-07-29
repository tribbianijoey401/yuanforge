"""Author-side regression tests for task-012-r1 causal proof closure.

The independent ``test_m9_held_out.py`` remains untouched and is the final
Hard Gate.  These tests only encode the public blockers that it disclosed.
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
CANDIDATE = ROOT
sys.path.insert(0, str(CANDIDATE / "scripts"))
sys.path.insert(0, str(CANDIDATE / ".yuan/core/0.1"))

import yuan_activation as activation
import yuan_m9_dogfood as m9
from completion_semantics import evidence_satisfies_ac
from trust_semantics import self_modification_authorized


def digest_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def load(path: pathlib.Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


class M9R1Causality(unittest.TestCase):
    def restore_revision_seven(self, repo: pathlib.Path) -> None:
        current = load(repo / ".yuan/authority/current")
        revision_eight = load(
            repo
            / ".yuan/authority/records"
            / f"{current['record_sha256']}.json"
        )
        (repo / ".yuan/authority/current").write_text(
            json.dumps(
                {
                    "schema_version": "yuan.authority-current/v1",
                    "record_sha256": revision_eight[
                        "previous_record_sha256"
                    ],
                },
                sort_keys=True,
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        active = {
            "schema_version": "yuan.active-run/v1",
            "run_id": "WORK-yuan-m8-m9-successor-r3-24820e1e41b7",
            "runtime_root": (
                ".yuan-run/runs/"
                "WORK-yuan-m8-m9-successor-r3-24820e1e41b7"
            ),
            "manifest_sha256": (
                "a135a77f8b6dddad29554e9145c79b8fe689ba1932bc44eea02c48a0940c1447"
            ),
        }
        (repo / ".yuan-run/active-run.json").write_text(
            json.dumps(active, sort_keys=True, indent=2) + "\n",
            encoding="utf-8",
        )
        tx = load(
            repo
            / ".yuan/authority/self-modification/transactions"
            / (
                "f38bd069cb0889403a29285dae70ba5b330d40d4e1e859659d4d79a8d8c3b303"
            )
            / "journal.json"
        )
        for entry in tx["files"]:
            (repo / entry["path"]).write_bytes(
                (repo / entry["retained_blob"]).read_bytes()
            )
        descriptor = (
            repo
            / ".yuan/authority/activation/history"
            / (
                "f6e35cfafc8dc50aa743dece471b1b4c5b40aa7467c6d8e79f391b9666d7143d.blob"
            )
        )
        (
            repo / ".yuan/authority/activation/yuan-core-0.1.json"
        ).write_bytes(descriptor.read_bytes())

    def test_manifest_uses_exact_any_of_policy_and_rejects_legacy_forms(self) -> None:
        candidate = load(CANDIDATE / ".yuan/core/0.1/candidate-manifest.json")
        self.assertEqual(
            {
                "operator": "any_of",
                "accepted": ["previous-root-proof", "independent-proof"],
            },
            candidate["activation"]["proof_policy"],
        )
        self.assertNotIn("requires", candidate["activation"])
        self.assertEqual("yuan.core.protocol/0.1.1", candidate["protocol_revision"])
        self.assertEqual("yuan.core/0.1.1", candidate["candidate_revision"])
        for invalid in (
            {"requires": ["previous-root-proof", "independent-proof"]},
            {"operator": "all_of", "accepted": ["previous-root-proof"]},
            {"operator": "any_of", "accepted": []},
            {"operator": "any_of", "accepted": ["unknown-proof"]},
        ):
            with self.subTest(invalid=invalid):
                value = copy.deepcopy(candidate)
                value["activation"]["proof_policy"] = invalid
                self.assertFalse(activation.activation_policy_valid(value))

    def test_previous_root_proof_requires_complete_causal_closure(self) -> None:
        now = dt.datetime.now(dt.timezone.utc)
        previous = {"id": "root", "revision": "1", "sha256": "1" * 64}
        candidate = {"id": "core", "revision": "0.1.1", "sha256": "2" * 64}
        proof = {
            "kind": "previous-root",
            "root_binding": previous,
            "candidate_binding": candidate,
            "status": "PASS",
            "assertions": 30,
            "receipt_sha256": "3" * 64,
            "suite_manifest_sha256": "4" * 64,
            "candidate_manifest_sha256": candidate["sha256"],
            "verifier_sha256": "5" * 64,
            "receipt_created_at": (now - dt.timedelta(seconds=2)).isoformat(),
        }
        change = {
            "target_kind": "core",
            "previous_binding": previous,
            "candidate_binding": candidate,
            "risk": "R0",
        }
        self.assertTrue(
            self_modification_authorized(
                change,
                [proof],
                now=now,
                prepared_at=(now - dt.timedelta(seconds=1)).isoformat(),
            )
        )
        for field in (
            "receipt_sha256",
            "suite_manifest_sha256",
            "candidate_manifest_sha256",
            "verifier_sha256",
            "receipt_created_at",
        ):
            attacked = copy.deepcopy(proof)
            attacked.pop(field)
            with self.subTest(missing=field):
                self.assertFalse(
                    self_modification_authorized(
                        change,
                        [attacked],
                        now=now,
                        prepared_at=now.isoformat(),
                    )
                )
        future = copy.deepcopy(proof)
        future["receipt_created_at"] = (now + dt.timedelta(seconds=1)).isoformat()
        self.assertFalse(
            self_modification_authorized(
                change, [future], now=now, prepared_at=now.isoformat()
            )
        )

    def test_evidence_requires_receipt_then_commit_then_evidence_order(self) -> None:
        active = ROOT / load(ROOT / ".yuan-run/active-run.json")["runtime_root"]
        work = load(next((active / "contracts").glob("*.json")))
        work["protocol_binding"]["revision"] = "0.1.1"
        attempt = load(active / "attempts/0001.json")
        attempt["protocol_binding"] = copy.deepcopy(work["protocol_binding"])
        evidence = load(active / "evidence/0001.json")
        ac = next(
            item
            for item in work["acceptance_criteria"]
            if item["id"] == evidence["ac_id"]
        )
        receipt_at = dt.datetime.now(dt.timezone.utc) - dt.timedelta(seconds=3)
        prepared_at = receipt_at + dt.timedelta(seconds=1)
        committed_at = prepared_at + dt.timedelta(seconds=1)
        evidence_at = committed_at + dt.timedelta(seconds=1)
        attempt["journal"] = [
            {
                "ordinal": index,
                "state": state,
                "recorded_at": timestamp.isoformat(),
                "receipt_sha256": None,
            }
            for index, (state, timestamp) in enumerate(
                (
                    ("PREPARED", prepared_at),
                    ("EXECUTING", prepared_at),
                    ("OBSERVED", committed_at),
                    ("COMMITTED", committed_at),
                ),
                1,
            )
        ]
        evidence["created_at"] = evidence_at.isoformat()
        evidence["proof_receipt_created_at"] = receipt_at.isoformat()
        evidence["immutable_digest"] = "0" * 64
        evidence["immutable_digest"] = m9.canonical_digest(
            evidence, omitted_paths=(("immutable_digest",),)
        )
        common = {
            "artifact_sha256": evidence["artifact_binding"]["sha256"],
            "environment_id": evidence["environment_binding"]["id"],
            "environment_fingerprint": evidence["environment_binding"]["fingerprint"],
            "observed_now": evidence_at + dt.timedelta(seconds=1),
            "attempts_by_id": {attempt["attempt_id"]: attempt},
        }
        self.assertTrue(evidence_satisfies_ac(work, ac, evidence, **common))
        for name, attacked_time in (
            ("before-receipt", receipt_at - dt.timedelta(seconds=1)),
            ("before-commit", committed_at - dt.timedelta(microseconds=1)),
            ("future", common["observed_now"] + dt.timedelta(seconds=1)),
        ):
            attacked = copy.deepcopy(evidence)
            attacked["created_at"] = attacked_time.isoformat()
            attacked["immutable_digest"] = m9.canonical_digest(
                attacked, omitted_paths=(("immutable_digest",),)
            )
            with self.subTest(name=name):
                self.assertFalse(
                    evidence_satisfies_ac(work, ac, attacked, **common)
                )

    def test_preflight_tamper_is_rejected_before_live_core_write(self) -> None:
        for attack in (
            "missing-receipt",
            "future-receipt",
            "replace-suite",
            "replace-candidate",
        ):
            with self.subTest(attack=attack), tempfile.TemporaryDirectory(
                prefix="r1-", dir=ROOT.parent
            ) as name:
                repo = pathlib.Path(name)
                for relative in (".yuan", ".yuan-run", "scripts", "tests"):
                    shutil.copytree(ROOT / relative, repo / relative)
                self.restore_revision_seven(repo)
                before = (
                    (repo / ".yuan/core/0.1/protocol.md").read_bytes(),
                    (repo / ".yuan/core/0.1/candidate-manifest.json").read_bytes(),
                    (repo / ".yuan/authority/current").read_bytes(),
                )
                with self.assertRaises(Exception):
                    m9.install(
                        repo,
                        proof_attack=attack,
                        candidate_root=CANDIDATE,
                    )
                self.assertEqual(
                    before,
                    (
                        (repo / ".yuan/core/0.1/protocol.md").read_bytes(),
                        (repo / ".yuan/core/0.1/candidate-manifest.json").read_bytes(),
                        (repo / ".yuan/authority/current").read_bytes(),
                    ),
                )


if __name__ == "__main__":
    unittest.main()
