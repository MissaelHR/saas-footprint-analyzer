from __future__ import annotations

from collections import defaultdict

from saas_footprint_analyzer.config.schema import DiscoveryConfig
from saas_footprint_analyzer.datadog.catalog import parse_tag_list
from saas_footprint_analyzer.models.domain import EnvironmentCandidate


class EnvironmentDiscoveryService:
    def __init__(self, config: DiscoveryConfig) -> None:
        self.config = config

    def discover(self, host_records: list[dict[str, object]]) -> list[EnvironmentCandidate]:
        grouped: dict[tuple[str, ...], list[dict[str, str]]] = defaultdict(list)
        for record in host_records:
            tag_values = record.get("tags") or []
            if not isinstance(tag_values, list):
                continue
            tags = parse_tag_list([str(item) for item in tag_values])
            if not self._passes_required(tags):
                continue
            if not self._passes_filters(tags):
                continue
            if any(key not in tags for key in self.config.environment_keys):
                continue
            key_tuple = tuple(tags[key] for key in self.config.environment_keys)
            grouped[key_tuple].append(tags)

        environments: list[EnvironmentCandidate] = []
        for key_tuple in sorted(grouped):
            members = grouped[key_tuple]
            key_tags = {
                key: key_tuple[index] for index, key in enumerate(self.config.environment_keys)
            }
            query_tags, ambiguous_tags = self._build_query_tags(members)
            environment_key = "|".join(
                f"{key}={key_tags[key]}" for key in self.config.environment_keys
            )
            environments.append(
                EnvironmentCandidate(
                    environment_key=environment_key,
                    key_tags=key_tags,
                    query_tags=query_tags,
                    source_count=len(members),
                    ambiguous_tags=ambiguous_tags,
                )
            )
        return environments

    def _passes_required(self, tags: dict[str, str]) -> bool:
        return all(tags.get(key) for key in self.config.required_tags)

    def _passes_filters(self, tags: dict[str, str]) -> bool:
        include_match = all(
            tags.get(key) in accepted for key, accepted in self.config.include.items()
        )
        exclude_match = all(
            tags.get(key) not in rejected for key, rejected in self.config.exclude.items()
        )
        return include_match and exclude_match

    def _build_query_tags(
        self, members: list[dict[str, str]]
    ) -> tuple[dict[str, str], dict[str, list[str]]]:
        interesting_keys = set(self.config.environment_keys) | set(self.config.required_tags) | set(
            self.config.optional_tags
        )
        values_by_key: dict[str, set[str]] = defaultdict(set)
        for tags in members:
            for key in interesting_keys:
                if key in tags:
                    values_by_key[key].add(tags[key])
        query_tags: dict[str, str] = {}
        ambiguous_tags: dict[str, list[str]] = {}
        for key in sorted(values_by_key):
            values = values_by_key[key]
            if len(values) == 1:
                query_tags[key] = next(iter(values))
            else:
                ambiguous_tags[key] = sorted(values)
        return query_tags, ambiguous_tags
