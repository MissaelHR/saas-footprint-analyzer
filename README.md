# saas-footprint-analyzer

`saas-footprint-analyzer` is a Datadog-only Python CLI that discovers logical environments from Datadog tags, queries metrics for each discovered environment, normalizes the results into comparable features, computes a weighted score, and classifies each environment into size tiers.

The project is intentionally CLI-first and provider-scoped. It does not integrate AWS, Kubernetes APIs, Prometheus, Grafana, or any other telemetry backends. Datadog is the single source of truth.

## Why this exists

Many teams need a repeatable way to answer a simple question: "How big is each logical environment we operate?" Datadog usually already has the telemetry and tags needed to estimate that, but the raw data is not directly packaged as an explainable sizing model. This tool closes that gap.

## Scope

Current scope:

- Discover logical environments from Datadog tags
- Query Datadog metrics for each environment
- Normalize metrics relative to the current audit run
- Score environments with a weighted, explainable classifier
- Export JSON, CSV, and Markdown reports

Non-goals for v1:

- No AWS API integration
- No Kubernetes API integration
- No web UI
- No multi-provider abstraction layer
- No secrets stored in YAML

## Installation

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
```

## Environment variables

The YAML configuration supports `${ENV_VAR}` interpolation. Store credentials in the environment, not in the config file.

Example:

```bash
export DD_API_KEY=...
export DD_APP_KEY=...
```

`.env.example` is included as a template.

## Configuration

A complete example config is available at [`examples/config.example.yaml`](examples/config.example.yaml).

High-level structure:

```yaml
version: 1
datadog:
  site: datadoghq.com
  api_key: ${DD_API_KEY}
  app_key: ${DD_APP_KEY}
  timeout_seconds: 30
  max_retries: 3
audit:
  lookback_days: 30
  timezone: UTC
  dry_run: false
discovery:
  environment_keys: [env, cluster_name, namespace]
  required_tags: [env, service]
  optional_tags: [team, region]
  include:
    env: [prod, staging]
  exclude:
    namespace: [kube-system, datadog, istio-system]
metrics:
  collect:
    - name: cpu_usage_p95
      query: "p95:kubernetes.cpu.usage.total{env:$env,cluster_name:$cluster_name,namespace:$namespace}"
      source_type: timeseries
      dimension: compute
      aggregator: p95
classification:
  strategy: weighted_score
  weights:
    compute: 0.35
    traffic: 0.25
    data: 0.20
    complexity: 0.20
  thresholds:
    small: [0, 25]
    medium: [25, 50]
    large: [50, 75]
    xlarge: [75, 100]
output:
  formats: [json, csv, markdown]
  directory: ./output
  include_reasons: true
```

## Commands

Validate config and connectivity:

```bash
saas-footprint-analyzer validate-config --config examples/config.example.yaml
```

Discover logical environments:

```bash
saas-footprint-analyzer discover --config examples/config.example.yaml
```

Run a full audit:

```bash
saas-footprint-analyzer audit --config examples/config.example.yaml
```

Explain one environment:

```bash
saas-footprint-analyzer explain --config examples/config.example.yaml --environment "env=prod|cluster_name=core|namespace=payments"
```

Re-render an existing audit:

```bash
saas-footprint-analyzer export --config examples/config.example.yaml --format markdown
```

Diagnostics:

```bash
saas-footprint-analyzer doctor --config examples/config.example.yaml
saas-footprint-analyzer version
```

## How discovery works

Discovery is deterministic and configuration-driven:

1. Datadog host tags are fetched through the Datadog API.
2. Tags are converted into key/value maps.
3. Records missing configured required tags are excluded.
4. Include and exclude filters are applied.
5. Records are grouped by the configured `environment_keys`.
6. Each group becomes a logical environment key such as `env=prod|cluster_name=core|namespace=payments`.

Important limitation:

- Datadog does not expose a universal "environment" object. v1 discovery relies on Datadog host tags as the tag inventory source. If your logical environment model depends on tags that are not consistently attached to hosts, discovery will be incomplete.

## How scoring works

The default v1 strategy is `weighted_score`.

1. Each configured metric is queried from Datadog for every discovered environment.
2. Aggregated raw values are computed from returned timeseries points.
3. Raw values are normalized to a `0-100` scale using min-max scaling across the environments in the current audit run.
4. Normalized metrics are averaged by dimension: `compute`, `traffic`, `data`, `complexity`.
5. Configured dimension weights are applied.
6. The final score is mapped to `small`, `medium`, `large`, or `xlarge`.

If all environments have the same raw value for a metric, normalization assigns a neutral score of `50.0` for that metric instead of inventing separation.

## Explainability

Each result includes:

- Final class
- Final score
- Dimension scores
- Raw metrics
- Normalized metrics
- Human-readable reasons derived from the actual scoring path
- Explicit notes when data is missing or ambiguous

## Output

Audit outputs are written into the configured output directory:

- `audit-results.json`
- `audit-results.csv`
- `audit-results.md`

JSON is the canonical machine-readable artifact. `export` re-renders CSV or Markdown from the JSON report.

## Development

```bash
make install
make lint
make test
```

## Limitations

- Discovery is based on Datadog host tag inventory in v1.
- Metric queries that depend on ambiguous tag values within one logical environment may return missing data rather than guessing.
- Missing dimension data is handled explicitly but still reduces confidence in the final score.

## Roadmap

- Additional Datadog tag inventory strategies where permissions and APIs allow
- More normalization strategies
- User-selectable scoring strategies
- Historical comparison between audit runs
