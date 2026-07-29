"""Independent revision-aware verifier for the task-012 M9 gate.

This module intentionally uses only the Python standard library.  Product
validator code is exercised by the held-out suite, but it is never trusted to
define the historical/candidate byte boundary verified here.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import pathlib
from typing import Any


REV8_RECORD_SHA256 = (
    "70e534c875aee40777f3b1c72fdb01d7c82a7fe788d6dd7a5ee06a2bae11d1ec"
)
REV8_VALIDATOR_BUNDLE_SHA256 = (
    "6ecf461025b36d854d745fbc60bae085f9b631dff1bf531719200d814a0f4a29"
)
VALIDATOR_BUNDLE_PATHS = {
    "scripts/yuan_activation.py",
    "scripts/yuan_authority.py",
    "scripts/yuan_m9_dogfood.py",
    "scripts/yuan_runtime_state.py",
    "scripts/yuan_runtime_transaction.py",
}
R2_REPLACED_PATHS = {
    "scripts/yuan_activation.py",
    "scripts/yuan_m9_dogfood.py",
    "scripts/yuan_runtime_state.py",
}
R2_SCRIPT_FILES = (
    "scripts/bootstrap_verifier.py",
    "scripts/bootstrap_verifier_support.py",
    "scripts/bootstrap-core-verifier.py",
    "scripts/verify-yuan-provenance.py",
    "scripts/yuan_activation.py",
    "scripts/yuan_authority.py",
    "scripts/yuan_m9_dogfood.py",
    "scripts/yuan_precommit.py",
    "scripts/yuan_provenance_history.py",
    "scripts/yuan_provenance_verify.py",
    "scripts/yuan_r2_successor.py",
    "scripts/yuan_runtime_seed.py",
    "scripts/yuan_runtime_state.py",
    "scripts/yuan_runtime_transaction.py",
    "scripts/yuan_shadow_migrate.py",
    "scripts/yuan_shadow_support.py",
    "scripts/yuan_successor_run.py",
    "scripts/yuan-authority.py",
    "scripts/yuan-provenance.py",
    "scripts/yuan-shadow-migrate.py",
)


class GateError(RuntimeError):
    """Fail-closed independent gate failure."""


def canonical(value: Any) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")


def digest_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def digest(path: pathlib.Path) -> str:
    try:
        return digest_bytes(path.read_bytes())
    except OSError as error:
        raise GateError(f"required file is unavailable: {path}") from error


def load_json(path: pathlib.Path) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise GateError(f"required JSON is unavailable: {path}") from error
    if not isinstance(value, dict):
        raise GateError(f"required JSON is not an object: {path}")
    return value


def _inside(root: pathlib.Path, relative: Any, label: str) -> pathlib.Path:
    if (
        not isinstance(relative, str)
        or not relative
        or "\\" in relative
        or pathlib.PurePosixPath(relative).is_absolute()
        or any(
            part in {"", ".", ".."}
            for part in pathlib.PurePosixPath(relative).parts
        )
    ):
        raise GateError(f"{label} path is invalid")
    root = root.resolve()
    path = (root / relative).resolve()
    try:
        path.relative_to(root)
    except ValueError as error:
        raise GateError(f"{label} path escapes the repository") from error
    return path


def gate_configuration(
    repo_root: pathlib.Path,
    *,
    mode: str,
    candidate_root: pathlib.Path | None,
) -> tuple[pathlib.Path, pathlib.Path]:
    repo = pathlib.Path(repo_root).resolve()
    if mode == "active":
        if candidate_root is not None:
            raise GateError("active mode forbids a candidate root")
        return repo, repo
    if mode != "candidate" or candidate_root is None:
        raise GateError("gate mode must be active or candidate with a root")
    candidate = pathlib.Path(candidate_root).resolve()
    if candidate == repo or not (candidate / "scripts").is_dir():
        raise GateError("candidate mode requires a distinct complete candidate")
    if not (candidate / ".yuan/core/0.1").is_dir():
        raise GateError("candidate Core is unavailable")
    return repo, candidate


def verify_validator_bundle(
    repo_root: pathlib.Path,
    manifest_sha256: str = REV8_VALIDATOR_BUNDLE_SHA256,
) -> dict[str, pathlib.Path]:
    repo = pathlib.Path(repo_root).resolve()
    root = repo / ".yuan/authority/validator-bundles" / manifest_sha256
    manifest_path = root / f"{manifest_sha256}.manifest.json"
    if digest(manifest_path) != manifest_sha256:
        raise GateError("validator bundle manifest hash mismatch")
    manifest = load_json(manifest_path)
    entries = manifest.get("files")
    if (
        manifest.get("schema_version") != "yuan.validator-bundle/v1"
        or not isinstance(entries, list)
        or len(entries) != len(VALIDATOR_BUNDLE_PATHS)
    ):
        raise GateError("validator bundle shape mismatch")
    result: dict[str, pathlib.Path] = {}
    for entry in entries:
        relative = entry.get("path") if isinstance(entry, dict) else None
        expected = entry.get("sha256") if isinstance(entry, dict) else None
        if (
            relative not in VALIDATOR_BUNDLE_PATHS
            or relative in result
            or not isinstance(expected, str)
        ):
            raise GateError("validator bundle entry mismatch")
        blob = root / f"{expected}.blob"
        if digest(blob) != expected:
            raise GateError("validator bundle blob hash mismatch")
        result[relative] = blob
    if set(result) != VALIDATOR_BUNDLE_PATHS:
        raise GateError("validator bundle path set mismatch")
    return result


def _rev8_transaction(
    repo: pathlib.Path,
    closure_sha256: str,
) -> tuple[pathlib.Path, dict[str, Any], dict[str, Any], dict[str, Any]]:
    matches = []
    root = repo / ".yuan/authority/self-modification/transactions"
    for journal_path in root.glob("*/journal.json"):
        journal = load_json(journal_path)
        prepared_path = journal_path.parent / "attempt-prepared.json"
        if (
            journal.get("schema_version")
            != "yuan.self-modification-transaction/v2"
            or journal.get("state") != "COMMITTED"
            or not prepared_path.is_file()
        ):
            continue
        prepared = load_json(prepared_path)
        proofs = (
            prepared.get("action", {})
            .get("self_modification", {})
            .get("proofs", [])
        )
        if (
            isinstance(proofs, list)
            and len(proofs) == 1
            and proofs[0].get("closure_index_sha256") == closure_sha256
        ):
            matches.append((journal_path.parent, journal, prepared, proofs[0]))
    if len(matches) != 1:
        raise GateError("rev8 causal transaction is missing or ambiguous")
    return matches[0]


def verify_rev8_history(
    repo_root: pathlib.Path,
    *,
    mode: str,
    candidate_root: pathlib.Path | None = None,
) -> dict[str, Any]:
    """Verify rev8 history against live bytes or the explicit r2 candidate.

    Candidate mode permits exactly the three r2 validator replacements.  Their
    old rev8 bytes must remain in the frozen bundle; all other old closure
    entries must still match the candidate directly.
    """
    repo, validation_root = gate_configuration(
        repo_root, mode=mode, candidate_root=candidate_root
    )
    current = load_json(repo / ".yuan/authority/current")
    if current.get("record_sha256") != REV8_RECORD_SHA256:
        raise GateError("active authority is not the frozen rev8 record")
    record_path = (
        repo / ".yuan/authority/records" / f"{REV8_RECORD_SHA256}.json"
    )
    record = load_json(record_path)
    if (
        digest_bytes(canonical(record)) != REV8_RECORD_SHA256
        or record.get("revision") != 8
    ):
        raise GateError("rev8 authority record mismatch")
    descriptor_path = (
        repo / ".yuan/authority/activation/yuan-core-0.1.json"
    )
    descriptor = load_json(descriptor_path)
    activation_binding = record.get("protocol_activation", {})
    if (
        digest(descriptor_path)
        != activation_binding.get("descriptor_sha256")
        or digest(_inside(repo, descriptor.get("protocol_path"), "rev8 protocol"))
        != activation_binding.get("protocol_sha256")
        or digest(
            _inside(
                repo,
                descriptor.get("candidate_manifest_path"),
                "rev8 candidate manifest",
            )
        )
        != activation_binding.get("candidate_manifest_sha256")
    ):
        raise GateError("rev8 activation descriptor binding mismatch")
    closure_path = _inside(
        repo, descriptor.get("proof_closure_index_path"), "rev8 closure"
    )
    closure_sha = descriptor.get("proof_closure_index_sha256")
    if (
        digest(closure_path) != closure_sha
        or closure_sha
        != activation_binding.get("proof_closure_index_sha256")
    ):
        raise GateError("rev8 closure index hash mismatch")
    closure = load_json(closure_path)
    if closure.get("schema_version") != "yuan.preflight-proof-closure/v1":
        raise GateError("rev8 closure schema mismatch")
    parent = closure_path.parent
    members = {
        "receipt": (
            closure.get("receipt_path"),
            closure.get("receipt_sha256"),
        ),
        "suite": (
            closure.get("suite_manifest_path"),
            closure.get("suite_manifest_sha256"),
        ),
        "verifier": (
            closure.get("verifier_path"),
            closure.get("verifier_sha256"),
        ),
        "full": (
            closure.get("full_candidate_manifest_path"),
            closure.get("full_candidate_manifest_sha256"),
        ),
    }
    member_paths: dict[str, pathlib.Path] = {}
    for label, (relative, expected) in members.items():
        path = _inside(repo, relative, f"rev8 {label}")
        if path.parent != parent or digest(path) != expected:
            raise GateError(f"rev8 {label} closure mismatch")
        member_paths[label] = path
    bundle = verify_validator_bundle(repo)
    full = load_json(member_paths["full"])
    entries = full.get("files")
    if (
        full.get("schema_version")
        != "yuan.self-modification-candidate/v1"
        or not isinstance(entries, list)
        or len(entries) != 42
    ):
        raise GateError("rev8 full candidate shape mismatch")
    differences: set[str] = set()
    seen: set[str] = set()
    for entry in entries:
        relative = entry.get("path") if isinstance(entry, dict) else None
        expected = entry.get("sha256") if isinstance(entry, dict) else None
        if (
            not isinstance(relative, str)
            or relative in seen
            or not isinstance(expected, str)
        ):
            raise GateError("rev8 full candidate entry mismatch")
        target = _inside(validation_root, relative, "rev8 candidate entry")
        if digest(target) != expected:
            differences.add(relative)
            archived = bundle.get(relative)
            if (
                mode != "candidate"
                or relative not in R2_REPLACED_PATHS
                or archived is None
                or digest(archived) != expected
            ):
                raise GateError("rev8 byte is neither current nor archived")
        seen.add(relative)
    expected_differences = R2_REPLACED_PATHS if mode == "candidate" else set()
    if differences != expected_differences:
        raise GateError("active/candidate revision boundary is ambiguous")
    tx, journal, prepared, proof = _rev8_transaction(repo, closure_sha)
    receipt = load_json(member_paths["receipt"])
    expected_proof = {
        "receipt_sha256": closure["receipt_sha256"],
        "suite_manifest_sha256": closure["suite_manifest_sha256"],
        "verifier_sha256": closure["verifier_sha256"],
        "closure_index_sha256": closure_sha,
        "full_candidate_manifest_sha256": closure[
            "full_candidate_manifest_sha256"
        ],
        "candidate_manifest_sha256": closure["candidate_manifest_sha256"],
        "receipt_created_at": closure["receipt_created_at"],
        "transaction_id": tx.name,
    }
    if any(proof.get(key) != value for key, value in expected_proof.items()):
        raise GateError("rev8 PREPARED proof binding mismatch")
    if (
        journal.get("prepared_attempt_sha256")
        != digest(tx / "attempt-prepared.json")
        or receipt.get("manifest_sha256") != closure["suite_manifest_sha256"]
    ):
        raise GateError("rev8 PREPARED snapshot mismatch")
    receipt_at = dt.datetime.fromisoformat(
        receipt["created_at"].replace("Z", "+00:00")
    )
    prepared_at = dt.datetime.fromisoformat(
        prepared["journal"][0]["recorded_at"].replace("Z", "+00:00")
    )
    if receipt_at > prepared_at:
        raise GateError("rev8 receipt postdates PREPARED")
    return {
        "mode": mode,
        "record_sha256": REV8_RECORD_SHA256,
        "closure_index_sha256": closure_sha,
        "validator_bundle_sha256": REV8_VALIDATOR_BUNDLE_SHA256,
        "candidate_differences": sorted(differences),
        "full_candidate_entries": len(entries),
        "transaction_id": tx.name,
    }


def verify_pointer_driven_rev8(repo_root: pathlib.Path) -> dict[str, Any]:
    """Independent baseline equivalent of the fixed public dogfood verifier."""
    repo = pathlib.Path(repo_root).resolve()
    current = load_json(repo / ".yuan/authority/current")
    record = load_json(
        repo
        / ".yuan/authority/records"
        / f"{current.get('record_sha256')}.json"
    )
    active_path = repo / ".yuan-run/active-run.json"
    active = load_json(active_path)
    runtime = _inside(repo, active.get("runtime_root"), "active runtime")
    manifest = runtime / "runtime-manifest.json"
    contracts = list((runtime / "contracts").glob("*.json"))
    if len(contracts) != 1:
        raise GateError("active Work is ambiguous")
    work = load_json(contracts[0])
    memory = load_json(runtime / "run-memory.json")
    if (
        current.get("record_sha256") != REV8_RECORD_SHA256
        or record.get("revision") != 8
        or record.get("runtime_root") != active.get("runtime_root")
        or record.get("runtime_pointer_sha256") != digest(active_path)
        or active.get("manifest_sha256") != digest(manifest)
        or work.get("revision", {}).get("revision") != "4"
        or memory.get("work_binding") != work.get("revision")
        or memory.get("protocol_binding") != work.get("protocol_binding")
        or memory.get("last_result") != "WAIT_AUTH"
    ):
        raise GateError("rev8/Work4 pointer-driven state mismatch")
    legal = memory.get("legal_next_steps")
    if (
        not isinstance(legal, list)
        or len(legal) != 1
        or legal[0].get("authorization_grant_id") is not None
        or any(
            "docs" in grant.get("scopes", [])
            for grant in work.get("authorization", {}).get("grants", [])
            if isinstance(grant, dict)
        )
    ):
        raise GateError("rev8 tombstone boundary mismatch")
    return {
        "authority_revision": 8,
        "work_revision": "4",
        "memory_result": "WAIT_AUTH",
    }


def candidate_full_manifest(
    candidate_root: pathlib.Path,
) -> dict[str, Any]:
    candidate = pathlib.Path(candidate_root).resolve()
    core_root = candidate / ".yuan/core/0.1"
    core_manifest = core_root / "candidate-manifest.json"
    paths = [
        path.relative_to(candidate).as_posix()
        for path in core_root.rglob("*")
        if path.is_file() and "__pycache__" not in path.parts
    ]
    paths.extend(R2_SCRIPT_FILES)
    paths = sorted(paths)
    if len(paths) != 55 or len(paths) != len(set(paths)):
        raise GateError("r2 candidate must contain exactly 55 unique files")
    files = []
    for relative in paths:
        path = _inside(candidate, relative, "r2 candidate")
        files.append({"path": relative, "sha256": digest(path)})
    return {
        "schema_version": "yuan.self-modification-candidate/v1",
        "candidate_revision": "yuan.validator-bundle/2",
        "core_candidate_manifest_sha256": digest(core_manifest),
        "files": files,
    }


def assert_candidate_matches_full_manifest(
    candidate_root: pathlib.Path,
    manifest: dict[str, Any],
) -> None:
    candidate = pathlib.Path(candidate_root).resolve()
    entries = manifest.get("files")
    if not isinstance(entries, list) or len(entries) != 55:
        raise GateError("candidate full manifest is incomplete")
    for entry in entries:
        relative = entry.get("path") if isinstance(entry, dict) else None
        expected = entry.get("sha256") if isinstance(entry, dict) else None
        path = _inside(candidate, relative, "bound candidate")
        if digest(path) != expected:
            raise GateError("candidate replacement is not closure-bound")


def verify_candidate_validator_bundle(
    repo_root: pathlib.Path,
    candidate_root: pathlib.Path,
    full_manifest: dict[str, Any],
    manifest_sha256: str,
) -> dict[str, pathlib.Path]:
    """Bind the new validator bundle to the same bytes as the v2 closure."""
    candidate = pathlib.Path(candidate_root).resolve()
    expected = {
        entry["path"]: entry["sha256"]
        for entry in full_manifest.get("files", [])
        if isinstance(entry, dict)
        and entry.get("path") in VALIDATOR_BUNDLE_PATHS
    }
    if set(expected) != VALIDATOR_BUNDLE_PATHS:
        raise GateError("full manifest omits candidate validator bytes")
    archived = verify_validator_bundle(repo_root, manifest_sha256)
    for relative, blob in archived.items():
        current = _inside(candidate, relative, "candidate validator")
        if (
            digest(blob) != expected[relative]
            or digest(current) != expected[relative]
        ):
            raise GateError("candidate validator bundle is not closure-bound")
    return archived


def _write_immutable(path: pathlib.Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and path.read_bytes() != payload:
        raise GateError(f"immutable path collision: {path}")
    path.write_bytes(payload)


def build_candidate_closure(
    repo_root: pathlib.Path,
    candidate_root: pathlib.Path,
    verifier_path: pathlib.Path,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Build an independent v2 closure in a disposable clone.

    The returned arguments are suitable for the candidate's public
    ``verify_preflight_closure`` seam.  The gate separately requires the
    candidate root to continue matching the full manifest.
    """
    repo = pathlib.Path(repo_root).resolve()
    candidate = pathlib.Path(candidate_root).resolve()
    full = candidate_full_manifest(candidate)
    full_bytes = canonical(full)
    full_sha = digest_bytes(full_bytes)

    bundle_entries = []
    bundle_payloads: dict[str, bytes] = {}
    for relative in sorted(VALIDATOR_BUNDLE_PATHS):
        payload = _inside(candidate, relative, "candidate validator").read_bytes()
        expected = digest_bytes(payload)
        bundle_entries.append({"path": relative, "sha256": expected})
        bundle_payloads[expected] = payload
    bundle = {
        "schema_version": "yuan.validator-bundle/v1",
        "files": bundle_entries,
    }
    bundle_bytes = canonical(bundle)
    bundle_sha = digest_bytes(bundle_bytes)
    bundle_root = repo / ".yuan/authority/validator-bundles" / bundle_sha
    for expected, payload in bundle_payloads.items():
        _write_immutable(bundle_root / f"{expected}.blob", payload)
    bundle_path = bundle_root / f"{bundle_sha}.manifest.json"
    _write_immutable(bundle_path, bundle_bytes)

    closure_root = (
        repo
        / ".yuan/authority/self-modification/evidence/preflight"
        / "task-012-r2-held-out"
    )
    full_path = closure_root / f"{full_sha}.candidate.json"
    _write_immutable(full_path, full_bytes)
    verifier_bytes = pathlib.Path(verifier_path).read_bytes()
    verifier_sha = digest_bytes(verifier_bytes)
    verifier_blob = closure_root / f"{verifier_sha}.blob"
    _write_immutable(verifier_blob, verifier_bytes)
    prepared = {
        "schema_version": "yuan.validator-upgrade-prepared/v1",
        "candidate_manifest_sha256": bundle_sha,
        "full_candidate_manifest_sha256": full_sha,
        "core_candidate_manifest_sha256": full[
            "core_candidate_manifest_sha256"
        ],
        "validator_bundle_before_sha256": REV8_VALIDATOR_BUNDLE_SHA256,
        "validator_bundle_after_sha256": bundle_sha,
    }
    prepared_bytes = canonical(prepared)
    prepared_sha = digest_bytes(prepared_bytes)
    prepared_path = closure_root / f"{prepared_sha}.prepared.json"
    _write_immutable(prepared_path, prepared_bytes)
    suite = {
        "schema_version": "yuan.independent-validator-suite/v1",
        "status": "PASS",
        "candidate_manifest_sha256": bundle_sha,
        "full_candidate_manifest_sha256": full_sha,
        "verifier_sha256": verifier_sha,
    }
    suite_bytes = canonical(suite)
    suite_sha = digest_bytes(suite_bytes)
    suite_path = closure_root / f"{suite_sha}.suite.json"
    _write_immutable(suite_path, suite_bytes)
    created_at = dt.datetime.now(dt.timezone.utc).isoformat().replace(
        "+00:00", "Z"
    )
    receipt = {
        "schema_version": "yuan.independent-validator-receipt/v1",
        "status": "PASS",
        "created_at": created_at,
        "manifest_sha256": suite_sha,
        "candidate_manifest_sha256": bundle_sha,
        "verifier_sha256": verifier_sha,
        "assertions": 1,
    }
    receipt_bytes = canonical(receipt)
    receipt_sha = digest_bytes(receipt_bytes)
    receipt_path = closure_root / f"{receipt_sha}.receipt.json"
    _write_immutable(receipt_path, receipt_bytes)

    def relative(path: pathlib.Path) -> str:
        return path.relative_to(repo).as_posix()

    index = {
        "schema_version": "yuan.preflight-proof-closure/v2",
        "receipt_path": relative(receipt_path),
        "receipt_sha256": receipt_sha,
        "receipt_created_at": created_at,
        "suite_manifest_path": relative(suite_path),
        "suite_manifest_sha256": suite_sha,
        "verifier_path": relative(verifier_blob),
        "verifier_sha256": verifier_sha,
        "full_candidate_manifest_path": relative(full_path),
        "full_candidate_manifest_sha256": full_sha,
        "candidate_manifest_sha256": bundle_sha,
        "prepared_snapshot_path": relative(prepared_path),
        "prepared_snapshot_sha256": prepared_sha,
    }
    index_bytes = canonical(index)
    index_sha = digest_bytes(index_bytes)
    index_path = closure_root / f"{index_sha}.index.json"
    _write_immutable(index_path, index_bytes)
    old_bundle_path = (
        repo
        / ".yuan/authority/validator-bundles"
        / REV8_VALIDATOR_BUNDLE_SHA256
        / f"{REV8_VALIDATOR_BUNDLE_SHA256}.manifest.json"
    )
    if digest(old_bundle_path) != REV8_VALIDATOR_BUNDLE_SHA256:
        raise GateError("rev8 validator bundle is unavailable")
    arguments = {
        "closure_index_path": relative(index_path),
        "closure_index_sha256": index_sha,
        "candidate_manifest_sha256": bundle_sha,
        "core_candidate_manifest_sha256": full[
            "core_candidate_manifest_sha256"
        ],
        "expected_verifier_sha256": verifier_sha,
        "prepared_snapshot_path": relative(prepared_path),
        "prepared_snapshot_sha256": prepared_sha,
        "candidate_root": candidate,
        "archived_bundle_manifest_path": relative(old_bundle_path),
        "archived_bundle_manifest_sha256": REV8_VALIDATOR_BUNDLE_SHA256,
    }
    return arguments, {
        "bundle": bundle,
        "bundle_path": bundle_path,
        "full": full,
        "full_path": full_path,
        "verifier_path": verifier_blob,
        "prepared_path": prepared_path,
        "archived_bundle_path": old_bundle_path,
        "suite_path": suite_path,
        "receipt_path": receipt_path,
        "index_path": index_path,
    }
