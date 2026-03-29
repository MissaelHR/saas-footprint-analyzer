import pytest

from saas_footprint_analyzer.config.secrets import resolve_env_placeholders


def test_resolve_env_placeholders(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DD_API_KEY", "secret")
    payload = {"datadog": {"api_key": "${DD_API_KEY}"}}
    assert resolve_env_placeholders(payload)["datadog"]["api_key"] == "secret"


def test_resolve_env_placeholders_missing_variable(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("DD_API_KEY", raising=False)
    with pytest.raises(ValueError, match="DD_API_KEY"):
        resolve_env_placeholders("${DD_API_KEY}")
