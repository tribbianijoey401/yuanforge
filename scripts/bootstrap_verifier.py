#!/usr/bin/env python3
"""Fail-closed implementation for the frozen Yuan bootstrap fixture suite."""

from __future__ import annotations

import argparse
import json
import pathlib
import subprocess
import sys
from typing import Any

from bootstrap_verifier_support import (
    NEGATIVE_CONTRACT,
    RESULT_SCHEMA,
    SHA256_PATTERN,
    SUITE_SCHEMA,
    ManifestError,
    atomic_write_json,
    file_sha256,
    meaningful_files,
    receipt_base,
    resolve_within,
    tree_digest,
    validate_hash_specs,
)


def validate_validator_result(stdout: str) -> tuple[list[str], int]:
    try:
        result = json.loads(stdout)
    except (json.JSONDecodeError, TypeError):
        return ["RESULT_PARSE_ERROR"], 0
    if not isinstance(result, dict) or result.get("schema_version") != RESULT_SCHEMA:
        return ["RESULT_SCHEMA_ERROR"], 0
    assertions = result.get("assertions")
    checks = result.get("checks")
    status = result.get("status")
    if isinstance(assertions, bool) or not isinstance(assertions, int) or assertions < 0:
        return ["RESULT_SCHEMA_ERROR"], 0
    if not isinstance(checks, list) or status not in {"PASS", "FAIL"}:
        return ["RESULT_SCHEMA_ERROR"], 0
    if assertions == 0:
        return ["ZERO_ASSERTIONS"], 0
    if len(checks) != assertions:
        return ["RESULT_SCHEMA_ERROR"], 0
    for check in checks:
        if (
            not isinstance(check, dict)
            or not isinstance(check.get("id"), str)
            or not check["id"]
            or check.get("status") not in {"PASS", "FAIL"}
        ):
            return ["RESULT_SCHEMA_ERROR"], 0
    if status == "FAIL" or any(check["status"] == "FAIL" for check in checks):
        return ["CHECK_FAILED"], assertions
    return [], assertions


def verify_case(case: dict[str, Any], root: pathlib.Path) -> dict[str, Any]:
    case_id = case.get("id")
    expected = case.get("expected")
    negative_class = case.get("negative_class")
    expected_reasons = case.get("expected_reason_codes")
    if not isinstance(case_id, str) or not case_id:
        raise ManifestError("every case requires a non-empty id")
    if expected not in {"ACCEPT", "REJECT"}:
        raise ManifestError(f"case {case_id}: expected must be ACCEPT or REJECT")
    if negative_class is not None and negative_class not in NEGATIVE_CONTRACT:
        raise ManifestError(f"case {case_id}: unknown negative_class")
    if expected == "ACCEPT" and negative_class is not None:
        raise ManifestError(f"case {case_id}: ACCEPT cannot be a negative case")
    if not isinstance(expected_reasons, list) or not all(
        isinstance(reason, str) for reason in expected_reasons
    ):
        raise ManifestError(f"case {case_id}: expected_reason_codes must be strings")
    if len(expected_reasons) != len(set(expected_reasons)):
        raise ManifestError(f"case {case_id}: expected_reason_codes must be unique")
    if negative_class and NEGATIVE_CONTRACT[negative_class] not in expected_reasons:
        raise ManifestError(f"case {case_id}: negative class reason is not frozen")

    candidate = resolve_within(root, case.get("candidate"), f"case {case_id}.candidate")
    required = validate_hash_specs(
        case.get("required_files"), candidate, f"case {case_id}.required_files"
    )
    if expected == "ACCEPT" and not required:
        raise ManifestError(f"case {case_id}: ACCEPT requires at least one bound file")
    validator = case.get("validator")
    if not isinstance(validator, dict):
        raise ManifestError(f"case {case_id}: validator must be an object")
    trusted = validate_hash_specs(
        validator.get("trusted_files"), root, f"case {case_id}.validator.trusted_files"
    )
    if not trusted:
        raise ManifestError(f"case {case_id}: validator has no trusted files")
    command = validator.get("command")
    timeout = validator.get("timeout_seconds")
    if (
        not isinstance(command, list)
        or not command
        or not all(isinstance(token, str) and token for token in command)
    ):
        raise ManifestError(f"case {case_id}: validator command is invalid")
    if isinstance(timeout, bool) or not isinstance(timeout, (int, float)) or not 0 < timeout <= 60:
        raise ManifestError(f"case {case_id}: timeout must be within (0, 60]")

    reasons: list[str] = []
    checks_executed = 0
    has_symlink = any(
        path.is_symlink() for path in candidate.rglob("*")
    ) if candidate.is_dir() else False
    files = meaningful_files(candidate)
    before_digest = tree_digest(candidate, files)
    if not candidate.is_dir() or not files:
        reasons.append("EMPTY_CANDIDATE")
    if has_symlink:
        reasons.append("SYMLINK_NOT_ALLOWED")
    expected_paths = {relative for _, relative, _ in required}
    actual_paths = {path.relative_to(candidate).as_posix() for path in files}
    if files and actual_paths != expected_paths:
        reasons.append("CANDIDATE_FILE_SET_MISMATCH")
    for path, _, expected_hash in required:
        checks_executed += 1
        if path.is_symlink():
            reasons.append("SYMLINK_NOT_ALLOWED")
        elif not path.is_file():
            reasons.append("REQUIRED_FILE_MISSING")
        elif file_sha256(path) != expected_hash:
            reasons.append("HASH_MISMATCH")
    for path, _, expected_hash in trusted:
        checks_executed += 1
        if (
            path.is_symlink()
            or not path.is_file()
            or file_sha256(path) != expected_hash
        ):
            reasons.append("UNTRUSTED_VALIDATOR")

    validator_receipt: dict[str, Any] = {"exit_code": None, "assertions": 0}
    if not reasons:
        expanded = [
            token.replace("{python}", sys.executable).replace(
                "{candidate}", str(candidate)
            )
            for token in command
        ]
        try:
            completed = subprocess.run(
                expanded,
                cwd=root,
                text=True,
                encoding="utf-8",
                errors="strict",
                capture_output=True,
                timeout=timeout,
                check=False,
            )
            validator_receipt["exit_code"] = completed.returncode
            validator_receipt["stderr"] = completed.stderr[-4000:]
            if completed.returncode != 0:
                reasons.append("VALIDATOR_ERROR")
            else:
                result_reasons, assertion_count = validate_validator_result(
                    completed.stdout
                )
                reasons.extend(result_reasons)
                checks_executed += assertion_count
                validator_receipt["assertions"] = assertion_count
        except subprocess.TimeoutExpired:
            reasons.append("VALIDATOR_TIMEOUT")
        except (OSError, UnicodeError):
            reasons.append("VALIDATOR_ERROR")
    after_files = meaningful_files(candidate)
    after_digest = tree_digest(candidate, after_files)
    if before_digest != after_digest:
        reasons.append("CANDIDATE_MUTATED")
    reasons = list(dict.fromkeys(reasons))
    observed = "REJECT" if reasons else "ACCEPT"
    matched = observed == expected and set(reasons) == set(expected_reasons)
    return {
        "id": case_id,
        "negative_class": negative_class,
        "expected": expected,
        "observed": observed,
        "matched": matched,
        "reason_codes": reasons,
        "candidate_sha256": after_digest,
        "checks_executed": checks_executed,
        "validator": validator_receipt,
    }


def run_suite(manifest: dict[str, Any], root: pathlib.Path) -> dict[str, Any]:
    if manifest.get("schema_version") != SUITE_SCHEMA:
        raise ManifestError(f"schema_version must be {SUITE_SCHEMA}")
    suite_id = manifest.get("suite_id")
    cases = manifest.get("cases")
    if not isinstance(suite_id, str) or not suite_id:
        raise ManifestError("suite_id must be a non-empty string")
    if not isinstance(cases, list) or not cases:
        raise ManifestError("cases must be a non-empty list")
    results = [verify_case(case, root) for case in cases if isinstance(case, dict)]
    if len(results) != len(cases):
        raise ManifestError("every case must be an object")
    ids = [case["id"] for case in results]
    if len(ids) != len(set(ids)):
        raise ManifestError("case ids must be unique")
    covered = {case["negative_class"] for case in results if case["negative_class"]}
    missing = sorted(set(NEGATIVE_CONTRACT) - covered)
    if missing:
        raise ManifestError(f"required negative classes missing: {', '.join(missing)}")
    if not any(case["expected"] == "ACCEPT" for case in results):
        raise ManifestError("suite requires at least one ACCEPT case")
    return {
        "suite_id": suite_id,
        "cases": results,
        "checks_executed": sum(case["checks_executed"] for case in results),
        "passed": all(case["matched"] for case in results),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Verify a frozen Yuan bootstrap fixture suite and emit a receipt."
    )
    parser.add_argument("--manifest", required=True, type=pathlib.Path)
    parser.add_argument(
        "--manifest-sha256",
        required=True,
        help="Trusted lowercase SHA-256 of the frozen manifest.",
    )
    parser.add_argument("--receipt", required=True, type=pathlib.Path)
    return parser.parse_args()


def main() -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    args = parse_args()
    manifest_path = args.manifest.resolve()
    receipt = receipt_base(manifest_path)
    exit_code = 2
    try:
        if not SHA256_PATTERN.fullmatch(args.manifest_sha256):
            raise ManifestError("manifest-sha256 is not lowercase SHA-256")
        actual_hash = file_sha256(manifest_path)
        receipt["manifest_sha256"] = actual_hash
        if actual_hash != args.manifest_sha256:
            receipt["reason_codes"].append("MANIFEST_HASH_MISMATCH")
        else:
            try:
                manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, UnicodeError):
                receipt["reason_codes"].append("MANIFEST_PARSE_ERROR")
            else:
                if not isinstance(manifest, dict):
                    raise ManifestError("manifest root must be an object")
                suite = run_suite(manifest, manifest_path.parent.resolve())
                receipt["suite_id"] = suite["suite_id"]
                receipt["cases"] = suite["cases"]
                receipt["checks_executed"] = suite["checks_executed"]
                if suite["passed"] and suite["checks_executed"] > 0:
                    receipt["status"] = "PASS"
                    exit_code = 0
                else:
                    receipt["reason_codes"].append("SUITE_EXPECTATION_MISMATCH")
                    exit_code = 1
    except FileNotFoundError:
        receipt["reason_codes"].append("MANIFEST_NOT_FOUND")
    except (ManifestError, OSError) as error:
        receipt["reason_codes"].append("MANIFEST_SCHEMA_ERROR")
        receipt["error"] = str(error)
    try:
        atomic_write_json(args.receipt.resolve(), receipt)
    except OSError as error:
        print(f"unable to write receipt: {error}", file=sys.stderr)
        return 2
    print(json.dumps(receipt, ensure_ascii=False))
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
