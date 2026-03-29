from __future__ import annotations

from saas_footprint_analyzer.config.schema import AppConfig


def build_reasons(
    raw_metrics: dict[str, float | None],
    normalized_metrics: dict[str, float | None],
    dimension_scores: dict[str, float | None],
    config: AppConfig,
    warnings: list[str],
) -> list[str]:
    reasons: list[str] = []
    weighted_dims = [
        (dimension, score)
        for dimension, score in dimension_scores.items()
        if score is not None and score > 0
    ]
    weighted_dims.sort(key=lambda item: item[1], reverse=True)
    for dimension, score in weighted_dims[:2]:
        reasons.append(f"{dimension} dimension contributed {score:.2f} points before weighting")

    ranked_metrics = [
        (name, normalized_metrics[name], raw_metrics.get(name))
        for name in normalized_metrics
        if normalized_metrics[name] is not None
    ]
    ranked_metrics.sort(key=lambda item: item[1], reverse=True)
    for name, normalized, raw in ranked_metrics[:3]:
        metric_config = next(metric for metric in config.metrics.collect if metric.name == name)
        reasons.append(
            f"{name} contributed heavily to the {metric_config.dimension} dimension "
            f"(raw={raw:.2f}, normalized={normalized:.2f})"
        )

    missing_required = [
        metric.name
        for metric in config.metrics.collect
        if metric.required and raw_metrics.get(metric.name) is None
    ]
    if missing_required:
        reasons.append(
            "required metric data was missing for "
            + ", ".join(sorted(missing_required))
            + "; the result is lower confidence"
        )
    if warnings:
        reasons.extend(warnings)
    if not reasons:
        reasons.append("classification was based on limited but complete neutral metric input")
    return reasons
