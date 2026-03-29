from __future__ import annotations

import csv
from pathlib import Path

from saas_footprint_analyzer.models.domain import AuditReport


def render_csv(report: AuditReport, output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    target = output_dir / "audit-results.csv"
    with target.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(
            [
                "environment_key",
                "final_class",
                "final_score",
                "compute_score",
                "traffic_score",
                "data_score",
                "complexity_score",
                "warnings",
            ]
        )
        for environment in report.environments:
            writer.writerow(
                [
                    environment.environment_key,
                    environment.final_class,
                    environment.final_score,
                    environment.dimension_scores.get("compute"),
                    environment.dimension_scores.get("traffic"),
                    environment.dimension_scores.get("data"),
                    environment.dimension_scores.get("complexity"),
                    "; ".join(environment.warnings),
                ]
            )
    return target
