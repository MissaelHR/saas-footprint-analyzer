from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class EnvironmentCandidate:
    environment_key: str
    key_tags: dict[str, str]
    query_tags: dict[str, str]
    source_count: int
    ambiguous_tags: dict[str, list[str]] = field(default_factory=dict)
    excluded_reasons: list[str] = field(default_factory=list)


@dataclass
class EnvironmentResult:
    environment_key: str
    environment_tags: dict[str, str]
    final_class: str
    final_score: float
    dimension_scores: dict[str, float | None]
    raw_metrics: dict[str, float | None]
    normalized_metrics: dict[str, float | None]
    reasons: list[str]
    warnings: list[str] = field(default_factory=list)


@dataclass
class AuditMetadata:
    generated_at: str
    lookback_days: int
    timezone: str
    datadog_site: str
    dry_run: bool
    discovered_environments: int
    config_path: str
    warnings: list[str] = field(default_factory=list)


@dataclass
class AuditReport:
    metadata: AuditMetadata
    environments: list[EnvironmentResult]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> AuditReport:
        metadata = AuditMetadata(**payload["metadata"])
        environments = [EnvironmentResult(**item) for item in payload["environments"]]
        return cls(metadata=metadata, environments=environments)


def utc_timestamp() -> str:
    return datetime.utcnow().replace(microsecond=0).isoformat() + "Z"
