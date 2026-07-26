from __future__ import annotations

import hashlib
import importlib.util
import pathlib
import sys
import tempfile
import time
import unittest

import yaml


REPOSITORY = pathlib.Path(__file__).resolve().parents[2]
CORE = REPOSITORY / ".yuan" / "core" / "0.1"
ADAPTERS = REPOSITORY / ".yuan" / "adapters"
PROTOCOL_REVISION = "yuan.core.protocol/0.1.0-candidate"

FILESYSTEM_CAPABILITIES = {
    "enumerate",
    "read_hash",
    "atomic_replace",
    "compare_and_swap",
    "path_containment",
}
COMMAND_CAPABILITIES = {
    "bounded_execution",
    "timeout",
    "structured_receipt",
    "output_cap",
    "scope_profile",
}
LLM_CAPABILITIES = {"propose_only", "no_unmediated_side_effects"}


def _load_module(name: str):
    if str(CORE) not in sys.path:
        sys.path.insert(0, str(CORE))
    spec = importlib.util.spec_from_file_location(name, CORE / f"{name}.py")
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load Core module: {name}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


reference_port = _load_module("reference_port")


def _load_descriptor(adapter_id: str) -> dict:
    path = ADAPTERS / f"{adapter_id}.yaml"
    if not path.is_file():
        raise AssertionError(
            f"missing executable Core adapter descriptor: "
            f".yuan/adapters/{adapter_id}.yaml"
        )
    loaded = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(loaded, dict):
        raise AssertionError(f"{path} must contain one mapping")
    return loaded


def _assert_capability_map(
    testcase: unittest.TestCase,
    actual: object,
    expected: set[str],
    *,
    adapter_id: str,
    group: str,
    status: str,
) -> None:
    testcase.assertIsInstance(
        actual, dict, f"{adapter_id}: capabilities.{group} must be a mapping"
    )
    missing = expected - set(actual)
    testcase.assertFalse(
        missing, f"{adapter_id}: capabilities.{group} omits {sorted(missing)}"
    )
    expected_value = "supported" if status == "supported" else "unsupported"
    for capability in expected:
        testcase.assertEqual(
            expected_value,
            actual[capability],
            f"{adapter_id}: {group}.{capability} must be explicitly "
            f"{expected_value}",
        )


def _assert_descriptor(
    testcase: unittest.TestCase,
    adapter_id: str,
    *,
    manual_reference_required: bool,
) -> None:
    descriptor = _load_descriptor(adapter_id)
    testcase.assertEqual("yuan.adapter-descriptor/v1", descriptor.get("schema_version"))
    testcase.assertEqual(adapter_id, descriptor.get("adapter_id"))
    testcase.assertEqual(PROTOCOL_REVISION, descriptor.get("core_protocol_revision"))
    status = descriptor.get("status")
    testcase.assertIn(status, {"supported", "unsupported"})

    if manual_reference_required:
        testcase.assertEqual(
            "supported",
            status,
            "manual must expose the executable reference Port rather than a "
            "documentation-only human fallback",
        )

    capabilities = descriptor.get("capabilities")
    testcase.assertIsInstance(capabilities, dict)
    _assert_capability_map(
        testcase,
        capabilities.get("filesystem"),
        FILESYSTEM_CAPABILITIES,
        adapter_id=adapter_id,
        group="filesystem",
        status=status,
    )
    _assert_capability_map(
        testcase,
        capabilities.get("command"),
        COMMAND_CAPABILITIES,
        adapter_id=adapter_id,
        group="command",
        status=status,
    )
    _assert_capability_map(
        testcase,
        capabilities.get("llm"),
        LLM_CAPABILITIES,
        adapter_id=adapter_id,
        group="llm",
        status=status,
    )

    if status == "supported":
        implementation = descriptor.get("executable_port")
        testcase.assertIsInstance(implementation, str)
        testcase.assertTrue(
            implementation.strip(),
            f"{adapter_id}: supported requires an executable_port binding",
        )
    else:
        reason = descriptor.get("unsupported_reason")
        testcase.assertIsInstance(reason, str)
        testcase.assertTrue(
            reason.strip(),
            f"{adapter_id}: unsupported must name why Core cannot execute it",
        )


class _ProposalOnlyProvider:
    def propose(self, request: dict) -> dict:
        return {
            "proposal": {
                "action": {
                    "type": "file-write",
                    "scope": request["target"],
                    "content": "must remain only a proposal",
                }
            }
        }


class ReferencePortConformance(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = pathlib.Path(self.temporary.name)
        self.port = reference_port.ReferencePort(
            self.root,
            allowed_executables=[sys.executable],
            max_command_seconds=1.0,
            max_output_bytes=256,
            proposal_provider=_ProposalOnlyProvider(),
        )

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def test_filesystem_enumerate_hash_atomic_replace_cas_and_containment(self) -> None:
        created = self.port.atomic_write("nested/a.txt", b"alpha", expected_sha256=None)
        observed = self.port.read("nested/a.txt")
        self.assertEqual(hashlib.sha256(b"alpha").hexdigest(), observed.sha256)
        self.assertEqual(created.after_sha256, observed.sha256)

        enumerate_files = getattr(self.port, "enumerate_files", None)
        self.assertTrue(
            callable(enumerate_files),
            "ReferencePort must expose bounded enumerate_files with per-file hashes",
        )
        listing = enumerate_files(".")
        self.assertEqual("yuan.tool-receipt/v1", listing.schema_version)
        self.assertEqual("file-enumeration", listing.kind)
        self.assertEqual("OBSERVED", listing.status)
        entries = list(listing.entries)
        self.assertEqual(["nested/a.txt"], [entry.path for entry in entries])
        self.assertEqual(observed.sha256, entries[0].sha256)
        self.assertEqual(5, entries[0].size_bytes)

        replaced = self.port.atomic_write(
            "nested/a.txt", b"beta", expected_sha256=observed.sha256
        )
        self.assertEqual("REPLACED", replaced.status)
        with self.assertRaises(reference_port.CASMismatch):
            self.port.atomic_write(
                "nested/a.txt", b"stale", expected_sha256=observed.sha256
            )
        for escaped in ("../outside.txt", str(self.root.parent / "outside.txt")):
            with self.assertRaises(reference_port.ScopeViolation):
                self.port.read(escaped)

    def test_command_is_bounded_receipted_capped_and_profile_scoped(self) -> None:
        receipt = self.port.run_command(
            [sys.executable, "-c", "print('x' * 1024)"], timeout_seconds=0.5
        )
        self.assertEqual("yuan.tool-receipt/v1", receipt.schema_version)
        self.assertEqual("command", receipt.kind)
        self.assertEqual("EXITED", receipt.status)
        self.assertTrue(receipt.sandboxed)
        self.assertTrue(receipt.stdout_truncated)
        self.assertLessEqual(len(receipt.stdout.encode("utf-8")), 256)
        self.assertEqual(64, len(receipt.stdout_sha256))
        self.assertEqual(64, len(receipt.stderr_sha256))

        started = time.monotonic()
        timed_out = self.port.run_command(
            [sys.executable, "-c", "import time; time.sleep(2)"],
            timeout_seconds=0.05,
        )
        self.assertEqual("TIMED_OUT", timed_out.status)
        self.assertIsNone(timed_out.exit_code)
        self.assertLess(time.monotonic() - started, 1.0)

        outside = str(self.root.parent / "outside.txt")
        with self.assertRaises(reference_port.CommandRejected):
            self.port.run_command(
                [sys.executable, "-c", "print('x')", outside],
                timeout_seconds=0.5,
            )
        unprofiled = reference_port.ReferencePort(
            self.root,
            allowed_executables=[sys.executable],
            command_profiles={sys.executable: "unknown-profile/v1"},
            max_command_seconds=1.0,
            max_output_bytes=256,
        )
        with self.assertRaises(reference_port.CommandRejected):
            unprofiled.run_command(
                [sys.executable, "-c", "print('x')"], timeout_seconds=0.5
            )

    def test_llm_is_proposal_only_and_returns_a_structured_receipt(self) -> None:
        target = self.root / "proposal-must-not-execute.txt"
        receipt = self.port.propose({"target": "proposal-must-not-execute.txt"})
        self.assertFalse(target.exists(), "Port must not execute an LLM-proposed action")
        self.assertEqual("yuan.tool-receipt/v1", receipt.get("schema_version"))
        self.assertEqual("llm-propose", receipt.get("kind"))
        self.assertEqual("PROPOSED", receipt.get("status"))
        self.assertIsInstance(receipt.get("operation_id"), str)
        self.assertIsInstance(receipt.get("proposal"), dict)


class AdapterDescriptorConformance(unittest.TestCase):
    def test_manual_has_executable_reference_mapping(self) -> None:
        _assert_descriptor(self, "manual", manual_reference_required=True)

    def test_hermes_is_executable_or_honestly_unsupported(self) -> None:
        _assert_descriptor(self, "hermes", manual_reference_required=False)


if __name__ == "__main__":
    unittest.main()
