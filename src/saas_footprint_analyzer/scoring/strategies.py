from __future__ import annotations

from statistics import mean

from saas_footprint_analyzer.config.schema import AppConfig


def compute_dimension_scores(
    normalized_metrics: dict[str, float | None], config: AppConfig
) -> dict[str, float | None]:
    score_by_dimension: dict[str, list[float]] = {
        "compute": [],
        "traffic": [],
        "data": [],
        "complexity": [],
    }
    for metric in config.metrics.collect:
        value = normalized_metrics.get(metric.name)
        if value is not None:
            score_by_dimension[metric.dimension].append(value)
    return {
        dimension: (round(mean(values), 2) if values else None)
        for dimension, values in score_by_dimension.items()
    }


def map_score_to_class(score: float, thresholds: dict[str, tuple[float, float]]) -> str:
    for label in ("small", "medium", "large", "xlarge"):
        lower, upper = thresholds[label]
        if lower <= score <= upper:
            return label
    if score < thresholds["small"][0]:
        return "small"
    return "xlarge"
