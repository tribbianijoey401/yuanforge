"""Adapter Descriptor 验证与 Profile 真实性检查。"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .canonical import digest_bytes, verify_digest
from .errors import ValidationError
from .validate import identifier, require, sha256


CAPABILITIES = {
    "artifact_audit",
    "scoped_file_cas",
    "bounded_command",
    "llm_proposal",
    "physical_effect_mediation",
}


def validate_adapter_descriptor(value: Any, root: Path | None = None) -> dict[str, Any]:
    require(isinstance(value, dict), "Adapter Descriptor 必须是 Object")
    require(
        set(value) == {"schema_version", "adapter_id", "platform", "profile", "capabilities", "port", "notes", "digest"},
        "Adapter Descriptor 字段不合法",
    )
    require(value["schema_version"] == "yuan.adapter/v1", "Adapter Schema Version 不受支持")
    identifier(value["adapter_id"], "adapter_id")
    identifier(value["platform"], "platform")
    require(value["profile"] in {"GUIDED", "AUDITED", "ENFORCED"}, "Adapter Profile 不合法")
    capabilities = value["capabilities"]
    require(isinstance(capabilities, dict) and set(capabilities) == CAPABILITIES, "Adapter Capability 集合不完整")
    for name, item in capabilities.items():
        require(isinstance(item, dict) and set(item) == {"status", "reason"}, f"Capability {name} 字段不合法")
        require(item["status"] in {"SUPPORTED", "UNSUPPORTED"}, f"Capability {name} Status 不合法")
        require(isinstance(item["reason"], str) and item["reason"].strip(), f"Capability {name} 缺少原因")
    if value["profile"] == "ENFORCED":
        require(
            capabilities["physical_effect_mediation"]["status"] == "SUPPORTED",
            "ENFORCED Adapter 必须提供 Physical Effect Mediation",
        )
    port = value["port"]
    if port is None:
        require(
            capabilities["physical_effect_mediation"]["status"] == "UNSUPPORTED",
            "没有 Port Binding 时不得声明 Physical Effect Mediation",
        )
    else:
        require(isinstance(port, dict) and set(port) == {"id", "revision", "path", "digest"}, "Port Binding 字段不合法")
        identifier(port["id"], "port.id")
        identifier(port["revision"], "port.revision")
        sha256(port["digest"], "port.digest")
        require(isinstance(port["path"], str) and port["path"], "port.path 不合法")
        if root is not None:
            target = (root.resolve() / port["path"]).resolve()
            try:
                target.relative_to(root.resolve())
            except ValueError as exc:
                raise ValidationError("Port Binding Path 逃逸 Root") from exc
            require(target.is_file() and digest_bytes(target.read_bytes()) == port["digest"], "Port Binding Digest 不匹配")
    require(isinstance(value["notes"], str), "Adapter notes 必须是 String")
    require(verify_digest(value), "Adapter Descriptor Digest 不匹配")
    return value
