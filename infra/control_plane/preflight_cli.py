"""CLI adapter that gates a workflow before any research/data entry point runs.

The adapter is side-effect-free. A locked scope exits non-zero before the
workflow can read datasets, inspect private outputs, or contact providers.
"""
from __future__ import annotations

import argparse
import os
import re
import sys
from pathlib import Path

from .safety_gate import SafetyGateError, preflight

DEFAULT_WORK_ID = "MS-20261116-CONTINUITY-001"
_WORK_ID = re.compile(r"^[A-Z0-9][A-Z0-9._-]{7,127}$")
_RUN_ID = re.compile(r"^[A-Za-z0-9._-]{1,80}$")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--action", required=True, choices=[
        "infrastructure", "governance", "synthetic_test",
        "research", "acquisition", "analysis", "backtest",
    ])
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--work-id", default=os.environ.get("MARKETSAGE_WORK_ID", DEFAULT_WORK_ID))
    parser.add_argument("--code-sha", default=os.environ.get("GITHUB_SHA", ""))
    parser.add_argument("--run-id", default=os.environ.get("GITHUB_RUN_ID", "manual"))
    args = parser.parse_args()

    if not _WORK_ID.fullmatch(args.work_id) or not _RUN_ID.fullmatch(args.run_id):
        print("MARKETSAGE_PREFLIGHT=BLOCKED reason=invalid_cli_identity", file=sys.stderr)
        return 2
    root = args.root.resolve()
    governance = root / "docs" / "governance"
    try:
        result = preflight(
            policy_path=governance / "execution_policy.json",
            work_item_path=governance / "work_items" / f"{args.work_id}.json",
            artifact_registry_path=governance / "ARTIFACT_REGISTRY.jsonl",
            run_ledger_path=governance / "RUN_LEDGER.jsonl",
            work_id=args.work_id,
            action=args.action,
            code_sha=args.code_sha,
            input_artifacts={},
            parameters={"entrypoint": "github_actions", "run_id": args.run_id},
            environment={"python": f"{sys.version_info.major}.{sys.version_info.minor}"},
            output_path=Path("/tmp") / f"marketsage-preflight-{args.run_id}",
        )
    except (SafetyGateError, OSError, ValueError) as exc:
        reason = str(exc).split(":", 1)[0].replace("\n", "")[:100]
        print(f"MARKETSAGE_PREFLIGHT=BLOCKED reason={reason}", file=sys.stderr)
        return 2

    print(f"MARKETSAGE_PREFLIGHT={result['preflight']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
