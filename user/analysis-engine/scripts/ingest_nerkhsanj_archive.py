#!/usr/bin/env python3
"""Ingest the Nerkhsanj announced daily archive as local, unapproved candidate data.

The script performs one bounded HTTPS GET unless --input-json is provided. It
converts valid Jalali dates to Gregorian dates, retains source series keys, never
guesses units, preserves duplicate-date observations with explicit flags, and
writes only local outputs outside Git by default. Nothing is approved for scoring.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import re
import sys
from collections import defaultdict
from datetime import date, datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

import httpx

SOURCE_ID = "iran.nerkhsanj.rates_archive"
ARCHIVE_URL = "https://nerkh.jahankhahan.shop/data/rates.json"
USER_AGENT = "MarketSage/0.1 source-discovery"
MAX_RESPONSE_BYTES = 25_000_000
JALALI_RE = re.compile(r"^([0-9]{4})/([0-9]{1,2})/([0-9]{1,2})$")

# These are labels inferred from provider key names, not verified instrument contracts.
# Values and quote conventions must remain unknown until independently reconciled.
SERIES_CANDIDATES: dict[str, tuple[str, str, str]] = {
    "dollar": ("iran_fx", "IR_NERKHANSAJ_USD_RATE_CANDIDATE", "USD rate candidate; free/official market convention unverified"),
    "euro": ("iran_fx", "IR_NERKHANSAJ_EUR_RATE_CANDIDATE", "EUR rate candidate; quote convention unverified"),
    "yuan": ("iran_fx", "IR_NERKHANSAJ_CNY_RATE_CANDIDATE", "CNY rate candidate; quote convention unverified"),
    "aed": ("iran_fx", "IR_NERKHANSAJ_AED_RATE_CANDIDATE", "AED rate candidate; quote convention unverified"),
    "lira": ("iran_fx", "IR_NERKHANSAJ_TRY_RATE_CANDIDATE", "TRY rate candidate; quote convention unverified"),
    "pound": ("iran_fx", "IR_NERKHANSAJ_GBP_RATE_CANDIDATE", "GBP rate candidate; quote convention unverified"),
    "cad": ("iran_fx", "IR_NERKHANSAJ_CAD_RATE_CANDIDATE", "CAD rate candidate; quote convention unverified"),
    "aud": ("iran_fx", "IR_NERKHANSAJ_AUD_RATE_CANDIDATE", "AUD rate candidate; quote convention unverified"),
    "chf": ("iran_fx", "IR_NERKHANSAJ_CHF_RATE_CANDIDATE", "CHF rate candidate; quote convention unverified"),
    "sar": ("iran_fx", "IR_NERKHANSAJ_SAR_RATE_CANDIDATE", "SAR rate candidate; quote convention unverified"),
    "qar": ("iran_fx", "IR_NERKHANSAJ_QAR_RATE_CANDIDATE", "QAR rate candidate; quote convention unverified"),
    "kwd": ("iran_fx", "IR_NERKHANSAJ_KWD_RATE_CANDIDATE", "KWD rate candidate; quote convention unverified"),
    "omr": ("iran_fx", "IR_NERKHANSAJ_OMR_RATE_CANDIDATE", "OMR rate candidate; quote convention unverified"),
    "iqd": ("iran_fx", "IR_NERKHANSAJ_IQD_RATE_CANDIDATE", "IQD rate candidate; quote convention unverified"),
    "afn": ("iran_fx", "IR_NERKHANSAJ_AFN_RATE_CANDIDATE", "AFN rate candidate; quote convention unverified"),
    "rub": ("iran_fx", "IR_NERKHANSAJ_RUB_RATE_CANDIDATE", "RUB rate candidate; quote convention unverified"),
    "inr": ("iran_fx", "IR_NERKHANSAJ_INR_RATE_CANDIDATE", "INR rate candidate; quote convention unverified"),
    "gold": ("iran_gold", "IR_NERKHANSAJ_GOLD_UNSPECIFIED_CANDIDATE", "Gold price candidate; purity, weight and quote unit unverified"),
    "gold24": ("iran_gold", "IR_NERKHANSAJ_GOLD24_CANDIDATE", "24K gold candidate inferred from key only; unit unverified"),
    "gram": ("iran_gold", "IR_NERKHANSAJ_GRAM_GOLD_CANDIDATE", "Possible gram-gold series inferred from key only; meaning unverified"),
    "mesghal": ("iran_gold", "IR_NERKHANSAJ_MESGHAL_GOLD_CANDIDATE", "Mesghal gold candidate inferred from key only; exact unit unverified"),
    "coin": ("iran_coin", "IR_NERKHANSAJ_COIN_UNSPECIFIED_CANDIDATE", "Coin price candidate; denomination/type unverified"),
    "bahar": ("iran_coin", "IR_NERKHANSAJ_BAHAR_COIN_CANDIDATE", "Bahar coin candidate inferred from key only; subtype/quote unit unverified"),
    "half": ("iran_coin", "IR_NERKHANSAJ_HALF_COIN_CANDIDATE", "Half-coin candidate inferred from key only; subtype/quote unit unverified"),
    "quarter": ("iran_coin", "IR_NERKHANSAJ_QUARTER_COIN_CANDIDATE", "Quarter-coin candidate inferred from key only; subtype/quote unit unverified"),
    "tether": ("iran_crypto_local", "IR_NERKHANSAJ_TETHER_CANDIDATE", "Tether/local-price candidate; parity and quote currency unverified"),
    "bitcoin": ("iran_crypto_local", "IR_NERKHANSAJ_BITCOIN_CANDIDATE", "Bitcoin/local-price candidate; quote currency and venue unverified"),
    "silver": ("iran_precious_metal", "IR_NERKHANSAJ_SILVER_CANDIDATE", "Silver candidate; weight, purity and quote unit unverified"),
}
CSV_FIELDS = [
    "source_id", "provider_series_key", "candidate_asset_id", "candidate_asset_family",
    "candidate_mapping_status", "candidate_interpretation", "observation_date",
    "observation_date_jalali", "value", "value_unit", "value_semantics",
    "row_quality_status", "source_payload_sha256", "retrieved_at_utc", "source_url",
    "source_approved", "eligible_for_scoring",
]
MANIFEST_FIELDS = [
    "source_id", "provider_series_key", "candidate_asset_id", "candidate_asset_family",
    "candidate_mapping_status", "candidate_interpretation", "source_row_count",
    "normalized_row_count", "quarantined_row_count", "unique_date_count",
    "duplicate_date_count", "conflicting_duplicate_date_count",
    "first_date_jalali", "last_date_jalali", "first_date_gregorian",
    "last_date_gregorian", "invalid_date_count", "invalid_value_count",
    "value_unit", "value_semantics", "rights_status", "source_approved",
    "eligible_for_scoring",
]
REJECT_FIELDS = [
    "provider_series_key", "series_index", "pair_index", "jalali_date",
    "value_repr", "reason_code", "source_payload_sha256",
]


class ArchiveError(RuntimeError):
    """Sanitized source/schema/normalization failure."""


def _is_gregorian_leap(year: int) -> bool:
    return year % 4 == 0 and (year % 100 != 0 or year % 400 == 0)


def jalali_to_gregorian(jalali_text: str) -> date:
    """Convert a validated YYYY/MM/DD Jalali date without external dependencies.

    The conversion is round-trip checked with the corresponding Gregorian-to-Jalali
    algorithm so invalid Esfand 30 dates cannot silently roll into the next year.
    """
    match = JALALI_RE.fullmatch(str(jalali_text).strip())
    if not match:
        raise ValueError("date must be Jalali YYYY/MM/DD")
    jy, jm, jd = (int(part) for part in match.groups())
    if not 1200 <= jy <= 1600 or not 1 <= jm <= 12:
        raise ValueError("Jalali year or month is outside supported range")
    max_day = 31 if jm <= 6 else 30 if jm <= 11 else 30
    if not 1 <= jd <= max_day:
        raise ValueError("Jalali day is outside month range")

    # Widely used integer day-number conversion for the modern Jalali calendar.
    shifted_year = jy + 1595
    days = (
        -355668 + 365 * shifted_year
        + (shifted_year // 33) * 8
        + ((shifted_year % 33 + 3) // 4)
        + jd
    )
    days += (jm - 1) * 31 if jm < 7 else 186 + (jm - 7) * 30

    gy = 400 * (days // 146097)
    days %= 146097
    if days > 36524:
        days -= 1
        gy += 100 * (days // 36524)
        days %= 36524
        if days >= 365:
            days += 1
    gy += 4 * (days // 1461)
    days %= 1461
    if days > 365:
        gy += (days - 1) // 365
        days = (days - 1) % 365
    gd = days + 1

    gregorian_month_lengths = [
        31, 29 if _is_gregorian_leap(gy) else 28, 31, 30, 31, 30,
        31, 31, 30, 31, 30, 31,
    ]
    gm = 1
    while gm <= 12 and gd > gregorian_month_lengths[gm - 1]:
        gd -= gregorian_month_lengths[gm - 1]
        gm += 1
    try:
        converted = date(gy, gm, gd)
    except ValueError:
        raise ValueError("Jalali date converted outside Gregorian calendar range") from None
    if gregorian_to_jalali(converted) != (jy, jm, jd):
        raise ValueError("invalid Jalali calendar date (failed round-trip validation)")
    return converted


def gregorian_to_jalali(value: date) -> tuple[int, int, int]:
    """Inverse of jalali_to_gregorian for round-trip date validation."""
    gy, gm, gd = value.year, value.month, value.day
    month_lengths = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
    gy2, gm2, gd2 = gy - 1600, gm - 1, gd - 1
    day_number = (
        365 * gy2 + (gy2 + 3) // 4 - (gy2 + 99) // 100
        + (gy2 + 399) // 400
    )
    day_number += sum(month_lengths[:gm2])
    if gm > 2 and _is_gregorian_leap(gy):
        day_number += 1
    day_number += gd2
    j_day_number = day_number - 79
    j_np = j_day_number // 12053
    j_day_number %= 12053
    jy = 979 + 33 * j_np + 4 * (j_day_number // 1461)
    j_day_number %= 1461
    if j_day_number >= 366:
        jy += (j_day_number - 1) // 365
        j_day_number = (j_day_number - 1) % 365
    if j_day_number < 186:
        jm = 1 + j_day_number // 31
        jd = 1 + j_day_number % 31
    else:
        jm = 7 + (j_day_number - 186) // 30
        jd = 1 + (j_day_number - 186) % 30
    return jy, jm, jd


def _positive_decimal(value: Any) -> Decimal | None:
    # Match the observed contract strictly: JSON numeric scalars only, not booleans/strings.
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    try:
        number = Decimal(str(value))
    except (InvalidOperation, ValueError):
        return None
    if not number.is_finite() or number <= 0:
        return None
    return number


def _candidate(key: str) -> tuple[str, str, str, str]:
    mapped = SERIES_CANDIDATES.get(key)
    if mapped:
        family, asset_id, interpretation = mapped
        return asset_id, family, "KEY_NAME_CANDIDATE_ONLY", interpretation
    safe_key = re.sub(r"[^A-Za-z0-9]+", "_", key).strip("_").upper()[:50] or "UNKNOWN"
    return (
        f"IR_NERKHANSAJ_UNMAPPED_{safe_key}_CANDIDATE",
        "unknown_candidate",
        "UNMAPPED_KEY_REQUIRES_REVIEW",
        "No interpretation assigned; provider series key retained without inference",
    )


def summarize_and_normalize(
    payload: Any,
    *,
    payload_sha256: str,
    retrieved_at_utc: str,
    source_url: str = ARCHIVE_URL,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
    """Return normalized rows, series manifest, quarantine rows, and summary."""
    if not isinstance(payload, dict) or not isinstance(payload.get("series"), list):
        raise ArchiveError("response does not match the expected object with a series array")
    if len(payload["series"]) > 500:
        raise ArchiveError("series count exceeded safety limit")
    seen_keys: set[str] = set()
    parsed_series: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []

    for series_index, item in enumerate(payload["series"]):
        if not isinstance(item, dict):
            raise ArchiveError(f"series item {series_index} is not an object")
        key = item.get("key")
        pairs = item.get("days")
        if not isinstance(key, str) or not key.strip() or not isinstance(pairs, list):
            raise ArchiveError(f"series item {series_index} lacks a string key or days array")
        key = key.strip()
        if key in seen_keys:
            raise ArchiveError(f"duplicate provider series key: {key}")
        seen_keys.add(key)
        asset_id, family, mapping_status, interpretation = _candidate(key)
        accepted: list[dict[str, Any]] = []
        date_values: dict[str, list[Decimal]] = defaultdict(list)
        valid_date_values: list[tuple[str, date, Decimal, int]] = []
        invalid_date_count = 0
        invalid_value_count = 0

        for pair_index, pair in enumerate(pairs):
            jalali_text = None
            value_obj: Any = None
            if isinstance(pair, list) and len(pair) == 2:
                jalali_text, value_obj = pair
            else:
                rejected.append({
                    "provider_series_key": key, "series_index": series_index,
                    "pair_index": pair_index, "jalali_date": "",
                    "value_repr": "", "reason_code": "INVALID_PAIR_SHAPE",
                    "source_payload_sha256": payload_sha256,
                })
                invalid_date_count += 1
                invalid_value_count += 1
                continue

            try:
                if not isinstance(jalali_text, str):
                    raise ValueError
                gregorian_date = jalali_to_gregorian(jalali_text)
            except ValueError:
                rejected.append({
                    "provider_series_key": key, "series_index": series_index,
                    "pair_index": pair_index, "jalali_date": str(jalali_text or ""),
                    "value_repr": repr(value_obj)[:100], "reason_code": "INVALID_JALALI_DATE",
                    "source_payload_sha256": payload_sha256,
                })
                invalid_date_count += 1
                continue

            number = _positive_decimal(value_obj)
            if number is None:
                rejected.append({
                    "provider_series_key": key, "series_index": series_index,
                    "pair_index": pair_index, "jalali_date": jalali_text,
                    "value_repr": repr(value_obj)[:100], "reason_code": "INVALID_NONPOSITIVE_OR_NONNUMERIC_VALUE",
                    "source_payload_sha256": payload_sha256,
                })
                invalid_value_count += 1
                continue
            iso_date = gregorian_date.isoformat()
            date_values[iso_date].append(number)
            valid_date_values.append((jalali_text, gregorian_date, number, pair_index))

        duplicate_dates = {d for d, values in date_values.items() if len(values) > 1}
        conflicting_dates = {
            d for d, values in date_values.items()
            if len({v for v in values}) > 1
        }
        for jalali_text, gregorian_date, number, pair_index in valid_date_values:
            iso_date = gregorian_date.isoformat()
            if iso_date in conflicting_dates:
                row_status = "DUPLICATE_DATE_CONFLICT"
            elif iso_date in duplicate_dates:
                row_status = "DUPLICATE_DATE_IDENTICAL"
            else:
                row_status = "CANDIDATE_VALID_UNAPPROVED"
            accepted.append({
                "source_id": SOURCE_ID,
                "provider_series_key": key,
                "candidate_asset_id": asset_id,
                "candidate_asset_family": family,
                "candidate_mapping_status": mapping_status,
                "candidate_interpretation": interpretation,
                "observation_date": iso_date,
                "observation_date_jalali": jalali_text,
                "value": format(number, "f"),
                "value_unit": "UNKNOWN_UNVERIFIED",
                "value_semantics": "DAILY_PROVIDER_VALUE_NOT_VALIDATED_AS_CLOSE",
                "row_quality_status": row_status,
                "source_payload_sha256": payload_sha256,
                "retrieved_at_utc": retrieved_at_utc,
                "source_url": source_url,
                "source_approved": "false",
                "eligible_for_scoring": "false",
                "_pair_index": pair_index,
            })
        accepted.sort(key=lambda row: (row["observation_date"], row["_pair_index"]))
        parsed_series.append({
            "key": key,
            "asset_id": asset_id,
            "family": family,
            "mapping_status": mapping_status,
            "interpretation": interpretation,
            "source_row_count": len(pairs),
            "accepted": accepted,
            "invalid_date_count": invalid_date_count,
            "invalid_value_count": invalid_value_count,
            "duplicate_dates": duplicate_dates,
            "conflicting_dates": conflicting_dates,
        })

    normalized: list[dict[str, Any]] = []
    manifest: list[dict[str, Any]] = []
    for series in parsed_series:
        accepted = series["accepted"]
        dates = [row["observation_date"] for row in accepted]
        jalali_dates = [row["observation_date_jalali"] for row in accepted]
        normalized.extend({k: v for k, v in row.items() if k != "_pair_index"} for row in accepted)
        manifest.append({
            "source_id": SOURCE_ID,
            "provider_series_key": series["key"],
            "candidate_asset_id": series["asset_id"],
            "candidate_asset_family": series["family"],
            "candidate_mapping_status": series["mapping_status"],
            "candidate_interpretation": series["interpretation"],
            "source_row_count": series["source_row_count"],
            "normalized_row_count": len(accepted),
            "quarantined_row_count": series["source_row_count"] - len(accepted),
            "unique_date_count": len(set(dates)),
            "duplicate_date_count": len(series["duplicate_dates"]),
            "conflicting_duplicate_date_count": len(series["conflicting_dates"]),
            "first_date_jalali": min(jalali_dates) if jalali_dates else "",
            "last_date_jalali": max(jalali_dates) if jalali_dates else "",
            "first_date_gregorian": min(dates) if dates else "",
            "last_date_gregorian": max(dates) if dates else "",
            "invalid_date_count": series["invalid_date_count"],
            "invalid_value_count": series["invalid_value_count"],
            "value_unit": "UNKNOWN_UNVERIFIED",
            "value_semantics": "DAILY_PROVIDER_VALUE_NOT_VALIDATED_AS_CLOSE",
            "rights_status": "UNREVIEWED",
            "source_approved": "false",
            "eligible_for_scoring": "false",
        })
    normalized.sort(key=lambda row: (row["candidate_asset_id"], row["observation_date"], row["provider_series_key"]))
    summary = {
        "source_id": SOURCE_ID,
        "ingestion_version": "1.0.0",
        "status": "COMPLETED_CANDIDATE_ONLY",
        "retrieved_at_utc": retrieved_at_utc,
        "source_url": source_url,
        "source_payload_sha256": payload_sha256,
        "source_payload_bytes": None,
        "raw_payload_saved": False,
        "source_terms_reviewed": False,
        "upstream_lineage_verified": False,
        "unit_semantics_verified": False,
        "jalali_calendar_validation": "round_trip_checked",
        "series_count": len(manifest),
        "source_rows": sum(row["source_row_count"] for row in manifest),
        "normalized_rows": len(normalized),
        "quarantined_pairs": len(rejected),
        "duplicate_date_series_count": sum(1 for row in manifest if row["duplicate_date_count"]),
        "conflicting_duplicate_date_series_count": sum(1 for row in manifest if row["conflicting_duplicate_date_count"]),
        "unknown_series_key_count": sum(1 for row in manifest if row["candidate_mapping_status"] == "UNMAPPED_KEY_REQUIRES_REVIEW"),
        "source_approved": False,
        "eligible_for_scoring": False,
        "adjusted_returns_approved": False,
        "investment_scoring_allowed": False,
        "backtest_approved": False,
        "outputs_are_price_feature_inputs": False,
        "limitations": [
            "A key-name candidate mapping is not proof of instrument identity or quote convention.",
            "Values are not treated as OHLC close prices; conversion to the shared market_prices_daily contract is intentionally blocked pending semantics review.",
            "Units, market convention, upstream data lineage, reliability and usage rights are unverified.",
            "Normalized candidate values are written locally outside Git for review; do not redistribute or use commercially without terms review.",
            "No scoring, investment ranking or backtest approval is granted by a successful ingestion.",
        ],
    }
    return normalized, manifest, rejected, summary


def fetch_archive(timeout: float = 15.0) -> tuple[bytes, int]:
    """Perform exactly one HTTPS GET, with no redirects/retries and a bounded response."""
    try:
        with httpx.Client(
            timeout=timeout,
            follow_redirects=False,
            headers={"Accept": "application/json", "User-Agent": USER_AGENT},
        ) as client:
            with client.stream("GET", ARCHIVE_URL) as response:
                if response.status_code == 429:
                    raise ArchiveError("provider returned HTTP 429; no retry attempted")
                if response.status_code < 200 or response.status_code >= 300:
                    raise ArchiveError(f"provider returned HTTP {response.status_code}; no retry attempted")
                body = bytearray()
                for chunk in response.iter_bytes():
                    body.extend(chunk)
                    if len(body) > MAX_RESPONSE_BYTES:
                        raise ArchiveError("response exceeded local size limit; no payload saved")
                return bytes(body), response.status_code
    except ArchiveError:
        raise
    except httpx.HTTPError as exc:
        raise ArchiveError(f"network request failed ({type(exc).__name__}); no retry attempted") from None


def require_vpn_on() -> bool:
    if not sys.stdin.isatty():
        print("VPN PRECHECK failed: interactive terminal required; no network request made.", file=sys.stderr)
        return False
    print("VPN PRECHECK: external host. Turn VPN ON before the archive request.")
    return input("Type VPN-ON to confirm: ").strip() == "VPN-ON"


def _write_csv(path: Path, rows: list[dict[str, Any]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input-json", help="Use an already captured local JSON response; makes no network request.")
    parser.add_argument("--output-root", default="/tmp/marketsage-nerkhsanj-ingestion")
    parser.add_argument("--timeout", type=float, default=15.0)
    args = parser.parse_args(argv)
    if args.timeout <= 0 or args.timeout > 120:
        parser.error("--timeout must be >0 and <=120 seconds")

    retrieved_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    if args.input_json:
        input_path = Path(args.input_json).expanduser()
        try:
            body = input_path.read_bytes()
        except OSError as exc:
            print(f"Could not read local input ({type(exc).__name__}).", file=sys.stderr)
            return 2
        if len(body) > MAX_RESPONSE_BYTES:
            print("Local JSON input exceeds the configured size limit.", file=sys.stderr)
            return 2
        source_url = "local-file:" + input_path.name
    else:
        if not require_vpn_on():
            print("VPN confirmation failed; no network request made.", file=sys.stderr)
            return 2
        try:
            body, _ = fetch_archive(args.timeout)
        except ArchiveError as exc:
            print(json.dumps({"status": "FAILED", "source_id": SOURCE_ID, "error": str(exc)}, indent=2), file=sys.stderr)
            return 1
        source_url = ARCHIVE_URL

    digest = hashlib.sha256(body).hexdigest()
    try:
        payload = json.loads(body.decode("utf-8"))
        normalized, manifest, rejected, summary = summarize_and_normalize(
            payload,
            payload_sha256=digest,
            retrieved_at_utc=retrieved_at,
            source_url=source_url,
        )
    except (UnicodeDecodeError, json.JSONDecodeError):
        print("Response was not valid UTF-8 JSON.", file=sys.stderr)
        return 1
    except ArchiveError as exc:
        print(f"Ingestion stopped: {exc}", file=sys.stderr)
        return 1

    summary["source_payload_bytes"] = len(body)
    run_id = datetime.now(timezone.utc).strftime("run_%Y%m%dT%H%M%S%fZ")
    out = Path(args.output_root).expanduser().resolve() / run_id
    normalized_path = out / "normalized" / "nerkhsanj_series_daily_values.csv"
    manifest_path = out / "normalized" / "nerkhsanj_series_manifest.csv"
    rejected_path = out / "quarantine" / "rejected_pairs.csv"
    report_path = out / "ingestion_report.json"
    _write_csv(normalized_path, normalized, CSV_FIELDS)
    _write_csv(manifest_path, manifest, MANIFEST_FIELDS)
    _write_csv(rejected_path, rejected, REJECT_FIELDS)
    summary.update({
        "run_id": run_id,
        "run_dir": str(out),
        "normalized_csv": str(normalized_path),
        "series_manifest_csv": str(manifest_path),
        "quarantine_csv": str(rejected_path),
    })
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "status": summary["status"],
        "source_id": SOURCE_ID,
        "run_dir": str(out),
        "series_count": summary["series_count"],
        "source_rows": summary["source_rows"],
        "normalized_rows": summary["normalized_rows"],
        "quarantined_pairs": summary["quarantined_pairs"],
        "duplicate_date_series_count": summary["duplicate_date_series_count"],
        "conflicting_duplicate_date_series_count": summary["conflicting_duplicate_date_series_count"],
        "source_payload_sha256": digest,
        "source_approved": False,
        "eligible_for_scoring": False,
        "backtest_approved": False,
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
