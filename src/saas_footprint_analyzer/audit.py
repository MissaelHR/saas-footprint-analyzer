from __future__ import annotations

from pathlib import Path

from saas_footprint_analyzer.config.loader import LoadedConfig
from saas_footprint_analyzer.datadog.client import DatadogClient
from saas_footprint_analyzer.datadog.metrics import render_metric_query
from saas_footprint_analyzer.discovery.environments import EnvironmentDiscoveryService
from saas_footprint_analyzer.models.domain import AuditMetadata, AuditReport, EnvironmentCandidate
from saas_footprint_analyzer.normalizers.features import MinMaxFeatureNormalizer
from saas_footprint_analyzer.reporters.csv_reporter import render_csv
from saas_footprint_analyzer.reporters.json_reporter import write_json_report
from saas_footprint_analyzer.reporters.markdown_reporter import render_markdown
from saas_footprint_analyzer.scoring.classifier import WeightedScoreClassifier
from saas_footprint_analyzer.utils.time import utc_timestamp


def discover_environments(
    loaded_config: LoadedConfig, client: DatadogClient
) -> list[EnvironmentCandidate]:
    service = EnvironmentDiscoveryService(loaded_config.config.discovery)
    return service.discover(list(client.iter_host_tag_records()))


def run_audit(loaded_config: LoadedConfig, client: DatadogClient) -> AuditReport:
    config = loaded_config.config
    environments = discover_environments(loaded_config, client)
    raw_by_environment: dict[str, dict[str, float | None]] = {
        environment.environment_key: {} for environment in environments
    }
    warnings_by_environment: dict[str, list[str]] = {
        environment.environment_key: [] for environment in environments
    }
    for environment in environments:
        if environment.ambiguous_tags:
            warnings_by_environment[environment.environment_key].append(
                "ambiguous discovery tags: "
                + ", ".join(
                    f"{key}={','.join(values)}"
                    for key, values in sorted(environment.ambiguous_tags.items())
                )
            )
        for metric in config.metrics.collect:
            try:
                rendered = render_metric_query(metric.query, environment.query_tags)
            except ValueError as exc:
                raw_by_environment[environment.environment_key][metric.name] = None
                warnings_by_environment[environment.environment_key].append(str(exc))
                continue
            if config.audit.dry_run:
                raw_by_environment[environment.environment_key][metric.name] = None
                warnings_by_environment[environment.environment_key].append(
                    f"dry_run enabled; skipped Datadog query for {metric.name}"
                )
                continue
            raw_by_environment[environment.environment_key][metric.name] = client.query_metric(
                metric, rendered, config.audit.lookback_days
            )
    normalized = MinMaxFeatureNormalizer().normalize(raw_by_environment)
    classifier = WeightedScoreClassifier(config)
    results = [
        classifier.classify(
            environment=environment,
            raw_metrics=raw_by_environment[environment.environment_key],
            normalized_metrics=normalized[environment.environment_key],
            warnings=warnings_by_environment[environment.environment_key],
        )
        for environment in environments
    ]
    report = AuditReport(
        metadata=AuditMetadata(
            generated_at=utc_timestamp(),
            lookback_days=config.audit.lookback_days,
            timezone=config.audit.timezone,
            datadog_site=config.datadog.site,
            dry_run=config.audit.dry_run,
            discovered_environments=len(results),
            config_path=str(loaded_config.path),
            warnings=list(loaded_config.warnings),
        ),
        environments=sorted(results, key=lambda item: item.final_score, reverse=True),
    )
    return report


def write_outputs(report: AuditReport, output_dir: Path, formats: list[str]) -> dict[str, Path]:
    generated: dict[str, Path] = {}
    if "json" in formats:
        generated["json"] = write_json_report(report, output_dir)
    if "csv" in formats:
        generated["csv"] = render_csv(report, output_dir)
    if "markdown" in formats:
        generated["markdown"] = render_markdown(report, output_dir)
    return generated
