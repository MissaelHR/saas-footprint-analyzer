from __future__ import annotations

from saas_footprint_analyzer.config.schema import AppConfig
from saas_footprint_analyzer.models.domain import EnvironmentCandidate, EnvironmentResult
from saas_footprint_analyzer.scoring.explain import build_reasons
from saas_footprint_analyzer.scoring.strategies import compute_dimension_scores, map_score_to_class


class WeightedScoreClassifier:
    def __init__(self, config: AppConfig) -> None:
        self.config = config
        self.weights, _ = config.normalized_weights()

    def classify(
        self,
        environment: EnvironmentCandidate,
        raw_metrics: dict[str, float | None],
        normalized_metrics: dict[str, float | None],
        warnings: list[str] | None = None,
    ) -> EnvironmentResult:
        warnings = list(warnings or [])
        dimension_scores = compute_dimension_scores(normalized_metrics, self.config)
        weighted_values = [
            (dimension_scores[dimension] or 0.0) * self.weights[dimension]
            for dimension in self.weights
        ]
        final_class = map_score_to_class(
            round(sum(weighted_values), 2),
            self.config.classification.thresholds,
        )
        final_score = round(
            sum(weighted_values),
            2,
        )
        reasons = build_reasons(
            raw_metrics,
            normalized_metrics,
            dimension_scores,
            self.config,
            warnings,
        )
        return EnvironmentResult(
            environment_key=environment.environment_key,
            environment_tags=environment.query_tags,
            final_class=final_class,
            final_score=final_score,
            dimension_scores=dimension_scores,
            raw_metrics=raw_metrics,
            normalized_metrics=normalized_metrics,
            reasons=reasons,
            warnings=warnings,
        )
