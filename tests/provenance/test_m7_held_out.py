"""Independent negative probes for M7 explicit provenance."""

from __future__ import annotations

import importlib.util
import hashlib
import json
import shutil
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PROV = ROOT / ".yuan/extensions/provenance"

verify_spec = importlib.util.spec_from_file_location(
    "yuan_provenance_verify",
    ROOT / "scripts/yuan_provenance_verify.py",
)
assert verify_spec and verify_spec.loader
verify_module = importlib.util.module_from_spec(verify_spec)
verify_spec.loader.exec_module(verify_module)

author_spec = importlib.util.spec_from_file_location(
    "yuan_provenance_author",
    ROOT / "scripts/yuan-provenance.py",
)
assert author_spec and author_spec.loader
author_module = importlib.util.module_from_spec(author_spec)
author_spec.loader.exec_module(author_module)


class M7HeldOutNegativeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.temp = tempfile.TemporaryDirectory(prefix="yuan-m7-held-out-")
        cls.base = Path(cls.temp.name) / "provenance"
        shutil.copytree(PROV, cls.base)

    @classmethod
    def tearDownClass(cls) -> None:
        cls.temp.cleanup()

    def lane(self, name: str) -> Path:
        target = Path(self.temp.name) / name
        shutil.copytree(self.base, target)
        return target

    def assert_rejected(self, lane: Path, contains: str) -> None:
        with self.assertRaises(verify_module.ProvenanceFailure) as caught:
            verify_module.verify(ROOT, lane)
        self.assertIn(contains, str(caught.exception))

    @staticmethod
    def canonical(payload: object) -> bytes:
        return (
            json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
        ).encode("utf-8")

    def semantic_registry(self, lane: Path) -> dict:
        return json.loads(
            (lane / "semantic-registry.json").read_text(encoding="utf-8")
        )

    def write_registry_and_manifest(
        self,
        lane: Path,
        payload: dict,
        *,
        update_pin: bool = True,
    ) -> str:
        encoded = self.canonical(payload)
        (lane / "semantic-registry.json").write_bytes(encoded)
        (lane / "clause-manifest.json").write_bytes(encoded)
        digest = hashlib.sha256(encoded).hexdigest()
        if update_pin:
            (lane / "semantic-registry.sha256").write_text(
                digest + "\n", encoding="ascii"
            )
        return digest

    def test_scope_shrink_is_rejected_against_frozen_tree(self) -> None:
        lane = self.lane("scope-shrink")
        path = lane / "inventory.lock.json"
        payload = json.loads(path.read_text(encoding="utf-8"))
        payload["entries"] = [
            entry for entry in payload["entries"]
            if entry["path"] != "docs/knowledge/pitfalls/PIT-003-docs-template-separation.md"
        ]
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        self.assert_rejected(lane, "inventory binding")

    def test_missing_explicit_mapping_becomes_unmapped(self) -> None:
        lane = self.lane("missing-map")
        payload = self.semantic_registry(lane)
        removed = payload["records"][0]["source_mapping_key"]
        payload["records"] = [
            record for record in payload["records"]
            if record["source_mapping_key"] != removed
        ]
        payload["semantic_record_count"] = len(payload["records"])
        self.write_registry_and_manifest(lane, payload)
        with self.assertRaisesRegex(ValueError, "UNMAPPED"):
            author_module.build(lane)

    def test_contradictory_heading_has_no_keyword_or_default_route(self) -> None:
        data = b"# Core COMPLETE may be self-declared by LLM\n"
        part = author_module.split_clauses(data, "AGENTS.md")[0]
        key = author_module.mapping_key("AGENTS.md", part["anchor"], part["clause_sha256"])
        registry = self.semantic_registry(PROV)
        self.assertNotIn(
            key, {record["source_mapping_key"] for record in registry["records"]}
        )

    def test_invalid_inclusive_range_is_rejected(self) -> None:
        lane = self.lane("invalid-range")
        path = lane / "clause-manifest.json"
        payload = json.loads(path.read_text(encoding="utf-8"))
        payload["records"][0]["line_end"] += 1
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        self.assert_rejected(lane, "registry/manifest")

    def test_missing_exact_destination_is_rejected(self) -> None:
        lane = self.lane("missing-target")
        payload = self.semantic_registry(lane)
        first = payload["records"][0]
        first["destination"]["path"] = ".yuan/extensions/provenance/retained/does-not-exist.blob"
        self.write_registry_and_manifest(lane, payload)
        self.assert_rejected(lane, "retained destination")

    def test_dirty_source_must_be_reproducible_from_snapshot(self) -> None:
        lane = self.lane("dirty-unreproducible")
        path = lane / "inventory.lock.json"
        payload = json.loads(path.read_text(encoding="utf-8"))
        entry = next(item for item in payload["entries"] if item["path"] == "AGENTS.md")
        entry["source"]["path"] = ".yuan/extensions/provenance/sources/missing.blob"
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        self.assert_rejected(lane, "inventory binding")

    def test_category_flip_is_rejected_even_when_registry_and_manifest_match(self) -> None:
        lane = self.lane("category-flip")
        payload = self.semantic_registry(lane)
        record = next(
            item for item in payload["records"]
            if item["disposition"] == "extension"
        )
        record["disposition"] = "core"
        self.write_registry_and_manifest(lane, payload)
        self.assert_rejected(lane, "disposition/target family")

    def test_valid_but_wrong_target_is_rejected_by_reviewed_registry_hash(self) -> None:
        lane = self.lane("valid-wrong-target")
        original = (lane / "semantic-registry.sha256").read_text(
            encoding="ascii"
        ).strip()
        payload = self.semantic_registry(lane)
        target_registry = json.loads(
            (lane / "target-family-registry.json").read_text(encoding="utf-8")
        )
        testing_targets = target_registry["families"]["testing"]["targets"]
        record = next(
            item for item in payload["records"]
            if item["source"] == ".yuan/rules/iron-rules.md"
            and item["line_start"] == 90
        )
        replacement = next(
            target for target in testing_targets
            if target["anchor"] != record["target"]["anchor"]
        )
        record["target"] = replacement
        self.write_registry_and_manifest(lane, payload)
        with self.assertRaises(verify_module.ProvenanceFailure) as caught:
            verify_module.verify(
                ROOT, lane, expected_registry_sha256=original
            )
        self.assertIn("semantic registry hash", str(caught.exception))

    def test_cross_family_target_is_rejected(self) -> None:
        lane = self.lane("cross-family")
        payload = self.semantic_registry(lane)
        record = next(
            item for item in payload["records"]
            if item["disposition"] == "extension"
            and item["target_family"] == "software-delivery"
            and item["target"]["kind"] == "semantic-anchor"
        )
        record["target_family"] = "testing"
        self.write_registry_and_manifest(lane, payload)
        self.assert_rejected(lane, "target family/path")

    def test_registry_manifest_drift_is_rejected(self) -> None:
        lane = self.lane("registry-manifest-drift")
        payload = self.semantic_registry(lane)
        payload["records"][0]["target_claim"] += " altered"
        (lane / "clause-manifest.json").write_bytes(self.canonical(payload))
        self.assert_rejected(lane, "registry/manifest")

    def test_compound_workflow_clause_requires_all_atomic_subclauses(self) -> None:
        lane = self.lane("compound-clause")
        payload = self.semantic_registry(lane)
        compound = [
            item for item in payload["records"]
            if item.get("parent_source_anchor")
            == "md:phase-4b-tester-测试验证:1"
        ]
        self.assertGreaterEqual(len(compound), 10)
        removed = compound[-1]["record_key"]
        payload["records"] = [
            item for item in payload["records"]
            if item["record_key"] != removed
        ]
        payload["semantic_record_count"] -= 1
        self.write_registry_and_manifest(lane, payload)
        self.assert_rejected(lane, "compound clause")


if __name__ == "__main__":
    unittest.main()
