import httpx
import pytest

from saas_footprint_analyzer.config.schema import DatadogConfig, MetricDefinition
from saas_footprint_analyzer.datadog.client import DatadogClient
from saas_footprint_analyzer.datadog.errors import DatadogAuthError, DatadogRequestError


def build_transport(handler):
    return httpx.MockTransport(handler)


def test_validate_credentials_auth_error() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(403, json={"errors": ["forbidden"]})

    client = DatadogClient(DatadogConfig(site="datadoghq.com", api_key="api", app_key="app"))
    client._client = httpx.Client(transport=build_transport(handler), base_url=client.base_url)
    with pytest.raises(DatadogAuthError):
        client.validate_credentials()


def test_query_metric_aggregates_points() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={"series": [{"pointlist": [[1, 2.0], [2, 4.0], [3, 6.0]]}]},
        )

    client = DatadogClient(DatadogConfig(site="datadoghq.com", api_key="api", app_key="app"))
    client._client = httpx.Client(transport=build_transport(handler), base_url=client.base_url)
    metric = MetricDefinition(
        name="cpu",
        query="avg:test{env:$env}",
        source_type="timeseries",
        dimension="compute",
        aggregator="avg",
    )
    assert client.query_metric(metric, "avg:test{env:prod}", 7) == 4.0


def test_query_metric_timeout_is_wrapped() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.TimeoutException("boom")

    client = DatadogClient(DatadogConfig(site="datadoghq.com", api_key="api", app_key="app"))
    client._client = httpx.Client(transport=build_transport(handler), base_url=client.base_url)
    metric = MetricDefinition(
        name="cpu",
        query="avg:test{env:$env}",
        source_type="timeseries",
        dimension="compute",
        aggregator="avg",
    )
    with pytest.raises(DatadogRequestError, match="timed out"):
        client.query_metric(metric, "avg:test{env:prod}", 7)
