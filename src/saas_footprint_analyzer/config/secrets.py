from __future__ import annotations

import os
import re
from typing import Any

ENV_PATTERN = re.compile(r"\$\{([A-Z0-9_]+)\}")


def resolve_env_placeholders(value: Any) -> Any:
    if isinstance(value, str):
        return _resolve_string(value)
    if isinstance(value, list):
        return [resolve_env_placeholders(item) for item in value]
    if isinstance(value, dict):
        return {key: resolve_env_placeholders(item) for key, item in value.items()}
    return value


def _resolve_string(raw: str) -> str:
    def replacement(match: re.Match[str]) -> str:
        key = match.group(1)
        if key not in os.environ:
            raise ValueError(f"environment variable '{key}' is not set")
        return os.environ[key]

    return ENV_PATTERN.sub(replacement, raw)
