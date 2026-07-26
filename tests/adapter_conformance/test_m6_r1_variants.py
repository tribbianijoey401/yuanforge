from __future__ import annotations

import copy
import hashlib
import importlib
import importlib.util
import json
import os
import pathlib
import sys
import tempfile
import unittest
from unittest import mock


REPOSITORY = pathlib.Path(__file__).resolve().parents[2]
CORE = REPOSITORY / ".yuan" / "core" / "0.1"


def _load_reference_port():
    if str(CORE) not in sys.path:
        sys.path.insert(0, str(CORE))
    spec = importlib.util.spec_from_file_location(
        "m6_r1_reference_port", CORE / "reference_port.py"
    )
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load Reference Port")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


reference_port = _load_reference_port()
port_types = importlib.import_module("port_types")


class _MalformedProvider:
    def propose(self, request: dict) -> dict:
        return {"proposal": {}}


class _ErrorProvider:
    def propose(self, request: dict) -> dict:
        raise RuntimeError("provider failed before producing a proposal")


def _descriptor_binding_is_valid(descriptor: dict) -> bool:
    if descriptor.get("status") != "supported":
        return False
    raw_path = descriptor.get("executable_port")
    expected_sha256 = descriptor.get("executable_port_sha256")
    if not isinstance(raw_path, str) or not isinstance(expected_sha256, str):
        return False
    relative = pathlib.Path(raw_path)
    if relative.is_absolute() or ".." in relative.parts:
        return False
    candidate = (REPOSITORY / relative).resolve(strict=False)
    try:
        candidate.relative_to(REPOSITORY.resolve())
    except ValueError:
        return False
    return (
        candidate.is_file()
        and hashlib.sha256(candidate.read_bytes()).hexdigest() == expected_sha256
    )


class M6IndependentVariants(unittest.TestCase):
    def test_enumeration_cannot_expand_budget_or_cross_a_link(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = pathlib.Path(temporary)
            port = reference_port.ReferencePort(
                root,
                allowed_executables=[sys.executable],
                max_command_seconds=1.0,
                max_output_bytes=128,
                max_enumeration_files=2,
                max_enumeration_depth=1,
            )
            port.atomic_write("one.txt", b"1", expected_sha256=None)
            port.atomic_write("two.txt", b"2", expected_sha256=None)
            with self.assertRaises(port_types.EnumerationLimitExceeded):
                port.enumerate_files(".", max_files=3)
            port.atomic_write("three.txt", b"3", expected_sha256=None)
            with self.assertRaises(port_types.EnumerationLimitExceeded):
                port.enumerate_files(".")

            outside = root.parent / f"{root.name}-m6-outside"
            outside.mkdir()
            try:
                (outside / "secret.txt").write_text("secret", encoding="utf-8")
                link = root / "escape"
                try:
                    os.symlink(outside, link, target_is_directory=True)
                except (OSError, NotImplementedError):
                    link.mkdir()
                    with mock.patch(
                        "port_enumeration._is_link_or_junction",
                        side_effect=lambda path: path.name == "escape",
                    ):
                        with self.assertRaises(reference_port.ScopeViolation):
                            port.enumerate_files(".")
                else:
                    with self.assertRaises(reference_port.ScopeViolation):
                        port.enumerate_files(".")
            finally:
                if outside.exists():
                    for child in outside.iterdir():
                        child.unlink()
                    outside.rmdir()

    def test_malformed_or_failed_provider_never_creates_a_receipt_or_action(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = pathlib.Path(temporary)
            target = root / "must-not-exist.txt"
            common = {
                "root": root,
                "allowed_executables": [sys.executable],
                "max_command_seconds": 1.0,
                "max_output_bytes": 128,
            }
            malformed = reference_port.ReferencePort(
                proposal_provider=_MalformedProvider(), **common
            )
            with self.assertRaises(port_types.PortError):
                malformed.propose({"target": target.name})
            errored = reference_port.ReferencePort(
                proposal_provider=_ErrorProvider(), **common
            )
            with self.assertRaises(RuntimeError):
                errored.propose({"target": target.name})
            self.assertFalse(target.exists())

    def test_descriptor_hash_drift_and_escape_are_rejected_in_memory(self) -> None:
        manual = json.loads(
            (REPOSITORY / ".yuan/adapters/manual.yaml").read_text(encoding="utf-8")
        )
        hermes = json.loads(
            (REPOSITORY / ".yuan/adapters/hermes.yaml").read_text(encoding="utf-8")
        )
        self.assertTrue(_descriptor_binding_is_valid(manual))
        self.assertEqual(
            ".yuan/core/0.1/reference_port.py", manual["executable_port"]
        )
        self.assertTrue(hasattr(reference_port, "ReferencePort"))

        drifted = copy.deepcopy(manual)
        drifted["executable_port_sha256"] = "0" * 64
        self.assertFalse(_descriptor_binding_is_valid(drifted))
        escaped = copy.deepcopy(manual)
        escaped["executable_port"] = "../outside.py"
        self.assertFalse(_descriptor_binding_is_valid(escaped))

        self.assertEqual("unsupported", hermes["status"])
        self.assertNotIn("executable_port", hermes)
        self.assertTrue(hermes["unsupported_reason"].strip())
        for family in hermes["capabilities"].values():
            self.assertTrue(all(value == "unsupported" for value in family.values()))
        candidate_manifest = json.loads(
            (CORE / "candidate-manifest.json").read_text(encoding="utf-8")
        )
        self.assertFalse(
            any("hermes" in item["path"].lower() for item in candidate_manifest["files"]),
            "Core candidate must not depend on the unsupported Hermes adapter",
        )


if __name__ == "__main__":
    unittest.main()
