#!/usr/bin/env python3
"""One-pass, low-impact smoke audit of candidate MarketSage data sources.

Checks reachability and response shape only. It does NOT certify history depth,
correctness, commercial rights, or predictive value. Stores metadata only.
"""
from __future__ import annotations

import argparse
import concurrent.futures
import csv
import io
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from typing import Any

UA = "MarketSage-Data-Feasibility/0.1 (single-request-audit)"
TIMEOUT_DEFAULT = 8

# One small request per candidate. These are discovery probes, not production
# endpoints. Unofficial website/API access may violate terms.
SOURCES: list[dict[str, Any]] = [
    {"id":"iran_tsetmc_marketwatch","market":"iran_equities_funds_bonds","provider":"TSETMC CDN","url":"https://cdn.tsetmc.com/api/MarketData/GetMarketWatch","kind":"json","cost":"free_candidate","auth":"none","caveat":"Unofficial/public endpoint; verify history, adjusted prices, stability and permitted use."},
    {"id":"iran_tindex_currency","market":"iran_fx_gold_coin_crypto","provider":"Tindex public API","url_env":"TINDEX_API_BASE_URL","path":"/api/public/currency-rates","kind":"json","cost":"free_tier_or_paid_upgrade","auth":"TINDEX_API_TOKEN","caveat":"Requires user token. One request only. Verify quota, historical depth and API commercial terms."},
    {"id":"iran_tgju_site","market":"iran_fx_gold_coin","provider":"TGJU website","url":"https://www.tgju.org/","kind":"html","cost":"public_page_not_api","auth":"none","caveat":"Page reachability only; no assumption of API, history access or redistribution rights."},
    {"id":"iran_streamdata_site","market":"iran_equities_funds_fx_gold_commodities_global","provider":"StreamData","url":"https://streamdata.ir/","kind":"html","cost":"commercial_candidate","auth":"none","caveat":"Vendor advertises broad coverage; verify actual free tier, history, licensing and price."},
    {"id":"iran_free_fx_archive_candidate","market":"iran_fx_gold_coin_crypto","provider":"Nerkh/Jahankhahan public JSON candidate","url":"https://nerkh.jahankhahan.shop/data/live.json","kind":"json","cost":"free_unverified","auth":"none","caveat":"Unverified third-party candidate; check ownership, archive endpoint, units, provenance and terms."},
    {"id":"iran_cbi_site","market":"iran_macro_rates_fx","provider":"Central Bank of Iran","url":"https://www.cbi.ir/","kind":"html","cost":"public_site","auth":"none","caveat":"Site reachability only; extract and version official series with release dates."},
    {"id":"iran_amar_site","market":"iran_macro_inflation","provider":"Statistical Centre of Iran","url":"https://www.amar.org.ir/","kind":"html","cost":"public_site","auth":"none","caveat":"Site reachability only; inspect downloadable history and revisions."},
    {"id":"iran_open_data","market":"iran_macro_policy_context","provider":"Iran Open Data","url":"https://iranopendata.org/","kind":"html","cost":"public_candidate","auth":"none","caveat":"Check each dataset's provenance, license, frequency and revisions."},
    {"id":"global_crypto_binance_klines","market":"crypto","provider":"Binance public market data","url":"https://api.binance.com/api/v3/klines?symbol=BTCUSDT&interval=1d&limit=2","kind":"json","cost":"public_api","auth":"none","caveat":"Exchange-specific history; not Iran exchange pricing or fiat access."},
    {"id":"global_crypto_coingecko","market":"crypto","provider":"CoinGecko public API","url":"https://api.coingecko.com/api/v3/ping","kind":"json","cost":"free_limited_or_paid","auth":"none","caveat":"Ping checks API availability only; history endpoint and rate limits require a separate test."},
    {"id":"global_yahoo_gold","market":"gold_global","provider":"Yahoo Finance chart endpoint","url":"https://query1.finance.yahoo.com/v8/finance/chart/GC%3DF?range=5d&interval=1d","kind":"json","cost":"unofficial_free_candidate","auth":"none","caveat":"Unofficial endpoint; futures are not spot gold. Verify semantics, license and long history."},
    {"id":"global_yahoo_silver","market":"silver_global","provider":"Yahoo Finance chart endpoint","url":"https://query1.finance.yahoo.com/v8/finance/chart/SI%3DF?range=5d&interval=1d","kind":"json","cost":"unofficial_free_candidate","auth":"none","caveat":"Unofficial endpoint; futures are not spot silver."},
    {"id":"global_yahoo_oil","market":"oil_global","provider":"Yahoo Finance chart endpoint","url":"https://query1.finance.yahoo.com/v8/finance/chart/CL%3DF?range=5d&interval=1d","kind":"json","cost":"unofficial_free_candidate","auth":"none","caveat":"Continuous futures have roll/contract effects; not a spot series."},
    {"id":"global_yahoo_dxy","market":"usd_index","provider":"Yahoo Finance chart endpoint","url":"https://query1.finance.yahoo.com/v8/finance/chart/DX-Y.NYB?range=5d&interval=1d","kind":"json","cost":"unofficial_free_candidate","auth":"none","caveat":"Check ticker availability and history consistency."},
    {"id":"global_yahoo_vix","market":"global_risk_volatility","provider":"Yahoo Finance chart endpoint","url":"https://query1.finance.yahoo.com/v8/finance/chart/%5EVIX?range=5d&interval=1d","kind":"json","cost":"unofficial_free_candidate","auth":"none","caveat":"Index level is a risk proxy, not directly investable."},
    {"id":"global_yahoo_treasury_yield","market":"global_rates_bonds","provider":"Yahoo Finance chart endpoint","url":"https://query1.finance.yahoo.com/v8/finance/chart/%5ETNX?range=5d&interval=1d","kind":"json","cost":"unofficial_free_candidate","auth":"none","caveat":"Check quote scaling/definition; not a bond total-return series."},
    {"id":"global_worldbank_iran_cpi","market":"iran_macro_inflation","provider":"World Bank API","url":"https://api.worldbank.org/v2/country/IRN/indicator/FP.CPI.TOTL.ZG?format=json&per_page=3","kind":"json","cost":"free_api","auth":"none","caveat":"Usually annual frequency; unsuitable as a daily signal without release-date discipline."},
    {"id":"global_worldbank_iran_gdp","market":"iran_macro_growth","provider":"World Bank API","url":"https://api.worldbank.org/v2/country/IRN/indicator/NY.GDP.MKTP.KD.ZG?format=json&per_page=3","kind":"json","cost":"free_api","auth":"none","caveat":"Low-frequency and subject to revisions; record publication dates."},
    {"id":"global_fred_docs","market":"global_macro_rates_bonds","provider":"FRED/ALFRED","url":"https://fred.stlouisfed.org/docs/api/fred/","kind":"html","cost":"free_api_key_required_for_api","auth":"API key for observations API","caveat":"Docs are public; observations API generally needs a key. ALFRED vintages help reduce look-ahead bias."},
    {"id":"global_treasury_rates","market":"global_rates_bonds","provider":"US Treasury Fiscal Data API","url":"https://api.fiscaldata.treasury.gov/services/api/fiscal_service/v2/accounting/od/avg_interest_rates?page%5Bsize%5D=1&sort=-record_date","kind":"json","cost":"free_api","auth":"none","caveat":"US government debt series, not Iran bond yields."},
    {"id":"global_gdelt_news","market":"news_event_features","provider":"GDELT DOC API","url":"https://api.gdeltproject.org/api/v2/doc/doc?query=Iran%20economy&mode=ArtList&format=json&maxrecords=2","kind":"json","cost":"free_candidate","auth":"none","caveat":"News discovery only; deduplicate syndication and capture publication/first-seen time."},
    {"id":"iran_divar_housing_auto","market":"iran_housing_auto","provider":"Divar public site","url":"https://divar.ir/","kind":"html","cost":"public_page_not_api","auth":"none","caveat":"Not a structured historical price feed; listings are not transaction prices. No bulk scraping."},
    {"id":"iran_sheypoor_housing_auto","market":"iran_housing_auto","provider":"Sheypoor public site","url":"https://www.sheypoor.com/","kind":"html","cost":"public_page_not_api","auth":"none","caveat":"Not a structured historical price feed; listings are not transaction prices."},
]

def safe_url(spec: dict[str, Any]) -> tuple[str | None, str | None]:
    if "url" in spec:
        return spec["url"], None
    origin = os.environ.get(str(spec.get("url_env", "")), "").strip()
    token = os.environ.get("TINDEX_API_TOKEN", "").strip()
    if not origin and not token:
        return None, "not_configured"
    if not origin or not token:
        return None, "incomplete_credentials"
    parsed = urllib.parse.urlsplit(origin)
    if parsed.scheme != "https" or not parsed.netloc or parsed.path not in ("", "/") or parsed.query or parsed.fragment:
        return None, "invalid_origin_config"
    return origin.rstrip("/") + str(spec["path"]), None

def shape_info(body: bytes, content_type: str, kind: str) -> dict[str, Any]:
    text = body.decode("utf-8", errors="replace")
    info: dict[str, Any] = {"bytes": len(body), "content_type": content_type.split(";")[0][:80]}
    if kind == "json":
        try:
            value = json.loads(text)
        except Exception:
            info.update(shape_valid=False, shape="not_json")
            return info
        info["shape_valid"] = True
        if isinstance(value, dict):
            info.update(shape="object", top_level_keys=sorted(str(k) for k in value.keys())[:40])
            for key in ("data", "result", "results", "rates", "prices", "candles", "klines", "observations", "value"):
                if key in value and isinstance(value[key], list):
                    info["row_count"] = len(value[key])
                    break
            if "chart" in value and isinstance(value.get("chart"), dict):
                result = value["chart"].get("result")
                info["row_count"] = len(result) if isinstance(result, list) else 0
        elif isinstance(value, list):
            info.update(shape="array", row_count=len(value))
            if value and isinstance(value[0], list):
                info["first_row_width"] = len(value[0])
            elif value and isinstance(value[0], dict):
                info["first_row_keys"] = sorted(str(k) for k in value[0].keys())[:30]
        else:
            info["shape"] = type(value).__name__
        return info
    if kind == "csv":
        try:
            rows = list(csv.reader(io.StringIO(text)))
            info.update(shape_valid=len(rows) >= 2, shape="csv", row_count=max(0, len(rows)-1), header=rows[0][:20] if rows else [])
        except Exception:
            info.update(shape_valid=False, shape="not_csv")
        return info
    info.update(shape_valid=bool(text.strip()), shape="html_or_text", has_html=bool(re.search(r"<html|<!doctype", text[:1000], re.I)))
    return info

def probe(spec: dict[str, Any], timeout: int) -> dict[str, Any]:
    url, config_error = safe_url(spec)
    result = {k: spec.get(k) for k in ("id", "market", "provider", "cost", "auth", "caveat")}
    if config_error:
        result.update(status=config_error, reachable=False, shape_valid=False)
        return result
    assert url
    headers = {"User-Agent": UA, "Accept": "application/json,text/csv,text/html;q=0.8,*/*;q=0.5"}
    if spec.get("auth") == "TINDEX_API_TOKEN":
        headers["Authorization"] = "Bearer " + os.environ["TINDEX_API_TOKEN"].strip()
    request = urllib.request.Request(url, headers=headers, method="GET")
    started = time.monotonic()
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            body = response.read(1_000_001)
            elapsed = round((time.monotonic() - started) * 1000)
            info = shape_info(body[:1_000_000], response.headers.get("Content-Type", ""), spec["kind"])
            result.update(status="http_ok" if 200 <= response.status < 300 else "http_error",
                          http_status=response.status, reachable=200 <= response.status < 300,
                          elapsed_ms=elapsed, **info)
            if len(body) > 1_000_000:
                result["response_truncated"] = True
    except urllib.error.HTTPError as exc:
        result.update(status="http_error", http_status=exc.code, reachable=False,
                      elapsed_ms=round((time.monotonic()-started)*1000), shape_valid=False)
    except Exception as exc:
        result.update(status="network_error", reachable=False,
                      elapsed_ms=round((time.monotonic()-started)*1000),
                      error_type=type(exc).__name__)
    return result

def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default="/tmp/marketsage-data-feasibility.json")
    parser.add_argument("--timeout", type=int, default=TIMEOUT_DEFAULT)
    parser.add_argument("--workers", type=int, default=3, help="Keep low to avoid stressing public sources.")
    parser.add_argument("--self-test", action="store_true", help="Run offline shape checks only.")
    args = parser.parse_args()
    if args.self_test:
        checks = [
            (b'{"data":[1,2]}', "application/json", "json", True),
            (b"<html>ok</html>", "text/html", "html", True),
            (b"not json", "text/plain", "json", False),
        ]
        for body, ctype, kind, expected in checks:
            actual = shape_info(body, ctype, kind).get("shape_valid")
            if actual != expected:
                print(f"FAIL shape check: {kind} expected {expected}, got {actual}", file=sys.stderr)
                return 1
        print("self_test=PASS (3 offline shape checks)")
        return 0
    results: list[dict[str, Any]] = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=max(1, min(args.workers, 4))) as pool:
        futures = {pool.submit(probe, dict(s), args.timeout): s["id"] for s in SOURCES}
        for future in concurrent.futures.as_completed(futures):
            try:
                results.append(future.result())
            except Exception as exc:
                results.append({"id": futures[future], "status": "probe_error", "error_type": type(exc).__name__, "reachable": False})
    results.sort(key=lambda x: x["id"])
    report = {
        "schema_version": 1,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "purpose": "source_discovery_smoke_test_only",
        "not_approved_for": ["production_scoring", "investment_ranking", "training_without_acceptance"],
        "network_checks": len(results),
        "configured_tindex": bool(os.environ.get("TINDEX_API_BASE_URL", "").strip() and os.environ.get("TINDEX_API_TOKEN", "").strip()),
        "summary": {
            "http_reachable": sum(bool(r.get("reachable")) for r in results),
            "valid_response_shape": sum(bool(r.get("shape_valid")) for r in results),
            "not_configured": sum(r.get("status") == "not_configured" for r in results),
            "errors": sum(not bool(r.get("reachable")) and r.get("status") not in ("not_configured",) for r in results),
        },
        "sources": results,
        "interpretation": "Reachability is not data acceptance. Verify history, units, timestamps, survivorship, adjustments, licensing, cost and predictive contribution separately.",
    }
    out = os.path.abspath(args.output)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print(json.dumps({"status":"completed_discovery_smoke_test", "output":out, **report["summary"]}, ensure_ascii=False, indent=2))
    print("No response payloads, tokens, or headers were written to the report.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
