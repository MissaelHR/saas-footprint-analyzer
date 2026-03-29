from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import yaml
from pydantic import ValidationError

from saas_footprint_analyzer.config.schema import AppConfig
from saas_footprint_analyzer.config.secrets import resolve_env_placeholders


class ConfigError(Exception):
    """Raised when configuration loading or validation fails."""


@dataclass
class LoadedConfig:
    path: Path
    config: AppConfig
    warnings: list[str] = field(default_factory=list)


def load_config(path: str | Path) -> LoadedConfig:
    config_path = Path(path).expanduser().resolve()
    if not config_path.exists():
        raise ConfigError(f"config file does not exist: {config_path}")
    try:
        payload = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        raise ConfigError(f"invalid YAML in {config_path}: {exc}") from exc
    if not isinstance(payload, dict):
        raise ConfigError("config root must be a YAML mapping")
    try:
        resolved = resolve_env_placeholders(payload)
        config = AppConfig.model_validate(resolved)
    except ValueError as exc:
        raise ConfigError(str(exc)) from exc
    except ValidationError as exc:
        raise ConfigError(exc.errors(include_url=False).__str__()) from exc
    warnings: list[str] = []
    _, weight_warning = config.normalized_weights()
    if weight_warning:
        warnings.append(weight_warning)
    return LoadedConfig(path=config_path, config=config, warnings=warnings)
