from __future__ import annotations

from saas_footprint_analyzer.config.schema import DatadogConfig


def build_auth_headers(config: DatadogConfig) -> dict[str, str]:
    return {
        "DD-API-KEY": config.api_key,
        "DD-APPLICATION-KEY": config.app_key,
        "Accept": "application/json",
        "User-Agent": "saas-footprint-analyzer/0.1.0",
    }
