"""Derive minimal pending side-effect pointers from immutable Attempts."""

from __future__ import annotations

from typing import Any, Callable

from trust_semantics import immutable_binding_matches


PENDING_STATES = {"PREPARED", "EXECUTING", "OBSERVED", "UNKNOWN"}
PURE_ACTION_TYPES = {"file-read", "verify", "llm-propose"}


def rebuild_pending_side_effects(
    work: dict[str, Any],
    attempts: list[dict[str, Any]],
    *,
    validate_document: Callable[[str, dict[str, Any]], Any],
    work_is_valid: bool,
    attempts_digest_trusted: bool,
) -> list[dict[str, str]]:
    """Return stable Attempt pointers; the Attempt remains the fact source."""
    ids = [item.get("attempt_id") for item in attempts if isinstance(item, dict)]
    sequences = [item.get("sequence") for item in attempts if isinstance(item, dict)]
    if (
        not work_is_valid
        or len(ids) != len(attempts)
        or len(ids) != len(set(ids))
        or any(not item for item in ids)
        or sequences != list(range(1, len(attempts) + 1))
    ):
        return []
    pending: list[dict[str, str]] = []
    for attempt in attempts:
        action = attempt.get("action", {})
        state = attempt.get("side_effect_state")
        if (
            validate_document("attempt", attempt).errors
            or not immutable_binding_matches(
                attempt.get("work_binding"), work.get("revision")
            )
            or not immutable_binding_matches(
                attempt.get("protocol_binding"), work.get("protocol_binding")
            )
            or not immutable_binding_matches(
                attempt.get("harness_binding"), work.get("harness_binding")
            )
            or action.get("mutating") is not True
            or action.get("type") in PURE_ACTION_TYPES
            or action.get("side_effect_class") == "none"
            or not isinstance(action.get("scope"), str)
            or not action["scope"]
            or state not in PENDING_STATES
        ):
            continue
        pending.append(
            {
                "attempt_id": attempt["attempt_id"],
                "state": state if attempts_digest_trusted else "UNKNOWN",
            }
        )
    return pending
