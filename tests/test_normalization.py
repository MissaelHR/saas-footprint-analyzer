from saas_footprint_analyzer.normalizers.features import MinMaxFeatureNormalizer


def test_min_max_normalization() -> None:
    normalizer = MinMaxFeatureNormalizer()
    result = normalizer.normalize(
        {
            "env-a": {"cpu": 10.0},
            "env-b": {"cpu": 20.0},
            "env-c": {"cpu": 15.0},
        }
    )
    assert result["env-a"]["cpu"] == 0.0
    assert result["env-b"]["cpu"] == 100.0
    assert result["env-c"]["cpu"] == 50.0


def test_min_max_normalization_handles_degenerate_case() -> None:
    normalizer = MinMaxFeatureNormalizer()
    result = normalizer.normalize({"env-a": {"cpu": 5.0}, "env-b": {"cpu": 5.0}})
    assert result["env-a"]["cpu"] == 50.0
    assert result["env-b"]["cpu"] == 50.0
