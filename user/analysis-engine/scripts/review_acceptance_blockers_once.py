#!/usr/bin/env python3
"""Read-only MarketSage acceptance review from existing local reports.

No network requests, downloads, normalization, adjustment, feature generation,
label generation, raw-data mutation, scoring enablement or backtest execution.
"""
from __future__ import annotations
import argparse
import csv
import datetime as dt
import json
from pathlib import Path
from typing import Any

DATA_DEFAULT = Path.home() / "marketsage-data"
REPO_DEFAULT = Path.home() / "projects" / "marketsage-acceptance"

ASSETS = [
    ("Iran equities / TSETMC",
     "1,220 raw archives and 1,220 normalized histories; 1,677,202 history rows; 128 research candidate series.",
     "INTERNAL_QA_PASS_ONLY",
     "Independently reconcile corporate actions/factors, explain date gaps, confirm units/identity and reuse rights."),
    ("Iran gold funds / ETFs",
     "Potentially included in TSETMC universe; no fund-specific acceptance proven by the finalization report.",
     "CANDIDATE_NOT_ACCEPTED",
     "Verify ISIN/type, history, unit, calendar, liquidity, fees and event/adjustment semantics."),
    ("Iran physical gold and coins",
     "Prior collection reported 30 TGJU gold rows and 30 coin rows; seller export audit reported 184 18K-gold rows.",
     "AUDITED_CANDIDATES_ONLY",
     "Reuse existing artifacts; verify quote unit, buy/sell vs indicative price, timestamp/cadence, independent cross-check and rights."),
    ("Iran free-market FX",
     "Prior multi-asset run had no FX rows; seller export audit reported 176 free-market USD rows.",
     "GAP_OR_CANDIDATE_ONLY",
     "Verify export provenance; distinguish buy/sell/mid, IRR/toman, quote time and weekend/holiday conventions."),
    ("Global gold/silver/oil, USD, rates/bonds/volatility",
     "Yahoo candidates included proxies such as GLD, TLT, UUP and USO; these are not the same as all spot/physical series.",
     "PROXY_CANDIDATES_ONLY",
     "Label proxy vs target; document exchange, currency, history, corporate actions, license and macro publication times."),
    ("Crypto",
     "Prior Yahoo candidates included BTC-USD, ETH-USD and SOL-USD; one Binance probe returned HTTP 451.",
     "CANDIDATE_NOT_ACCEPTED",
     "Verify lawful/permitted provider, UTC timestamps, market identity, gaps, fees, delistings and reuse terms."),
    ("Iran/global macro and bonds",
     "FRED/ALFRED credentials were previously missing; other sources remain feasibility candidates.",
     "NOT_ACCEPTED",
     "Record units, observation period, publication time, revisions/vintages, frequency, license and source-backed history."),
    ("News, events and Persian sentiment",
     "Prior collection summary reported 180 unique candidate news items; GDELT previously returned HTTP 429. Article count is not sentiment validation.",
     "CANDIDATE_ONLY",
     "Persist provenance; deduplicate; retain publication/first-seen times; create labelled Persian/English benchmark; evaluate sentiment/events with abstention and point-in-time joins."),
    ("Housing, vehicles and other Iran assets",
     "No accepted historical series established by the current reports.",
     "NOT_IN_ACCEPTED_COVERAGE",
     "Later scope: find lawful source, stable definitions/units, update frequency and timestamped history before comparing."),
]

BLOCKERS = [
    ("A1", "Corporate-action evidence and economic correctness", "BLOCKED",
     "Arithmetic QA cannot prove provider-supplied factors are economically correct. Select a bounded, representative sample of splits, capital increases, cash dividends and symbol changes. Reconcile against official disclosures or another independently documented source. Record event ID, effective date, raw prices, factor/formula, document URL, reviewer and discrepancy. Do not approve the source before this evidence and reuse rights are reviewed."),
    ("A2", "Missing dates, calendar, suspensions and listings", "OPEN",
     "Do not repair with nearest-date matching. Classify each gap as official non-trading day, market holiday, suspension, IPO/listing boundary, delisting, provider omission or unknown. Require official calendar/disclosure evidence for each resolved class."),
    ("A3", "Licensing, storage and commercial reuse", "OPEN",
     "Record source-specific written terms for historical collection, durable storage, commercial use, derived features, model training, caching and redistribution. Public endpoint/reachability is not a license. Unknown means not accepted."),
    ("A4", "Return semantics", "OPEN",
     "Document quote unit/currency, raw vs backward-adjusted close, dividends, volume adjustment and corporate-action convention. Distinguish price return from total return. Keep adjusted candidate returns research-only until reviewed."),
    ("A5", "Point-in-time tradability and backtest readiness", "BLOCKED_FOR_BACKTEST",
     "Retrospective adjusted history does not prove point-in-time tradability. Freeze decision/availability timestamps, universe membership, delistings, costs/slippage, monthly decision schedule and chronological holdout before any approved backtest."),
]

DEPLOYMENT = [
    ("D1", "Clean production-like start, deterministic migrations and health checks", "UNKNOWN — verify on target server"),
    ("D2", "External secrets, no secrets in Git/images/logs, least privilege", "UNKNOWN — verify server configuration"),
    ("D3", "TLS/domain/reverse proxy, firewall, backup and restore test, monitoring/log rotation", "UNKNOWN — verify infrastructure"),
    ("D4", "Authentication/authorization, rate limits, validation, safe errors and dependency/image scan", "UNKNOWN — verify release checklist"),
    ("D5", "UI labels research-only status, source timestamps, stale/missing data and non-advisory limits", "PARTIAL/UNKNOWN — verify current UI/API"),
    ("D6", "Scoring, investment ranking, adjusted-return approval and backtest stay fail-closed", "REQUIRED"),
    ("D7", "Deployed URL smoke test, rollback plan and post-deploy health check", "NOT VERIFIED"),
]

def read_json(p: Path) -> Any:
    try:
        return json.loads(p.read_text(encoding="utf-8-sig"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        return None

def find_files(root: Path, names: set[str]) -> list[Path]:
    if not root.is_dir():
        return []
    return sorted((p for p in root.rglob("*") if p.is_file() and p.name in names),
                  key=lambda p: (len(p.parts), str(p)))

def latest_run(data_root: Path) -> Path | None:
    base = data_root / "tsetmc-research"
    runs = [p for p in base.glob("finalize_*") if p.is_dir()] if base.exists() else []
    return max(runs, key=lambda p: p.stat().st_mtime) if runs else None

def summarize_csv(p: Path) -> dict[str, Any]:
    out: dict[str, Any] = {"path": str(p)}
    try:
        with p.open("r", encoding="utf-8-sig", newline="") as f:
            r = csv.DictReader(f)
            out["columns"] = r.fieldnames or []
            rows, series, dates, flags = 0, set(), set(), {}
            for row in r:
                rows += 1
                for k in ("isin", "ISIN", "symbol", "ticker"):
                    if row.get(k):
                        series.add(row[k]); break
                for k in ("date", "timestamp", "datetime", "observed_at"):
                    if row.get(k):
                        dates.add(row[k][:10]); break
                for k in ("research_only", "adjusted_returns_allowed", "scoring_allowed", "backtest_approved"):
                    if row.get(k) is not None:
                        key = k + "=" + row[k]
                        flags[key] = flags.get(key, 0) + 1
            out.update(rows=rows, distinct_series=len(series), distinct_dates=len(dates), safety_flags=flags)
    except (OSError, UnicodeDecodeError, csv.Error) as e:
        out["read_error"] = type(e).__name__
    return out

def collect_report_evidence(run: Path | None) -> dict[str, Any]:
    out: dict[str, Any] = {"run_root": str(run) if run else None, "reports": [], "candidate_csvs": []}
    if not run or not run.is_dir():
        out["error"] = "No existing finalize_* run found. Supply --run-root pointing at an existing run."
        return out
    summary = run / "finalization_summary.json"
    out["finalization_summary"] = read_json(summary) if summary.is_file() else None
    report_paths = find_files(run, {"pipeline_report.json", "validation_report.json", "research_acceptance_suite.json"})
    blockers, statuses = [], []
    for p in report_paths:
        data = read_json(p)
        out["reports"].append({"path": str(p), "parsed": data is not None})
        if not isinstance(data, dict):
            continue
        for key in ("blockers_not_resolvable_by_code_only", "blockers", "acceptance_blockers"):
            if isinstance(data.get(key), list):
                blockers.extend(str(x) for x in data[key])
        for key in ("qa_status", "status", "validation_status"):
            v = data.get(key)
            if isinstance(v, str) and ("PASS_INTERNAL_QA" in v or v == "PASSED"):
                statuses.append(v)
    out["explicit_blockers"] = list(dict.fromkeys(blockers))
    out["internal_qa_status"] = statuses[0] if statuses else "NOT_FOUND_IN_KNOWN_FIELDS"
    csv_paths = find_files(run, {"research_features_candidate_only.csv", "forward_labels_126obs_candidate_only.csv",
                                 "research_series_candidate_only.csv", "reprocessing_triage_summary.csv"})
    out["candidate_csvs"] = [summarize_csv(p) for p in csv_paths]
    return out

def inventory_existing_summaries(data_root: Path) -> dict[str, Any]:
    roots = [data_root / "multi-asset-collection", Path("/tmp/marketsage-multi-asset-collection")]
    files = []
    for root in roots:
        files.extend(find_files(root, {"summary.json", "collection_summary.json", "manifest.json",
                                       "multi_asset_collection_summary.json"}))
    files = list(dict.fromkeys(files))
    return {"summary_files_found": len(files),
            "files": [{"path": str(p), "parsed": read_json(p) is not None} for p in files[:50]],
            "note": "Only existing summary/manifest files are inspected; no market payload is downloaded or copied."}

def evidence_records(path: Path) -> list[dict[str, Any]]:
    """Read existing report artifacts only; never inspect raw history archives."""
    try:
        if path.suffix.lower() == ".csv":
            with path.open("r", encoding="utf-8-sig", newline="") as f:
                return [dict(x) for x in csv.DictReader(f)]
        if path.suffix.lower() == ".jsonl":
            rows = []
            for line in path.read_text(encoding="utf-8-sig").splitlines():
                try:
                    value = json.loads(line)
                    if isinstance(value, dict):
                        rows.append(value)
                except json.JSONDecodeError:
                    continue
            return rows
        if path.suffix.lower() == ".json":
            value = read_json(path)
            if isinstance(value, list):
                return [x if isinstance(x, dict) else {"value": x} for x in value]
            if isinstance(value, dict):
                rows = []
                for key, val in value.items():
                    if isinstance(val, list):
                        rows.extend(x if isinstance(x, dict) else {"section": key, "value": x} for x in val)
                return rows or [value]
    except (OSError, UnicodeDecodeError, csv.Error):
        return []
    return []

def write_evidence_ledgers(run_root: Path | None, output: Path) -> dict[str, Any]:
    """Turn relevant existing report rows into human-review queues; never assert correctness."""
    event_rows, gap_rows, scanned = [], [], []
    if run_root and run_root.is_dir():
        for path in run_root.rglob("*"):
            if not path.is_file() or path.suffix.lower() not in {".csv", ".json", ".jsonl"}:
                continue
            name = path.name.lower()
            if not any(word in name for word in ("event", "adjust", "corporate", "triage", "gap", "missing", "calendar", "reconcil", "coverage")):
                continue
            scanned.append(str(path))
            rows = evidence_records(path)
            for index, row in enumerate(rows, start=1):
                blob = (name + " " + json.dumps(row, ensure_ascii=False, default=str)).lower()
                base = {
                    "evidence_file": str(path),
                    "source_row": index,
                    "review_status": "NEEDS_INDEPENDENT_SOURCE_REVIEW",
                    "record_json": json.dumps(row, ensure_ascii=False, sort_keys=True, default=str),
                }
                if any(word in blob for word in ("adjust", "corporate", "dividend", "split", "factor", "sharechange", "price_event", "capital increase", "تعدیل", "افزایش سرمایه", "سود نقدی")):
                    event_rows.append(base)
                if any(word in blob for word in ("missing", "gap", "calendar", "suspend", "coverage", "non-trading", "trading day", "date mismatch", "missing date", "تاریخ غایب", "تعلیق", "تقویم معاملاتی")):
                    gap_rows.append(base)
    headers = ["evidence_file", "source_row", "review_status", "record_json"]
    event_path, gap_path = output / "corporate_action_evidence_review.csv", output / "date_gap_evidence_review.csv"
    for path, rows in ((event_path, event_rows), (gap_path, gap_rows)):
        with path.open("w", encoding="utf-8-sig", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writeheader()
            writer.writerows(rows)
    return {
        "existing_report_files_scanned": len(scanned),
        "scanned_files": scanned,
        "corporate_action_rows_queued": len(event_rows),
        "corporate_action_ledger": str(event_path),
        "date_gap_rows_queued": len(gap_rows),
        "date_gap_ledger": str(gap_path),
        "interpretation": "These are candidate rows extracted from existing report artifacts only. They are review queues, not independently verified facts; empty ledgers mean no matching report rows were found, not that no events/gaps exist.",
    }

def make_report(args: argparse.Namespace) -> dict[str, Any]:
    data_root = args.data_root.expanduser()
    run = args.run_root.expanduser() if args.run_root else latest_run(data_root)
    tsetmc = collect_report_evidence(run)
    return {
        "generated_at_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "mode": "READ_ONLY_EXISTING_REPORTS_NO_NETWORK_NO_REPROCESSING",
        "repository_path": str(args.repo.expanduser()),
        "data_root": str(data_root),
        "tsetmc": tsetmc,
        "acceptance_blockers": [{"id": i, "gate": g, "status": s, "required_evidence": a} for i, g, s, a in BLOCKERS],
        "other_asset_families": [{"family": n, "known_evidence": e, "status": s, "next_gate": a} for n, e, s, a in ASSETS],
        "existing_multi_asset_summaries": inventory_existing_summaries(data_root),
        "deployment": {
            "decision": "SPLIT RELEASE: a clearly labelled research-only prototype may be deployed after D1-D5 and D7 are verified. Investment recommendations, source acceptance and backtests remain blocked by their separate evidence gates.",
            "estimate": "The data QA report cannot provide a defensible number of days to deployment. A research-only deployment is a separate, smaller gate; final investment decisioning cannot be dated until independent event, license and semantics reviews are complete.",
            "gates": [{"id": i, "requirement": r, "status": s} for i, r, s in DEPLOYMENT],
        },
        "next_actions_without_rerunning_data": [
            "Use the existing final QA report and reprocessing triage CSV; reconcile sampled event records to official source documents without regenerating candidates.",
            "Build an event reconciliation ledger from existing event inventory/reports, including factor, effective date, event type, official reference, reviewer and discrepancy.",
            "Build a date-gap exception ledger from existing raw-vs-normalized reconciliation; never assume a gap is a holiday without calendar evidence.",
            "Create per-source rights/semantics records; mark unknown as blocked.",
            "Reuse any existing persisted multi-asset summaries; if none exist, report that evidence is not durably available rather than silently recollecting.",
            "Only run this script again after the evidence or code changes. It does not run market-data processing.",
            "Human review must make the source acceptance decision; this script never approves a source or enables scoring.",
        ],
        "safety": {"network_requests": False, "market_data_downloads": False, "raw_inputs_modified": False,
                   "normalization_adjustment_features_labels_rerun": False, "scoring_enabled": False,
                   "backtest_approved": False},
    }

def render_md(r: dict[str, Any]) -> str:
    lines = [
        "# MarketSage acceptance blockers and release readiness",
        "",
        "- Generated UTC: " + r["generated_at_utc"],
        "- Mode: " + r["mode"],
        "- Existing TSETMC run: " + str(r["tsetmc"].get("run_root")),
        "- Internal QA status parsed: " + str(r["tsetmc"].get("internal_qa_status")),
        "",
        "Internal QA PASS is not independent economic validation, legal permission, source acceptance or backtest approval.",
        "",
        "## Existing report blockers",
        "",
    ]
    blockers = r["tsetmc"].get("explicit_blockers", [])
    lines.extend(["- " + x for x in blockers] if blockers else ["- No blocker list parsed from known report fields; see report file paths in JSON."])
    lines += ["", "## Existing candidate artifact counts", ""]
    for x in r["tsetmc"].get("candidate_csvs", []):
        lines.append("- " + x["path"] + ": rows=" + str(x.get("rows", "?")) +
                     ", series=" + str(x.get("distinct_series", "?")) +
                     ", distinct dates=" + str(x.get("distinct_dates", "?")))
        if x.get("safety_flags"):
            lines.append("  - safety flags: " + json.dumps(x["safety_flags"], ensure_ascii=False, sort_keys=True))
    ledger = r.get("existing_report_evidence_ledgers", {})
    lines += ["", "## Existing-report review queues", "",
              "These are rows extracted from existing reports, not verified acceptance evidence.",
              "- Corporate-action rows queued: " + str(ledger.get("corporate_action_rows_queued", 0)),
              "- Corporate-action ledger: " + str(ledger.get("corporate_action_ledger")),
              "- Date-gap rows queued: " + str(ledger.get("date_gap_rows_queued", 0)),
              "- Date-gap ledger: " + str(ledger.get("date_gap_ledger")),
              "- " + str(ledger.get("interpretation", "")), "",
              "## Acceptance gates", ""]
    for x in r["acceptance_blockers"]:
        lines += ["### " + x["id"] + " — " + x["gate"] + " [" + x["status"] + "]", "", x["required_evidence"], ""]
    lines += ["## Other assets", "", "| Family | Existing evidence | Status | Next gate |",
              "|---|---|---|---|"]
    for x in r["other_asset_families"]:
        lines.append("| " + x["family"] + " | " + x["known_evidence"] + " | " + x["status"] + " | " + x["next_gate"] + " |")
    lines += ["", "## Deployment", "", r["deployment"]["decision"], "", r["deployment"]["estimate"], "",
              "| Gate | Requirement | Status |", "|---|---|---|"]
    for x in r["deployment"]["gates"]:
        lines.append("| " + x["id"] + " | " + x["requirement"] + " | " + x["status"] + " |")
    lines += ["", "## Next actions without repeated data generation", ""]
    lines.extend(str(i) + ". " + x for i, x in enumerate(r["next_actions_without_rerunning_data"], 1))
    lines += ["", "## Safety", ""]
    lines.extend("- " + k + ": " + str(v).lower() for k, v in r["safety"].items())
    lines += ["", "This is an evidence tracker, not an acceptance decision.", ""]
    return "\n".join(lines)

def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--data-root", type=Path, default=DATA_DEFAULT)
    p.add_argument("--repo", type=Path, default=REPO_DEFAULT)
    p.add_argument("--run-root", type=Path, help="Existing finalize_* directory; default is latest by modification time.")
    p.add_argument("--output-dir", type=Path, help="Default: DATA_ROOT/acceptance-review/<UTC timestamp>")
    args = p.parse_args()
    report = make_report(args)
    stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    output = args.output_dir.expanduser() if args.output_dir else args.data_root.expanduser() / "acceptance-review" / stamp
    output.mkdir(parents=True, exist_ok=True)
    report["existing_report_evidence_ledgers"] = write_evidence_ledgers(
        Path(report["tsetmc"]["run_root"]) if report["tsetmc"].get("run_root") else None, output
    )
    jp, mp = output / "acceptance_blocker_review.json", output / "acceptance_blocker_review.md"
    jp.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    mp.write_text(render_md(report) + "\n", encoding="utf-8")
    print("MARKETSAGE ACCEPTANCE BLOCKER REVIEW")
    print("MODE:", report["mode"])
    print("TSETMC_RUN:", report["tsetmc"].get("run_root") or "NOT_FOUND")
    print("INTERNAL_QA:", report["tsetmc"].get("internal_qa_status"))
    print("REPORT_BLOCKERS_PARSED:", len(report["tsetmc"].get("explicit_blockers", [])))
    print("ASSET_FAMILIES_TRACKED:", len(report["other_asset_families"]))
    print("OUTPUT_JSON:", jp)
    print("OUTPUT_MARKDOWN:", mp)
    for k, v in report["safety"].items():
        print(k.upper() + ":", str(v).lower())
    return 2 if report["tsetmc"].get("error") else 0

if __name__ == "__main__":
    raise SystemExit(main())
