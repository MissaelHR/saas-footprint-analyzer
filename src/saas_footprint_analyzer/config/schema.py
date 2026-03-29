from __future__ import annotations

import math
import re
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

ALLOWED_DIMENSIONS = {"compute", "traffic", "data", "complexity"}
ALLOWED_OUTPUT_FORMATS = {"json", "csv", "markdown"}
ALLOWED_AGGREGATORS = {"avg", "min", "max", "p95"}


class DatadogConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    site: str
    api_key: str
    app_key: str
    timeout_seconds: int = Field(default=30, ge=1, le=300)
    max_retries: int = Field(default=3, ge=0, le=10)

    @model_validator(mode="after")
    def validate_site(self) -> DatadogConfig:
        if not re.fullmatch(r"[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", self.site):
            raise ValueError("datadog.site must be a valid Datadog domain such as datadoghq.com")
        return self


class AuditConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    lookback_days: int = Field(default=30, ge=1, le=365)
    timezone: str = "UTC"
    dry_run: bool = False


class DiscoveryConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    environment_keys: list[str]
    required_tags: list[str] = Field(default_factory=list)
    optional_tags: list[str] = Field(default_factory=list)
    include: dict[str, list[str]] = Field(default_factory=dict)
    exclude: dict[str, list[str]] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_discovery(self) -> DiscoveryConfig:
        if not self.environment_keys:
            raise ValueError("discovery.environment_keys must not be empty")
        for mapping_name in ("include", "exclude"):
            mapping = getattr(self, mapping_name)
            for key, values in mapping.items():
                invalid_values = (
                    not key
                    or not isinstance(values, list)
                    or not values
                    or any(not item for item in values)
                )
                if invalid_values:
                    raise ValueError(
                        f"discovery.{mapping_name} must map tag keys to non-empty string lists"
                    )
        return self


class MetricDefinition(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    query: str
    source_type: Literal["timeseries"]
    dimension: Literal["compute", "traffic", "data", "complexity"]
    aggregator: Literal["avg", "min", "max", "p95"]
    required: bool = False


class MetricsConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    collect: list[MetricDefinition]

    @model_validator(mode="after")
    def validate_metrics(self) -> MetricsConfig:
        if not self.collect:
            raise ValueError("metrics.collect must contain at least one metric definition")
        names = [metric.name for metric in self.collect]
        if len(set(names)) != len(names):
            raise ValueError("metrics.collect contains duplicate metric names")
        return self


class ClassificationConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    strategy: Literal["weighted_score"]
    weights: dict[Literal["compute", "traffic", "data", "complexity"], float]
    thresholds: dict[Literal["small", "medium", "large", "xlarge"], tuple[float, float]]

    @model_validator(mode="after")
    def validate_classification(self) -> ClassificationConfig:
        if set(self.weights) != ALLOWED_DIMENSIONS:
            raise ValueError(
                "classification.weights must contain compute, traffic, data, and complexity"
            )
        threshold_order = ["small", "medium", "large", "xlarge"]
        previous_upper: float | None = None
        for label in threshold_order:
            lower, upper = self.thresholds[label]
            if lower < 0 or upper > 100 or lower > upper:
                raise ValueError(
                    f"classification.thresholds.{label} must be within 0-100 and ordered"
                )
            if previous_upper is not None and lower < previous_upper:
                raise ValueError("classification.thresholds must be ordered and non-overlapping")
            previous_upper = upper
        return self


class OutputConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    formats: list[Literal["json", "csv", "markdown"]]
    directory: Path
    include_reasons: bool = True

    @model_validator(mode="after")
    def validate_output(self) -> OutputConfig:
        if not self.formats:
            raise ValueError("output.formats must contain at least one format")
        return self


class AppConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")

    version: Literal[1]
    datadog: DatadogConfig
    audit: AuditConfig
    discovery: DiscoveryConfig
    metrics: MetricsConfig
    classification: ClassificationConfig
    output: OutputConfig

    def normalized_weights(self) -> tuple[dict[str, float], str | None]:
        total = sum(self.classification.weights.values())
        if math.isclose(total, 1.0, rel_tol=1e-9, abs_tol=1e-9):
            return dict(self.classification.weights), None
        normalized = {
            dimension: weight / total
            for dimension, weight in self.classification.weights.items()
        }
        return normalized, f"classification.weights summed to {total:.4f}; normalized to 1.0"
