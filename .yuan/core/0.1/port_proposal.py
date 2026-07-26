"""Build proposal-only receipts without interpreting or executing proposals."""

from __future__ import annotations

import hashlib
import json
import uuid
from datetime import datetime, timezone
from typing import Any

from port_types import PortError, ProposalProvider


def _canonical_bytes(value: object) -> bytes:
    try:
        encoded = json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        )
    except (TypeError, ValueError) as error:
        raise PortError("proposal data must be canonical JSON") from error
    return encoded.encode("utf-8")


def build_proposal_receipt(
    provider: ProposalProvider,
    request: dict[str, Any],
) -> dict[str, Any]:
    if not isinstance(request, dict):
        raise PortError("proposal request must be a mapping")
    input_bytes = _canonical_bytes(request)
    input_sha256 = hashlib.sha256(input_bytes).hexdigest()
    request_snapshot = json.loads(input_bytes)
    result = provider.propose(request_snapshot)
    if (
        not isinstance(result, dict)
        or not isinstance(result.get("proposal"), dict)
        or not result["proposal"]
        or (
            "action" in result["proposal"]
            and not isinstance(result["proposal"]["action"], dict)
        )
    ):
        raise PortError("proposal provider returned a malformed proposal")
    result_bytes = _canonical_bytes(result)
    result_snapshot = json.loads(result_bytes)
    result_sha256 = hashlib.sha256(result_bytes).hexdigest()
    provider_id = getattr(provider, "provider_id", None)
    if not isinstance(provider_id, str) or not provider_id.strip():
        provider_type = type(provider)
        provider_id = f"{provider_type.__module__}.{provider_type.__qualname__}"
    model_id = getattr(provider, "model_id", None)
    if model_id is not None and (
        not isinstance(model_id, str) or not model_id.strip()
    ):
        raise PortError("proposal provider model_id must be a non-empty string")
    binding = {
        "input_sha256": input_sha256,
        "provider_id": provider_id,
        "model_id": model_id,
        "result_sha256": result_sha256,
    }
    return {
        "schema_version": "yuan.tool-receipt/v1",
        "kind": "llm-propose",
        "operation_id": str(uuid.uuid4()),
        "status": "PROPOSED",
        **binding,
        "binding_sha256": hashlib.sha256(_canonical_bytes(binding)).hexdigest(),
        "proposal": result_snapshot["proposal"],
        "proposed_at": datetime.now(timezone.utc).isoformat(),
    }
