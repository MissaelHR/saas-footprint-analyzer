from __future__ import annotations

import math
import re
from statistics import mean

QUERY_VARIABLE_PATTERN = re.compile(r"\$([a-zA-Z_][a-zA-Z0-9_]*)")


def required_query_tags(query: str) -> set[str]:
    return set(QUERY_VARIABLE_PATTERN.findall(query))


def render_metric_query(query: str, tags: dict[str, str]) -> str:
    missing = [name for name in sorted(required_query_tags(query)) if name not in tags]
    if missing:
        raise ValueError(f"missing query tags for metric rendering: {', '.join(missing)}")
    rendered = query
    for key, value in tags.items():
        rendered = rendered.replace(f"${key}", value)
    return rendered


def aggregate_points(points: list[tuple[float, float]], aggregator: str) -> float | None:
    values = [value for _, value in points if value is not None and not math.isnan(value)]
    if not values:
        return None
    if aggregator == "avg":
        return float(mean(values))
    if aggregator == "min":
        return float(min(values))
    if aggregator == "max":
        return float(max(values))
    if aggregator == "p95":
        ordered = sorted(values)
        index = max(0, min(len(ordered) - 1, math.ceil(len(ordered) * 0.95) - 1))
        return float(ordered[index])
    raise ValueError(f"unsupported aggregator: {aggregator}")
