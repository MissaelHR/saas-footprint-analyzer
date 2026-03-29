from __future__ import annotations

from pathlib import Path

from saas_footprint_analyzer.models.domain import AuditReport


def render_markdown(report: AuditReport, output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    target = output_dir / "audit-results.md"
    lines = [
        "# saas-footprint-analyzer audit report",
        "",
        "## Audit metadata",
        "",
        f"- Generated at: `{report.metadata.generated_at}`",
        f"- Datadog site: `{report.metadata.datadog_site}`",
        f"- Lookback days: `{report.metadata.lookback_days}`",
        f"- Timezone: `{report.metadata.timezone}`",
        f"- Discovered environments: `{report.metadata.discovered_environments}`",
        "",
        "## Environment summary",
        "",
        "| Environment | Class | Score | Compute | Traffic | Data | Complexity |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for environment in sorted(report.environments, key=lambda item: item.final_score, reverse=True):
        lines.append(
            f"| `{environment.environment_key}` | `{environment.final_class}` | "
            f"{environment.final_score:.2f} "
            f"| {fmt(environment.dimension_scores.get('compute'))} "
            f"| {fmt(environment.dimension_scores.get('traffic'))} "
            f"| {fmt(environment.dimension_scores.get('data'))} "
            f"| {fmt(environment.dimension_scores.get('complexity'))} |"
        )
    lines.extend(["", "## Top environments by score", ""])
    top_environments = sorted(
        report.environments,
        key=lambda item: item.final_score,
        reverse=True,
    )[:5]
    for environment in top_environments:
        lines.extend(
            [
                f"### `{environment.environment_key}`",
                "",
                f"- Final class: `{environment.final_class}`",
                f"- Final score: `{environment.final_score:.2f}`",
                f"- Reasons: {'; '.join(environment.reasons)}",
                "",
            ]
        )
    target.write_text("\n".join(lines), encoding="utf-8")
    return target


def fmt(value: float | None) -> str:
    return "-" if value is None else f"{value:.2f}"
