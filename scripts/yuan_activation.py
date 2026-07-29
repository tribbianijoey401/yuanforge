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
        descriptor = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as error:
        raise AuthorityError("Core activation descriptor is missing or invalid") from error
    protocol = repo / ".yuan/core/0.1/protocol.md"
    candidate = repo / ".yuan/core/0.1/candidate-manifest.json"
    evidence = _inside(repo, descriptor.get("independent_evidence_path", ""))
    verifier = _inside(repo, descriptor.get("older_root_verifier_path", ""))
    expected_verifier = descriptor.get("older_root_verifier_sha256", "")
    if not verifier.is_file():
        verifier = (
            repo
            / ".yuan/authority/activation/verifiers"
            / f"{expected_verifier}.blob"
        )
    try:
        receipt = json.loads(evidence.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise AuthorityError("Core activation Evidence is missing or invalid") from error
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
        descriptor.get("schema_version") != "yuan.core-activation/v1"
        or descriptor.get("accepted_by_authority") != "legacy"
        or descriptor.get("protocol_sha256") != file_sha256(protocol)
        or descriptor.get("candidate_manifest_sha256") != file_sha256(candidate)
        or descriptor.get("independent_evidence_sha256") != file_sha256(evidence)
        or expected_verifier != file_sha256(verifier)
        or receipt.get("status") != "PASS"
        or receipt.get("checks_executed", 0) < 80
        or not accepted
    ):
        raise AuthorityError("Core activation older-root proof did not PASS")
    return {
        "schema_version": "yuan.protocol-activation-binding/v1",
        "protocol_sha256": descriptor["protocol_sha256"],
        "candidate_manifest_sha256": descriptor["candidate_manifest_sha256"],
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
