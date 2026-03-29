from pathlib import Path

import pytest

from saas_footprint_analyzer.config.loader import ConfigError, load_config


def write_config(tmp_path: Path, content: str) -> Path:
    path = tmp_path / "config.yaml"
    path.write_text(content, encoding="utf-8")
    return path


def test_load_config_normalizes_weights(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("DD_API_KEY", "api")
    monkeypatch.setenv("DD_APP_KEY", "app")
    config_path = write_config(
        tmp_path,
        """
version: 1
datadog:
  site: datadoghq.com
  api_key: ${DD_API_KEY}
  app_key: ${DD_APP_KEY}
audit:
  lookback_days: 7
  timezone: UTC
discovery:
  environment_keys: [env]
  required_tags: [env]
metrics:
  collect:
    - name: cpu
      query: "avg:test.metric{env:$env}"
      source_type: timeseries
      dimension: compute
      aggregator: avg
classification:
  strategy: weighted_score
  weights:
    compute: 2
    traffic: 1
    data: 1
    complexity: 1
  thresholds:
    small: [0, 25]
    medium: [25, 50]
    large: [50, 75]
    xlarge: [75, 100]
output:
  formats: [json]
  directory: ./output
        """.strip(),
    )
    loaded = load_config(config_path)
    assert loaded.warnings
    weights, _ = loaded.config.normalized_weights()
    assert weights["compute"] == pytest.approx(0.4)


def test_load_config_rejects_bad_thresholds(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setenv("DD_API_KEY", "api")
    monkeypatch.setenv("DD_APP_KEY", "app")
    config_path = write_config(
        tmp_path,
        """
version: 1
datadog:
  site: datadoghq.com
  api_key: ${DD_API_KEY}
  app_key: ${DD_APP_KEY}
audit:
  lookback_days: 7
  timezone: UTC
discovery:
  environment_keys: [env]
metrics:
  collect:
    - name: cpu
      query: "avg:test.metric{env:$env}"
      source_type: timeseries
      dimension: compute
      aggregator: avg
classification:
  strategy: weighted_score
  weights:
    compute: 0.25
    traffic: 0.25
    data: 0.25
    complexity: 0.25
  thresholds:
    small: [0, 30]
    medium: [20, 50]
    large: [50, 75]
    xlarge: [75, 100]
output:
  formats: [json]
  directory: ./output
        """.strip(),
    )
    with pytest.raises(ConfigError, match="non-overlapping"):
        load_config(config_path)
