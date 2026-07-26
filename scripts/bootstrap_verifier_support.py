"""Filesystem and receipt helpers for the Yuan bootstrap verifier."""

from __future__ import annotations

import hashlib
import json
import os
import pathlib
import re
import tempfile
from datetime import datetime, timezone
from typing import Any


VERIFIER_REVISION = "yuan.bootstrap-verifier/1"
SUITE_SCHEMA = "yuan.bootstrap-suite/v1"
RESULT_SCHEMA = "yuan.validator-result/v1"
RECEIPT_SCHEMA = "yuan.bootstrap-receipt/v1"
SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")
PLACEHOLDER_FILES = {".gitkeep", ".keep"}
NEGATIVE_CONTRACT = {
    "empty_candidate": "EMPTY_CANDIDATE",
    "known_bad": "CHECK_FAILED",
    "zero_assertions": "ZERO_ASSERTIONS",
    "validator_error": "VALIDATOR_ERROR",
    "parse_error": "RESULT_PARSE_ERROR",
}


class ManifestError(ValueError):
    """The trusted manifest does not satisfy the bootstrap contract."""


def file_sha256(path: pathlib.Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def atomic_write_json(path: pathlib.Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(value, ensure_ascii=False, indent=2) + "\n"
    temporary_name: str | None = None
    try:
        with tempfile.NamedTemporaryFile(
            "w",
            encoding="utf-8",
            newline="\n",
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
            temporary_name = stream.name
        os.replace(temporary_name, path)
    finally:
        if temporary_name and os.path.exists(temporary_name):
            os.unlink(temporary_name)


def receipt_base(manifest_path: pathlib.Path) -> dict[str, Any]:
    return {
        "schema_version": RECEIPT_SCHEMA,
        "verifier_revision": VERIFIER_REVISION,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "manifest_path": str(manifest_path),
        "manifest_sha256": None,
        "suite_id": None,
        "status": "FAIL",
        "reason_codes": [],
        "checks_executed": 0,
        "cases": [],
    }


def resolve_within(root: pathlib.Path, relative: Any, field: str) -> pathlib.Path:
    if not isinstance(relative, str) or not relative or pathlib.Path(relative).is_absolute():
        raise ManifestError(f"{field} must be a non-empty relative path")
    resolved = (root / relative).resolve()
    try:
        resolved.relative_to(root)
    except ValueError as error:
        raise ManifestError(f"{field} escapes the manifest directory") from error
    return resolved


def meaningful_files(candidate: pathlib.Path) -> list[pathlib.Path]:
    if not candidate.is_dir():
        return []
    return sorted(
        (
            path
            for path in candidate.rglob("*")
            if path.is_file()
            and not path.is_symlink()
            and path.name not in PLACEHOLDER_FILES
        ),
        key=lambda path: path.relative_to(candidate).as_posix(),
    )


def tree_digest(candidate: pathlib.Path, files: list[pathlib.Path]) -> str | None:
    if not files:
        return None
    digest = hashlib.sha256()
    for path in files:
        relative = path.relative_to(candidate).as_posix()
        digest.update(relative.encode("utf-8"))
        digest.update(b"\0")
        digest.update(file_sha256(path).encode("ascii"))
        digest.update(b"\n")
    return digest.hexdigest()


def validate_hash_specs(
    specs: Any,
    root: pathlib.Path,
    field: str,
) -> list[tuple[pathlib.Path, str, str]]:
    if not isinstance(specs, list):
        raise ManifestError(f"{field} must be a list")
    validated: list[tuple[pathlib.Path, str, str]] = []
    seen: set[str] = set()
    for index, spec in enumerate(specs):
        if not isinstance(spec, dict):
            raise ManifestError(f"{field}[{index}] must be an object")
        relative = spec.get("path")
        expected_hash = spec.get("sha256")
        path = resolve_within(root, relative, f"{field}[{index}].path")
        if relative in seen:
            raise ManifestError(f"{field} contains duplicate path {relative!r}")
        if not isinstance(expected_hash, str) or not SHA256_PATTERN.fullmatch(
            expected_hash
        ):
            raise ManifestError(f"{field}[{index}].sha256 is not lowercase SHA-256")
        seen.add(relative)
        validated.append((path, relative, expected_hash))
    return validated


def expand_trusted_command(
    command: Any,
    *,
    root: pathlib.Path,
    candidate: pathlib.Path,
    trusted: list[tuple[pathlib.Path, str, str]],
    field: str,
    python_executable: str,
) -> list[str]:
    if (
        not isinstance(command, list)
        or not command
        or not all(isinstance(token, str) and token for token in command)
    ):
        raise ManifestError(f"{field} is invalid")
    uses_python = command[0] == "{python}"
    if uses_python and (
        len(command) < 2
        or command[1] in {"{python}", "{candidate}"}
        or command[1].startswith("-")
    ):
        raise ManifestError(f"{field} requires a trusted script after {{python}}")
    trusted_paths = {path for path, _, _ in trusted}
    expanded: list[str] = []
    for index, token in enumerate(command):
        if token == "{python}":
            if index != 0:
                raise ManifestError(f"{field} uses {{python}} outside argv[0]")
            expanded.append(python_executable)
        elif token == "{candidate}":
            if index == 0:
                raise ManifestError(f"{field} cannot execute the candidate")
            expanded.append(str(candidate))
        elif "{" in token or "}" in token:
            raise ManifestError(f"{field} contains an unknown placeholder")
        elif token.startswith("-"):
            if not re.fullmatch(r"--?[A-Za-z0-9][A-Za-z0-9_.:@+-]*(?:=[A-Za-z0-9_.:@+-]+)?", token):
                raise ManifestError(f"{field}[{index}] contains an unsafe option")
            expanded.append(token)
        else:
            bound_path = resolve_within(root, token, f"{field}[{index}]")
            if bound_path not in trusted_paths:
                raise ManifestError(f"{field}[{index}] is not bound by trusted_files")
            expanded.append(str(bound_path))
    if not uses_python and pathlib.Path(expanded[0]) not in trusted_paths:
        raise ManifestError(f"{field}[0] is not a trusted executable")
    return expanded


def collect_protected_inputs(
    manifest: dict[str, Any],
    root: pathlib.Path,
    manifest_path: pathlib.Path,
) -> list[pathlib.Path]:
    cases = manifest.get("cases")
    if not isinstance(cases, list):
        raise ManifestError("cases must be a list")
    protected = [manifest_path]
    for index, case in enumerate(cases):
        if not isinstance(case, dict):
            raise ManifestError(f"cases[{index}] must be an object")
        candidate = resolve_within(
            root,
            case.get("candidate"),
            f"cases[{index}].candidate",
        )
        protected.append(candidate)
        validator = case.get("validator")
        if not isinstance(validator, dict):
            raise ManifestError(f"cases[{index}].validator must be an object")
        trusted = validate_hash_specs(
            validator.get("trusted_files"),
            root,
            f"cases[{index}].validator.trusted_files",
        )
        protected.extend(path for path, _, _ in trusted)
    return list(dict.fromkeys(protected))


def paths_overlap(left: pathlib.Path, right: pathlib.Path) -> bool:
    return (
        left == right
        or left in right.parents
        or right in left.parents
    )
