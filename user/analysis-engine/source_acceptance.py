"""Evidence checklist evaluator for MarketSage data-source onboarding.

This module reports whether documented acceptance evidence is complete. It never
changes the source registry and never grants production-scoring approval.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

from source_registry import SOURCES, source_scoring_gate


_ALLOWED_STATUSES = {"passed", "failed", "pending"}
_REQUIRED_TOP_LEVEL = ("reviewer", "reviewed_at", "rights_review", "host_connectivity",
                       "timestamp_quality", "historical_coverage", "unit_reconciliation")


def _aware_timestamp(value: Any) -> bool:
    if not isinstance(value, str) or not value.strip():
        return False
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return False
    return parsed.tzinfo is not None and parsed.utcoffset() is not None


def evaluate_acceptance(source_id: str, evidence: dict[str, Any]) -> dict[str, Any]:
    """Evaluate a human-maintained evidence document without promoting a source."""
    source = next((item for item in SOURCES if item.source_id == source_id), None)
    if source is None:
        return {
            "source_id": source_id,
            "evidence_complete": False,
            "missing_items": ["source_not_registered"],
            "failed_items": [],
            "production_scoring_gate": source_scoring_gate(source_id),
        }

    missing: list[str] = []
    failed: list[str] = []
    for field in _REQUIRED_TOP_LEVEL:
        value = evidence.get(field)
        if field == "reviewed_at":
            if not _aware_timestamp(value):
                missing.append("reviewed_at_timezone_aware")
        elif field == "reviewer":
            if not isinstance(value, str) or not value.strip():
                missing.append(field)
        elif value not in _ALLOWED_STATUSES:
            missing.append(f"{field}_status")
        elif value != "passed":
            failed.append(field)

    checks = evidence.get("checks")
    if not isinstance(checks, dict):
        missing.append("checks_object")
        checks = {}

    required = set(source.required_checks)
    supplied = set(checks)
    missing.extend(f"check:{name}" for name in sorted(required - supplied))
    missing.extend(f"unexpected_check:{name}" for name in sorted(supplied - required))
    for name in sorted(required & supplied):
        item = checks[name]
        if not isinstance(item, dict):
            missing.append(f"check:{name}_object")
            continue
        status = item.get("status")
        reference = item.get("evidence")
        if status not in _ALLOWED_STATUSES:
            missing.append(f"check:{name}_status")
        elif status != "passed":
            failed.append(f"check:{name}")
        if not isinstance(reference, str) or not reference.strip():
            missing.append(f"check:{name}_evidence_reference")

    gate = source_scoring_gate(source_id)
    return {
        "source_id": source_id,
        "evidence_complete": not missing and not failed,
        "missing_items": sorted(set(missing)),
        "failed_items": sorted(set(failed)),
        "production_scoring_gate": gate,
        "production_scoring_allowed": gate["eligible_for_production_scoring"],
        "note": (
            "Evidence completeness is not production approval. The independent registry "
            "gate remains authoritative and must be explicitly reviewed and updated."
        ),
    }


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if len(args) != 1:
        print("Usage: python source_acceptance.py EVIDENCE.json", file=sys.stderr)
        return 3
    try:
        evidence = json.loads(Path(args[0]).read_text(encoding="utf-8"))
        if not isinstance(evidence, dict) or not isinstance(evidence.get("source_id"), str):
            raise ValueError("evidence JSON must be an object with a string source_id")
        report = evaluate_acceptance(evidence["source_id"], evidence)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=False, indent=2))
        return 3
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    if report["missing_items"] or report["failed_items"]:
        return 2
    if not report["evidence_complete"] or not report["production_scoring_allowed"]:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
