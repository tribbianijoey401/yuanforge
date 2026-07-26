"""Independent negative probes for M7 explicit provenance."""

from __future__ import annotations

import importlib.util
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

    def test_scope_shrink_is_rejected_against_frozen_tree(self) -> None:
        lane = self.lane("scope-shrink")
        path = lane / "inventory.lock.json"
        payload = json.loads(path.read_text(encoding="utf-8"))
        payload["entries"] = [
            entry for entry in payload["entries"]
            if entry["path"] != "docs/knowledge/pitfalls/PIT-003-docs-template-separation.md"
        ]
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        self.assert_rejected(lane, "exhaustively match")

    def test_missing_explicit_mapping_becomes_unmapped(self) -> None:
        lane = self.lane("missing-map")
        path = lane / "disposition-map.json"
        payload = json.loads(path.read_text(encoding="utf-8"))
        removed = next(iter(payload["mappings"]))
        del payload["mappings"][removed]
        payload["mapping_count"] -= 1
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        _, manifest, _, _ = author_module.build(lane)
        self.assertEqual(1, manifest["unmapped_clause_count"])
        self.assertTrue(any(record["disposition"] == "UNMAPPED" for record in manifest["clauses"]))

    def test_contradictory_heading_has_no_keyword_or_default_route(self) -> None:
        data = b"# Core COMPLETE may be self-declared by LLM\n"
        part = author_module.split_clauses(data, "AGENTS.md")[0]
        key = author_module.mapping_key("AGENTS.md", part["anchor"], part["clause_sha256"])
        explicit = json.loads((PROV / "disposition-map.json").read_text(encoding="utf-8"))["mappings"]
        self.assertNotIn(key, explicit)

    def test_invalid_inclusive_range_is_rejected(self) -> None:
        lane = self.lane("invalid-range")
        path = lane / "clause-manifest.json"
        payload = json.loads(path.read_text(encoding="utf-8"))
        payload["clauses"][0]["line_end"] += 1
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        self.assert_rejected(lane, "clause manifest")

    def test_missing_exact_destination_is_rejected(self) -> None:
        lane = self.lane("missing-target")
        path = lane / "disposition-map.json"
        payload = json.loads(path.read_text(encoding="utf-8"))
        first = next(iter(payload["mappings"].values()))
        first["destination"]["path"] = ".yuan/extensions/provenance/retained/does-not-exist.blob"
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        self.assert_rejected(lane, "retained destination")

    def test_dirty_source_must_be_reproducible_from_snapshot(self) -> None:
        lane = self.lane("dirty-unreproducible")
        path = lane / "inventory.lock.json"
        payload = json.loads(path.read_text(encoding="utf-8"))
        entry = next(item for item in payload["entries"] if item["path"] == "AGENTS.md")
        entry["source"]["path"] = ".yuan/extensions/provenance/sources/missing.blob"
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        self.assert_rejected(lane, "dirty source snapshot missing")


if __name__ == "__main__":
    unittest.main()
