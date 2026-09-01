from __future__ import annotations

import json
from pathlib import Path


class ConfigError(ValueError):
    """The project-level configuration error exposed to callers."""


DEFAULT_TIMEOUT_SECONDS = 30


def load_settings(path: Path) -> dict[str, object]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ConfigError("settings file is unreadable") from exc
    if not isinstance(payload, dict) or not isinstance(payload.get("name"), str):
        raise ConfigError("settings require a string name")
    return {"name": payload["name"]}
