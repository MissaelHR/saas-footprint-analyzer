from saas_footprint_analyzer.config.schema import AppConfig
from saas_footprint_analyzer.models.domain import EnvironmentCandidate
from saas_footprint_analyzer.scoring.classifier import WeightedScoreClassifier


def build_config() -> AppConfig:
    return AppConfig.model_validate(
        {
            "version": 1,
            "datadog": {
                "site": "datadoghq.com",
                "api_key": "api",
                "app_key": "app",
            },
            "audit": {"lookback_days": 30, "timezone": "UTC", "dry_run": False},
            "discovery": {"environment_keys": ["env"], "required_tags": ["env"]},
            "metrics": {
                "collect": [
                    {
                        "name": "cpu",
                        "query": "avg:test{env:$env}",
                        "source_type": "timeseries",
                        "dimension": "compute",
                        "aggregator": "avg",
                    },
                    {
                        "name": "rps",
                        "query": "avg:req{env:$env}",
                        "source_type": "timeseries",
                        "dimension": "traffic",
                        "aggregator": "avg",
                    },
                ]
            },
            "classification": {
                "strategy": "weighted_score",
                "weights": {"compute": 0.5, "traffic": 0.25, "data": 0.15, "complexity": 0.10},
                "thresholds": {
                    "small": [0, 25],
                    "medium": [25, 50],
                    "large": [50, 75],
                    "xlarge": [75, 100],
                },
            },
            "output": {"formats": ["json"], "directory": "./output", "include_reasons": True},
        }
    )


def test_weighted_classifier() -> None:
    classifier = WeightedScoreClassifier(build_config())
    environment = EnvironmentCandidate("env=prod", {"env": "prod"}, {"env": "prod"}, 1)
    result = classifier.classify(
        environment=environment,
        raw_metrics={"cpu": 80.0, "rps": 40.0},
        normalized_metrics={"cpu": 80.0, "rps": 40.0},
    )
    assert result.final_class == "medium"
    assert result.final_score == 50.0
    assert result.dimension_scores["compute"] == 80.0
