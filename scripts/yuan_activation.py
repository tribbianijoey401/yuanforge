"""Mechanical older-root activation binding for the inert Core candidate."""

from __future__ import annotations

import json
import pathlib
from typing import Any

from yuan_runtime_state import AuthorityError, file_sha256


DESCRIPTOR_PATH = pathlib.PurePosixPath(
    ".yuan/authority/activation/yuan-core-0.1.json"
)


def _inside(repo: pathlib.Path, relative: str) -> pathlib.Path:
    path = (repo / relative).resolve()
    try:
        path.relative_to(repo)
    except ValueError as error:
        raise AuthorityError("activation binding escapes the repository") from error
    return path


def _json(path: pathlib.Path, label: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise AuthorityError(f"{label} is missing or invalid") from error
    if not isinstance(value, dict):
        raise AuthorityError(f"{label} must be a JSON object")
    return value


def _verify_candidate_manifest(
    repo: pathlib.Path,
    path: pathlib.Path,
    expected_sha256: str,
) -> dict[str, Any]:
    if file_sha256(path) != expected_sha256:
        raise AuthorityError("activated candidate manifest hash mismatch")
    manifest = _json(path, "activated candidate manifest")
    entries = manifest.get("files")
    if (
        manifest.get("schema_version") != "yuan.core-candidate-manifest/v1"
        or not isinstance(entries, list)
        or not entries
    ):
        raise AuthorityError("activated candidate manifest shape mismatch")
    root = path.parent.resolve()
    seen: set[str] = set()
    for entry in entries:
        relative = entry.get("path") if isinstance(entry, dict) else None
        expected = entry.get("sha256") if isinstance(entry, dict) else None
        if (
            not isinstance(relative, str)
            or not relative
            or "\\" in relative
            or relative in seen
            or not isinstance(expected, str)
            or len(expected) != 64
        ):
            raise AuthorityError("activated candidate manifest entry invalid")
        target = (root / relative).resolve()
        try:
            target.relative_to(root)
        except ValueError as error:
            raise AuthorityError("candidate manifest entry escapes Core") from error
        if not target.is_file() or file_sha256(target) != expected:
            raise AuthorityError("activated candidate file binding mismatch")
        seen.add(relative)
    return manifest


def _verify_suite_manifest(
    suite: dict[str, Any],
    candidate: dict[str, Any],
    candidate_sha256: str,
) -> None:
    cases = [
        item
        for item in suite.get("cases", [])
        if isinstance(item, dict) and item.get("id") == "yuan-core-01-candidate"
    ]
    if len(cases) != 1:
        raise AuthorityError("older-root suite candidate case is ambiguous")
    required = {
        item.get("path"): item.get("sha256")
        for item in cases[0].get("required_files", [])
        if isinstance(item, dict)
    }
    expected = {
        item["path"]: item["sha256"]
        for item in candidate["files"]
    }
    expected["candidate-manifest.json"] = candidate_sha256
    if required != expected:
        raise AuthorityError("older-root suite does not bind activated Core files")


def verify_activation_descriptor(
    repo_root: pathlib.Path,
    descriptor_path: pathlib.Path | None = None,
) -> dict[str, Any]:
    repo = pathlib.Path(repo_root).resolve()
    path = (
        pathlib.Path(descriptor_path).resolve()
        if descriptor_path is not None
        else repo / DESCRIPTOR_PATH
    )
    try:
        path.relative_to(repo)
        descriptor = _json(path, "Core activation descriptor")
    except (AuthorityError, ValueError) as error:
        raise AuthorityError("Core activation descriptor is missing or invalid") from error
    protocol = repo / ".yuan/core/0.1/protocol.md"
    candidate_path = _inside(repo, descriptor.get("candidate_manifest_path", ""))
    evidence = _inside(repo, descriptor.get("independent_evidence_path", ""))
    old_suite_path = _inside(repo, descriptor.get("older_root_manifest_path", ""))
    active_suite_path = _inside(
        repo, descriptor.get("activated_older_root_manifest_path", "")
    )
    previous_descriptor = _inside(
        repo, descriptor.get("previous_descriptor_path", "")
    )
    verifier = _inside(repo, descriptor.get("older_root_verifier_path", ""))
    expected_verifier = descriptor.get("older_root_verifier_sha256", "")
    if not verifier.is_file():
        verifier = (
            repo
            / ".yuan/authority/activation/verifiers"
            / f"{expected_verifier}.blob"
        )
    receipt = _json(evidence, "Core activation Evidence")
    old_suite = _json(old_suite_path, "older-root suite manifest")
    active_suite = _json(active_suite_path, "activated older-root suite manifest")
    activated_sha = descriptor.get("activated_candidate_manifest_sha256", "")
    candidate = _verify_candidate_manifest(repo, candidate_path, activated_sha)
    _verify_suite_manifest(active_suite, candidate, activated_sha)
    previous_sha = descriptor.get("previous_candidate_manifest_sha256", "")
    prior_sha = descriptor.get("prior_activated_candidate_manifest_sha256", "")
    previous_blob = (
        repo
        / ".yuan/authority/core-history/m7-to-m8/blobs"
        / f"{previous_sha}.blob"
    )
    prior_blob = (
        repo
        / ".yuan/authority/core-history/m8-r1-to-r2/blobs"
        / f"{prior_sha}.blob"
    )
    candidate_cases = [
        item
        for item in receipt.get("cases", [])
        if item.get("id") == "yuan-core-01-candidate"
    ]
    accepted = (
        len(candidate_cases) == 1
        and candidate_cases[0].get("observed") == "ACCEPT"
        and candidate_cases[0].get("matched") is True
        and candidate_cases[0].get("validator", {}).get("assertions", 0) > 0
    )
    if (
        descriptor.get("schema_version") != "yuan.core-activation/v2"
        or descriptor.get("accepted_by_authority") != "legacy"
        or descriptor.get("protocol_sha256") != file_sha256(protocol)
        or descriptor.get("candidate_manifest_sha256") != activated_sha
        or not previous_blob.is_file()
        or file_sha256(previous_blob) != previous_sha
        or not prior_blob.is_file()
        or file_sha256(prior_blob) != prior_sha
        or descriptor.get("older_root_manifest_sha256")
        != file_sha256(old_suite_path)
        or descriptor.get("activated_older_root_manifest_sha256")
        != file_sha256(active_suite_path)
        or descriptor.get("independent_evidence_sha256") != file_sha256(evidence)
        or descriptor.get("older_root_receipt_sha256") != file_sha256(evidence)
        or expected_verifier != file_sha256(verifier)
        or descriptor.get("previous_descriptor_sha256")
        != file_sha256(previous_descriptor)
        or receipt.get("manifest_sha256") != file_sha256(active_suite_path)
        or receipt.get("status") != "PASS"
        or receipt.get("checks_executed", 0) < 80
        or not accepted
    ):
        raise AuthorityError("Core activation older-root proof did not PASS")
    return {
        "schema_version": "yuan.protocol-activation-binding/v1",
        "protocol_sha256": descriptor["protocol_sha256"],
        "previous_candidate_manifest_sha256": previous_sha,
        "prior_activated_candidate_manifest_sha256": prior_sha,
        "activated_candidate_manifest_sha256": activated_sha,
        "candidate_manifest_sha256": activated_sha,
        "older_root_manifest_sha256": descriptor["older_root_manifest_sha256"],
        "activated_older_root_manifest_sha256": descriptor[
            "activated_older_root_manifest_sha256"
        ],
        "accepted_by_authority": "legacy",
        "independent_evidence_sha256": descriptor[
            "independent_evidence_sha256"
        ],
        "older_root_verifier_sha256": descriptor[
            "older_root_verifier_sha256"
        ],
        "descriptor_sha256": file_sha256(path),
        "assertions": receipt["checks_executed"],
    }
