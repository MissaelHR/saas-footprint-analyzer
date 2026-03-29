from __future__ import annotations

import json
from pathlib import Path

from saas_footprint_analyzer.models.domain import AuditReport


def write_json_report(report: AuditReport, output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    target = output_dir / "audit-results.json"
    target.write_text(json.dumps(report.to_dict(), indent=2), encoding="utf-8")
    return target


def read_report(output_dir: Path) -> AuditReport:
    target = output_dir / "audit-results.json"
    if not target.exists():
        raise FileNotFoundError(f"report file not found: {target}")
    payload = json.loads(target.read_text(encoding="utf-8"))
    return AuditReport.from_dict(payload)
