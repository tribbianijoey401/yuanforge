"""Deny-by-default scope, authorization, grant-use, and budget reduction."""

from __future__ import annotations

import pathlib
from datetime import datetime
from typing import Any

from document_validation import validate_document
from trust_semantics import parse_trusted_time, trusted_now as resolve_trusted_now


def _scope_contains(parent: str, child: str) -> bool:
    parent_path = pathlib.PurePosixPath(parent.replace("\\", "/"))
    child_path = pathlib.PurePosixPath(child.replace("\\", "/"))
    if child_path.is_absolute() or ".." in child_path.parts:
        return False
    return child_path == parent_path or parent_path in child_path.parents


def authorization_status(
    work: dict[str, Any],
    action: dict[str, Any],
    charge: dict[str, Any],
    remaining: dict[str, Any],
    *,
    trusted_now: datetime | None = None,
    grant_usage: dict[str, int] | None = None,
) -> str:
    if validate_document("work-contract", work).errors:
        return "BLOCKED"
    scope = action.get("scope")
    if not isinstance(scope, str):
        return "BLOCKED"
    declared_scope = work["scope"]
    if (
        action.get("side_effect_class") not in declared_scope["side_effect_classes"]
        or not any(
            _scope_contains(item, scope) for item in declared_scope["allowed_paths"]
        )
        or any(_scope_contains(item, scope) for item in declared_scope["denied_paths"])
    ):
        return "BLOCKED"
    grant = next(
        (
            item
            for item in work["authorization"]["grants"]
            if item["id"] == action.get("authorization_grant_id")
        ),
        None,
    )
    if (
        grant is None
        or action.get("type") not in grant["action_types"]
        or action.get("side_effect_class") not in grant["side_effect_classes"]
        or not any(_scope_contains(item, scope) for item in grant["scopes"])
        or (action.get("high_impact") is True and grant["high_impact"] is not True)
    ):
        return "WAIT_AUTH"
    observed_now = resolve_trusted_now(trusted_now)
    expires_at = grant.get("expires_at")
    if expires_at is not None:
        try:
            if observed_now > parse_trusted_time(expires_at):
                return "WAIT_AUTH"
        except (TypeError, ValueError):
            return "WAIT_AUTH"
    max_uses = grant.get("max_uses")
    uses = (grant_usage or {}).get(grant["id"], 0)
    if max_uses is not None and (
        not isinstance(uses, int)
        or isinstance(uses, bool)
        or uses < 0
        or uses >= max_uses
    ):
        return "WAIT_AUTH"
    budget_fields = ("ticks", "tool_calls", "strategies", "command_seconds")
    if any(
        not isinstance(charge.get(item), (int, float))
        or isinstance(charge.get(item), bool)
        or charge[item] < 0
        or charge[item] > remaining.get(item, -1)
        for item in budget_fields
    ):
        return "BUDGET_EXIT"
    return "AUTHORIZED"
