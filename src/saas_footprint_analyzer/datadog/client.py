from __future__ import annotations

import datetime as dt
from collections.abc import Iterator
from typing import Any

import httpx
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from saas_footprint_analyzer.config.schema import DatadogConfig, MetricDefinition
from saas_footprint_analyzer.datadog.auth import build_auth_headers
from saas_footprint_analyzer.datadog.errors import (
    DatadogAuthError,
    DatadogRateLimitError,
    DatadogRequestError,
)
from saas_footprint_analyzer.datadog.metrics import aggregate_points


class DatadogClient:
    def __init__(self, config: DatadogConfig) -> None:
        self.config = config
        self.base_url = f"https://api.{config.site}"
        self._client = httpx.Client(
            base_url=self.base_url,
            headers=build_auth_headers(config),
            timeout=config.timeout_seconds,
        )

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> DatadogClient:
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    @retry(
        retry=retry_if_exception_type(
            (httpx.TimeoutException, httpx.NetworkError, DatadogRateLimitError)
        ),
        wait=wait_exponential(multiplier=1, min=1, max=8),
        stop=stop_after_attempt(3),
        reraise=True,
    )
    def _request(self, method: str, path: str, **kwargs: Any) -> dict[str, Any]:
        try:
            response = self._client.request(method, path, **kwargs)
        except httpx.TimeoutException as exc:
            raise DatadogRequestError(f"Datadog request timed out for {path}") from exc
        except httpx.HTTPError as exc:
            raise DatadogRequestError(f"Datadog request failed for {path}: {exc}") from exc
        if response.status_code in {401, 403}:
            raise DatadogAuthError(self._format_error(response, path))
        if response.status_code == 429:
            raise DatadogRateLimitError(self._format_error(response, path))
        if response.status_code >= 400:
            raise DatadogRequestError(self._format_error(response, path))
        return response.json()

    @staticmethod
    def _format_error(response: httpx.Response, path: str) -> str:
        try:
            payload = response.json()
        except ValueError:
            payload = response.text
        return f"Datadog API error for {path}: status={response.status_code}, body={payload}"

    def validate_credentials(self) -> None:
        self._request("GET", "/api/v1/validate")
        self._request("GET", "/api/v1/tags/hosts", params={"count": 1})

    def iter_host_tag_records(self) -> Iterator[dict[str, Any]]:
        payload = self._request("GET", "/api/v1/tags/hosts")
        for record in payload.get("tags", []):
            if isinstance(record, dict):
                yield record

    def query_metric(
        self,
        metric: MetricDefinition,
        rendered_query: str,
        lookback_days: int,
    ) -> float | None:
        utc = getattr(dt, "UTC", dt.timezone.utc)
        now = dt.datetime.now(utc)
        start = now - dt.timedelta(days=lookback_days)
        payload = self._request(
            "GET",
            "/api/v1/query",
            params={
                "from": int(start.timestamp()),
                "to": int(now.timestamp()),
                "query": rendered_query,
            },
        )
        points: list[tuple[float, float]] = []
        for series in payload.get("series", []):
            for point in series.get("pointlist", []):
                if isinstance(point, (list, tuple)) and len(point) == 2 and point[1] is not None:
                    points.append((float(point[0]), float(point[1])))
        return aggregate_points(points, metric.aggregator)
