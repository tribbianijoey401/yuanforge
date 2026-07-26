#!/usr/bin/env python3
"""Run the frozen M1 bootstrap verifier over the M3 Core candidate.

The M1 verifier only accepts candidates beneath the manifest root.  This
runner therefore creates an isolated suite, copies the exact content-addressed
candidate and frozen M1 negative cases into it, and invokes the unchanged M1
verifier.  The persisted manifest snapshot and receipt make the run auditable.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import shutil
import subprocess
import sys
import tempfile
from typing import Any


ROOT = pathlib.Path(__file__).resolve().parents[2]
CORE = ROOT / ".yuan" / "core" / "0.1"
M1_SUITE = ROOT / "tests" / "bootstrap_verifier" / "fixtures" / "author-visible"
M1_MANIFEST_SHA256 = "66f20b3a04050135468209e6ead66f3df258f2faff8dbeb8f76a50c635ad8e55"
CORE_MANIFEST_SHA256 = "c3d41ac1a056523ad5af4a430e09185f7ab1e732507097ba7546be7f512d72e3"
FROZEN_M1_FILES = {
    "scripts/bootstrap-core-verifier.py": "94a36a178ee8242e850ee9f23b7cafc63906eac8aac2e723ca64225751cdfb40",
    "scripts/bootstrap_verifier.py": "9ec6ba19fb7a4c2d4e6d654be0bcda3190c38fcd0842ddf8ce17b3996a984119",
    "scripts/bootstrap_verifier_support.py": "d4435acdc60458893c39e7722a801df1418dd634d8330469ecf3c34b8ac5749b",
}


def sha256(path: pathlib.Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_object(path: pathlib.Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise TypeError(f"{path} is not a JSON object")
    return value


def assert_frozen_inputs() -> tuple[dict[str, Any], dict[str, Any]]:
    for relative, expected in FROZEN_M1_FILES.items():
        actual = sha256(ROOT / relative)
        if actual != expected:
            raise RuntimeError(f"old trust-root drift: {relative}: {actual}")
    visible_manifest = M1_SUITE / "manifest.json"
    if sha256(visible_manifest) != M1_MANIFEST_SHA256:
        raise RuntimeError("frozen M1 negative manifest drift")
    core_manifest_path = CORE / "candidate-manifest.json"
    if sha256(core_manifest_path) != CORE_MANIFEST_SHA256:
        raise RuntimeError("task-005 candidate manifest drift")
    return load_object(visible_manifest), load_object(core_manifest_path)


def copy_core(
    destination: pathlib.Path,
    candidate_manifest: dict[str, Any],
) -> list[dict[str, str]]:
    required: list[dict[str, str]] = []
    expected_paths: set[str] = set()
    for item in candidate_manifest.get("files", []):
        relative = item["path"]
        expected = item["sha256"]
        source = CORE / pathlib.PurePosixPath(relative)
        if not source.is_file() or sha256(source) != expected:
            raise RuntimeError(f"candidate file drift: {relative}")
        target = destination / pathlib.PurePosixPath(relative)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
        required.append({"path": relative, "sha256": expected})
        expected_paths.add(relative)
    manifest_target = destination / "candidate-manifest.json"
    shutil.copyfile(CORE / "candidate-manifest.json", manifest_target)
    required.append(
        {
            "path": "candidate-manifest.json",
            "sha256": CORE_MANIFEST_SHA256,
        }
    )
    expected_paths.add("candidate-manifest.json")
    actual_paths = {
        path.relative_to(destination).as_posix()
        for path in destination.rglob("*")
        if path.is_file()
    }
    if actual_paths != expected_paths:
        raise RuntimeError("isolated candidate topology mismatch")
    return required


def build_suite(root: pathlib.Path) -> tuple[pathlib.Path, str, dict[str, Any]]:
    visible_manifest, candidate_manifest = assert_frozen_inputs()
    shutil.copytree(M1_SUITE / "candidates", root / "candidates")
    shutil.copytree(M1_SUITE / "validators", root / "validators")
    required = copy_core(root / "candidates" / "core-01", candidate_manifest)
    independent_validator = pathlib.Path(__file__).with_name("held_out_validator.py")
    validator_target = root / "validators" / "m3_held_out_validator.py"
    shutil.copyfile(independent_validator, validator_target)
    validator_hash = sha256(validator_target)
    cases = list(visible_manifest["cases"])
    cases.append(
        {
            "id": "yuan-core-01-candidate",
            "candidate": "candidates/core-01",
            "required_files": required,
            "validator": {
                "command": [
                    "{python}",
                    "validators/m3_held_out_validator.py",
                    "{candidate}",
                ],
                "trusted_files": [
                    {
                        "path": "validators/m3_held_out_validator.py",
                        "sha256": validator_hash,
                    }
                ],
                "timeout_seconds": 20,
            },
            "expected": "ACCEPT",
            "negative_class": None,
            "expected_reason_codes": [],
        }
    )
    manifest = {
        "schema_version": "yuan.bootstrap-suite/v1",
        "suite_id": "m3-old-root-verifies-yuan-core-01",
        "cases": cases,
    }
    manifest_path = root / "manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    return manifest_path, sha256(manifest_path), manifest


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--receipt", required=True, type=pathlib.Path)
    parser.add_argument("--manifest-snapshot", required=True, type=pathlib.Path)
    args = parser.parse_args()
    receipt = args.receipt.resolve()
    manifest_snapshot = args.manifest_snapshot.resolve()
    receipt.parent.mkdir(parents=True, exist_ok=True)
    manifest_snapshot.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="yuan-m3-bootstrap-") as temporary:
        manifest_path, manifest_hash, manifest = build_suite(pathlib.Path(temporary))
        manifest_snapshot.write_text(
            json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
            newline="\n",
        )
        completed = subprocess.run(
            [
                sys.executable,
                "-B",
                str(ROOT / "scripts" / "bootstrap-core-verifier.py"),
                "--manifest",
                str(manifest_path),
                "--manifest-sha256",
                manifest_hash,
                "--receipt",
                str(receipt),
            ],
            cwd=ROOT,
            text=True,
            encoding="utf-8",
            errors="strict",
            capture_output=True,
            check=False,
        )
    sys.stdout.write(completed.stdout)
    sys.stderr.write(completed.stderr)
    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())
