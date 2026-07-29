"""Deterministic trust helpers shared by Core conformance and replay."""

from __future__ import annotations

import copy
import hashlib
import json
from datetime import datetime, timezone
from typing import Any, Iterable


PROTECTED_SELF_MOD_TARGETS = {"protocol", "core", "harness", "validator", "authority"}
SHA256_LENGTH = 64


def canonical_digest(
    value: Any,
    *,
    omitted_paths: Iterable[tuple[str, ...]] = (),
) -> str:
    canonical = copy.deepcopy(value)
    for path in omitted_paths:
        current = canonical
        for token in path[:-1]:
            if not isinstance(current, dict) or token not in current:
                break
            current = current[token]
        else:
            if isinstance(current, dict):
                current.pop(path[-1], None)
    payload = json.dumps(
        canonical,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def parse_trusted_time(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("trusted timestamps must include a timezone")
    return parsed.astimezone(timezone.utc)


def trusted_now(value: datetime | None) -> datetime:
    observed = value or datetime.now(timezone.utc)
    if observed.tzinfo is None:
        raise ValueError("trusted clock must be timezone-aware")
    return observed.astimezone(timezone.utc)


def immutable_binding_matches(left: Any, right: Any) -> bool:
    keys = ("id", "revision", "sha256")
    return (
        isinstance(left, dict)
        and isinstance(right, dict)
        and all(left.get(key) == right.get(key) for key in keys)
    )


def _proof_closure_valid(
    proof: dict[str, Any],
    candidate: dict[str, Any],
    *,
    observed_now: datetime,
    prepared_at: str | None,
) -> bool:
    """Validate the content-addressed proof that existed before mutation."""
    # Compatibility is confined to replay of pre-0.1.1 frozen Work.  The
    # 0.1.1 replay path always supplies ``prepared_at`` and therefore always
    # requires the complete closure below.
    if prepared_at is None:
        return True
    required_hashes = (
        "receipt_sha256",
        "suite_manifest_sha256",
        "candidate_manifest_sha256",
        "verifier_sha256",
    )
    if any(
        not isinstance(proof.get(field), str)
        or len(proof[field]) != SHA256_LENGTH
        or any(token not in "0123456789abcdef" for token in proof[field])
        for field in required_hashes
    ):
        return False
    if proof["candidate_manifest_sha256"] != candidate.get("sha256"):
        return False
    try:
        receipt_at = parse_trusted_time(proof["receipt_created_at"])
        prepared = parse_trusted_time(prepared_at) if prepared_at else None
    except (KeyError, TypeError, ValueError):
        return False
    return (
        receipt_at <= observed_now
        and prepared is not None
        and receipt_at <= prepared
        and prepared <= observed_now
    )


def self_modification_authorized(
    change: dict[str, Any],
    proofs: list[dict[str, Any]],
    *,
    now: datetime | None = None,
    prepared_at: str | None = None,
) -> bool:
    if change.get("target_kind") not in PROTECTED_SELF_MOD_TARGETS:
        return False
    candidate = change.get("candidate_binding")
    previous = change.get("previous_binding")
    risk = change.get("risk")
    if not all(
        isinstance(item, dict)
        and isinstance(item.get("revision"), str)
        and isinstance(item.get("sha256"), str)
        for item in (candidate, previous)
    ) or not isinstance(risk, str):
        return False
    observed_now = trusted_now(now)
    for proof in proofs:
        if not isinstance(proof, dict):
            continue
        kind = proof.get("kind")
        if (
            kind == "previous-root"
            and immutable_binding_matches(proof.get("root_binding"), previous)
            and immutable_binding_matches(proof.get("candidate_binding"), candidate)
            and proof.get("status") == "PASS"
            and isinstance(proof.get("assertions"), int)
            and not isinstance(proof.get("assertions"), bool)
            and proof["assertions"] > 0
            and _proof_closure_valid(
                proof,
                candidate,
                observed_now=observed_now,
                prepared_at=prepared_at,
            )
        ):
            return True
        if (
            kind == "independent-root"
            and proof.get("independent") is True
            and proof.get("root_id") not in {candidate.get("id"), previous.get("id")}
            and immutable_binding_matches(proof.get("candidate_binding"), candidate)
            and proof.get("status") == "PASS"
            and isinstance(proof.get("assertions"), int)
            and not isinstance(proof.get("assertions"), bool)
            and proof["assertions"] > 0
            and _proof_closure_valid(
                proof,
                candidate,
                observed_now=observed_now,
                prepared_at=prepared_at,
            )
        ):
            return True
        if kind == "human-grant":
            try:
                authorized = parse_trusted_time(proof["authorized_at"])
                expires = parse_trusted_time(proof["expires_at"])
            except (KeyError, TypeError, ValueError):
                continue
            if (
                proof.get("human_id")
                and proof.get("grant_id")
                and proof.get("candidate_revision") == candidate.get("revision")
                and proof.get("candidate_sha256") == candidate.get("sha256")
                and proof.get("risk") == risk
                and authorized <= observed_now
                and observed_now <= expires
            ):
                return True
    return False
