#!/usr/bin/env python3
"""Create pending human-review evidence templates for registered sources.

Templates are never acceptance decisions. Empty/pending fields deliberately fail
closed until a reviewer adds traceable evidence and the acceptance evaluator runs.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

ENGINE_DIR = Path(__file__).resolve().parents[1]
if str(ENGINE_DIR) not in sys.path:
    sys.path.insert(0, str(ENGINE_DIR))

from source_registry import SOURCES


def build_template(source_id: str) -> dict[str, Any]:
    source = next((item for item in SOURCES if item.source_id == source_id), None)
    if source is None:
        raise ValueError("source_id is not in the current source registry")
    return {
        "source_id": source.source_id,
        "template_only": True,
        "reviewer": "",
        "reviewed_at": None,
        "rights_review": "pending",
        "host_connectivity": "pending",
        "timestamp_quality": "pending",
        "historical_coverage": "pending",
        "unit_reconciliation": "pending",
        "checks": {
            name: {"status": "pending", "evidence": ""}
            for name in source.required_checks
        },
        "note": (
            "Fill with verifiable source references. A complete evidence file does not "
            "automatically change source_registry.py or enable production scoring."
        ),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--source-id", choices=[source.source_id for source in SOURCES])
    group.add_argument("--all", action="store_true", help="Create one pending template per registered source")
    parser.add_argument("--output", help="Output path for one source; required with --source-id")
    parser.add_argument("--output-dir", default="/tmp/marketsage-source-evidence-templates",
                        help="Directory for --all output")
    args = parser.parse_args(argv)

    if args.source_id and not args.output:
        parser.error("--output is required with --source-id")
    if args.source_id:
        target = Path(args.output).expanduser()
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(build_template(args.source_id), ensure_ascii=False, indent=2) + "\n",
                          encoding="utf-8")
        print(json.dumps({"created": 1, "path": str(target), "status": "pending_template_only"}, indent=2))
        return 0

    out_dir = Path(args.output_dir).expanduser()
    out_dir.mkdir(parents=True, exist_ok=True)
    created = []
    for source in SOURCES:
        safe_id = re.sub(r"[^A-Za-z0-9_.-]+", "_", source.source_id)
        target = out_dir / f"{safe_id}.evidence.template.json"
        target.write_text(json.dumps(build_template(source.source_id), ensure_ascii=False, indent=2) + "\n",
                          encoding="utf-8")
        created.append(str(target))
    print(json.dumps({"created": len(created), "output_dir": str(out_dir),
                      "status": "pending_template_only", "paths": created}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
