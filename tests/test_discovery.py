from saas_footprint_analyzer.config.schema import DiscoveryConfig
from saas_footprint_analyzer.datadog.metrics import render_metric_query
from saas_footprint_analyzer.discovery.environments import EnvironmentDiscoveryService


def test_discovery_groups_and_filters_environments() -> None:
    service = EnvironmentDiscoveryService(
        DiscoveryConfig.model_validate(
            {
                "environment_keys": ["env", "namespace"],
                "required_tags": ["env", "service"],
                "optional_tags": ["team"],
                "include": {"env": ["prod"]},
                "exclude": {"namespace": ["kube-system"]},
            }
        )
    )
    environments = service.discover(
        [
            {"tags": ["env:prod", "namespace:payments", "service:api", "team:core"]},
            {"tags": ["env:prod", "namespace:payments", "service:api", "team:core"]},
            {"tags": ["env:prod", "namespace:kube-system", "service:agent"]},
            {"tags": ["env:dev", "namespace:payments", "service:api"]},
        ]
    )
    assert len(environments) == 1
    assert environments[0].environment_key == "env=prod|namespace=payments"
    assert environments[0].source_count == 2


def test_discovery_marks_ambiguous_tags() -> None:
    service = EnvironmentDiscoveryService(
        DiscoveryConfig.model_validate(
            {
                "environment_keys": ["env"],
                "required_tags": ["env", "service"],
                "optional_tags": ["team"],
            }
        )
    )
    environments = service.discover(
        [
            {"tags": ["env:prod", "service:api", "team:core"]},
            {"tags": ["env:prod", "service:web", "team:core"]},
        ]
    )
    assert environments[0].ambiguous_tags["service"] == ["api", "web"]


def test_render_metric_query_requires_all_tags() -> None:
    rendered = render_metric_query(
        "avg:test{env:$env,service:$service}",
        {"env": "prod", "service": "api"},
    )
    assert rendered == "avg:test{env:prod,service:api}"
