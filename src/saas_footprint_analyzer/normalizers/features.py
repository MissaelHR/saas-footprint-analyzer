from __future__ import annotations


class MinMaxFeatureNormalizer:
    def normalize(
        self, raw_by_environment: dict[str, dict[str, float | None]]
    ) -> dict[str, dict[str, float | None]]:
        metric_names = sorted(
            {metric for metrics in raw_by_environment.values() for metric in metrics}
        )
        result = {environment: {} for environment in raw_by_environment}
        for metric_name in metric_names:
            values = [
                metrics.get(metric_name)
                for metrics in raw_by_environment.values()
                if metrics.get(metric_name) is not None
            ]
            if not values:
                for environment in result:
                    result[environment][metric_name] = None
                continue
            minimum = min(values)
            maximum = max(values)
            for environment, metrics in raw_by_environment.items():
                value = metrics.get(metric_name)
                if value is None:
                    result[environment][metric_name] = None
                elif minimum == maximum:
                    result[environment][metric_name] = 50.0
                else:
                    score = ((value - minimum) / (maximum - minimum)) * 100
                    result[environment][metric_name] = round(score, 2)
        return result
