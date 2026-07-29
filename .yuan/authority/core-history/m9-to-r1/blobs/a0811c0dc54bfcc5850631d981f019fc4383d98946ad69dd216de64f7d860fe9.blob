from __future__ import annotations

import pathlib
import sys
import tempfile
import threading
import time
import unittest

from _load import load_core_module


reference_port = load_core_module("reference_port")


class ReferencePortTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = pathlib.Path(self.temporary.name)
        self.port = reference_port.ReferencePort(
            self.root,
            allowed_executables=[sys.executable],
            max_command_seconds=2.0,
            max_output_bytes=4096,
        )

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def test_atomic_create_read_and_compare_and_swap(self) -> None:
        created = self.port.atomic_write("state/data.txt", b"one", expected_sha256=None)
        self.assertEqual("CREATED", created.status)
        observed = self.port.read("state/data.txt")
        self.assertEqual(b"one", observed.data)
        self.assertEqual(created.after_sha256, observed.sha256)
        updated = self.port.atomic_write(
            "state/data.txt", b"two", expected_sha256=observed.sha256
        )
        self.assertEqual("REPLACED", updated.status)
        with self.assertRaises(reference_port.CASMismatch):
            self.port.atomic_write(
                "state/data.txt", b"stale", expected_sha256=observed.sha256
            )

    def test_existing_file_cannot_be_overwritten_without_cas_hash(self) -> None:
        self.port.atomic_write("data.txt", b"one", expected_sha256=None)
        with self.assertRaises(reference_port.CASMismatch):
            self.port.atomic_write("data.txt", b"two", expected_sha256=None)

    def test_path_escape_and_symlink_are_rejected(self) -> None:
        with self.assertRaises(reference_port.ScopeViolation):
            self.port.read("../outside.txt")
        outside = self.root.parent / "outside-yuan-port.txt"
        outside.write_bytes(b"outside")
        link = self.root / "link.txt"
        try:
            link.symlink_to(outside)
        except OSError:
            with self.assertRaises(reference_port.ScopeViolation):
                self.port.read(str(outside))
        else:
            with self.assertRaises(reference_port.ScopeViolation):
                self.port.read("link.txt")

    def test_command_returns_structured_receipt(self) -> None:
        receipt = self.port.run_command(
            [sys.executable, "-c", "print('ok')"], timeout_seconds=1.0
        )
        self.assertEqual("EXITED", receipt.status)
        self.assertEqual(0, receipt.exit_code)
        self.assertEqual("ok\n", receipt.stdout)
        self.assertEqual(64, len(receipt.stdout_sha256))
        self.assertEqual("yuan.tool-receipt/v1", receipt.schema_version)
        self.assertEqual("command", receipt.kind)

    def test_command_output_is_truncated_with_full_stream_digest(self) -> None:
        receipt = self.port.run_command(
            [sys.executable, "-c", "print('x' * 6000)"], timeout_seconds=1.0
        )
        self.assertEqual("EXITED", receipt.status)
        self.assertTrue(receipt.stdout_truncated)
        self.assertLessEqual(len(receipt.stdout.encode("utf-8")), 4096)
        self.assertEqual(64, len(receipt.stdout_sha256))

    def test_command_timeout_is_bounded_and_fail_closed(self) -> None:
        started = time.monotonic()
        receipt = self.port.run_command(
            [sys.executable, "-c", "import time; time.sleep(2)"],
            timeout_seconds=0.1,
        )
        self.assertEqual("TIMED_OUT", receipt.status)
        self.assertIsNone(receipt.exit_code)
        self.assertLess(time.monotonic() - started, 1.5)

    def test_command_can_be_cancelled(self) -> None:
        token = reference_port.CancellationToken()
        timer = threading.Timer(0.1, token.cancel)
        timer.start()
        try:
            receipt = self.port.run_command(
                [sys.executable, "-c", "import time; time.sleep(2)"],
                timeout_seconds=1.0,
                cancellation=token,
            )
        finally:
            timer.cancel()
        self.assertEqual("CANCELLED", receipt.status)
        self.assertIsNone(receipt.exit_code)

    def test_unbound_executable_and_shell_string_are_rejected(self) -> None:
        with self.assertRaises(reference_port.CommandRejected):
            self.port.run_command(["not-authorized", "--version"], timeout_seconds=1.0)
        with self.assertRaises(reference_port.CommandRejected):
            self.port.run_command("echo unsafe", timeout_seconds=1.0)

    def test_llm_proposal_requires_an_explicit_bound_provider(self) -> None:
        with self.assertRaises(reference_port.UnsupportedCapability):
            self.port.propose({"messages": [{"role": "user", "content": "next"}]})


if __name__ == "__main__":
    unittest.main()
