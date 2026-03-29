from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console
from rich.table import Table

from saas_footprint_analyzer import __version__
from saas_footprint_analyzer.audit import discover_environments, run_audit, write_outputs
from saas_footprint_analyzer.config.loader import ConfigError, LoadedConfig, load_config
from saas_footprint_analyzer.datadog.client import DatadogClient
from saas_footprint_analyzer.datadog.errors import DatadogError
from saas_footprint_analyzer.reporters.csv_reporter import render_csv
from saas_footprint_analyzer.reporters.json_reporter import read_report
from saas_footprint_analyzer.reporters.markdown_reporter import render_markdown
from saas_footprint_analyzer.utils.logging import configure_logging

app = typer.Typer(help="Audit and classify logical cloud environments using the Datadog API.")
console = Console()
ConfigOption = Annotated[Path, typer.Option(..., exists=True, dir_okay=False)]
EnvironmentOption = Annotated[str, typer.Option(..., "--environment")]
FormatOption = Annotated[str, typer.Option(..., "--format")]


def _load(path: Path) -> LoadedConfig:
    try:
        loaded = load_config(path)
    except ConfigError as exc:
        console.print(f"[red]Configuration error:[/red] {exc}")
        raise typer.Exit(code=1) from exc
    for warning in loaded.warnings:
        console.print(f"[yellow]Warning:[/yellow] {warning}")
    return loaded


def _client(loaded: LoadedConfig) -> DatadogClient:
    return DatadogClient(loaded.config.datadog)


@app.command("validate-config")
def validate_config(config: ConfigOption) -> None:
    """Validate configuration and Datadog connectivity."""
    configure_logging()
    loaded = _load(config)
    try:
        with _client(loaded) as client:
            client.validate_credentials()
    except DatadogError as exc:
        console.print(f"[red]Datadog validation failed:[/red] {exc}")
        raise typer.Exit(code=2) from exc
    console.print("[green]Configuration is valid and Datadog connectivity succeeded.[/green]")


@app.command()
def discover(config: ConfigOption) -> None:
    """Discover logical environments from Datadog tags."""
    loaded = _load(config)
    try:
        with _client(loaded) as client:
            environments = discover_environments(loaded, client)
    except DatadogError as exc:
        console.print(f"[red]Discovery failed:[/red] {exc}")
        raise typer.Exit(code=2) from exc
    table = Table(title="Discovered environments")
    table.add_column("Environment key")
    table.add_column("Query tags")
    table.add_column("Sources", justify="right")
    for environment in environments:
        table.add_row(
            environment.environment_key,
            ", ".join(f"{key}={value}" for key, value in sorted(environment.query_tags.items())),
            str(environment.source_count),
        )
    console.print(table)
    console.print(f"Discovered {len(environments)} environments.")


@app.command()
def audit(config: ConfigOption) -> None:
    """Run discovery, metric collection, normalization, scoring, and export."""
    loaded = _load(config)
    try:
        with _client(loaded) as client:
            report = run_audit(loaded, client)
    except DatadogError as exc:
        console.print(f"[red]Audit failed:[/red] {exc}")
        raise typer.Exit(code=2) from exc
    outputs = write_outputs(report, loaded.config.output.directory, loaded.config.output.formats)
    console.print(f"Audited {len(report.environments)} environments.")
    for format_name, path in outputs.items():
        console.print(f"- {format_name}: {path}")


@app.command()
def explain(
    config: ConfigOption,
    environment: EnvironmentOption,
) -> None:
    """Display the scoring details for one environment."""
    loaded = _load(config)
    output_dir = loaded.config.output.directory
    try:
        report = read_report(output_dir)
    except FileNotFoundError:
        try:
            with _client(loaded) as client:
                report = run_audit(loaded, client)
        except DatadogError as exc:
            console.print(f"[red]Explain failed:[/red] {exc}")
            raise typer.Exit(code=2) from exc
    match = next(
        (item for item in report.environments if item.environment_key == environment),
        None,
    )
    if not match:
        console.print(f"[red]Environment not found:[/red] {environment}")
        raise typer.Exit(code=1)
    console.print(f"[bold]Environment:[/bold] {match.environment_key}")
    console.print(f"[bold]Final class:[/bold] {match.final_class}")
    console.print(f"[bold]Final score:[/bold] {match.final_score:.2f}")
    console.print(f"[bold]Dimension scores:[/bold] {match.dimension_scores}")
    console.print(f"[bold]Raw metrics:[/bold] {match.raw_metrics}")
    console.print(f"[bold]Normalized metrics:[/bold] {match.normalized_metrics}")
    console.print("[bold]Reasons:[/bold]")
    for reason in match.reasons:
        console.print(f"- {reason}")


@app.command()
def export(
    config: ConfigOption,
    format: FormatOption,
) -> None:
    """Re-render a previously computed audit report."""
    loaded = _load(config)
    if format not in {"json", "csv", "markdown"}:
        console.print(f"[red]Unsupported format:[/red] {format}")
        raise typer.Exit(code=1)
    try:
        report = read_report(loaded.config.output.directory)
    except FileNotFoundError as exc:
        console.print(f"[red]Export failed:[/red] {exc}")
        raise typer.Exit(code=1) from exc
    if format == "json":
        path = loaded.config.output.directory / "audit-results.json"
    elif format == "csv":
        path = render_csv(report, loaded.config.output.directory)
    else:
        path = render_markdown(report, loaded.config.output.directory)
    console.print(f"Exported {format} report to {path}")


@app.command()
def doctor(config: ConfigOption) -> None:
    """Run richer validation and local diagnostics."""
    loaded = _load(config)
    output_dir = loaded.config.output.directory
    console.print(f"Config path: {loaded.path}")
    console.print(f"Output directory: {output_dir.resolve()}")
    try:
        with _client(loaded) as client:
            client.validate_credentials()
            environments = discover_environments(loaded, client)
    except DatadogError as exc:
        console.print(f"[red]Doctor failed:[/red] {exc}")
        raise typer.Exit(code=2) from exc
    console.print(
        f"Datadog validation OK. Discovery preview found {len(environments)} environments."
    )


@app.command()
def version() -> None:
    """Print the installed version."""
    console.print(__version__)


if __name__ == "__main__":
    app()
