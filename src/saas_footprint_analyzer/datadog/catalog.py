from __future__ import annotations


def parse_tag_list(tag_values: list[str]) -> dict[str, str]:
    parsed: dict[str, str] = {}
    for tag in tag_values:
        if ":" not in tag:
            continue
        key, value = tag.split(":", 1)
        if key and value:
            parsed[key] = value
    return parsed
