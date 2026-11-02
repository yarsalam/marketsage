from __future__ import annotations

import sys
from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest

SCRIPT_DIR = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

from ingest_nerkhsanj_archive import (  # noqa: E402
    ArchiveError,
    jalali_to_gregorian,
    summarize_and_normalize,
)


def test_jalali_to_gregorian_known_modern_dates() -> None:
    assert jalali_to_gregorian("1405/07/29") == date(2026, 10, 21)
    assert jalali_to_gregorian("1399/12/30") == date(2021, 3, 20)
    assert jalali_to_gregorian("1399/01/01") == date(2020, 3, 20)


@pytest.mark.parametrize(
    "value",
    [
        "2026-10-21",
        "1405/13/01",
        "1405/07/00",
        "1405/07/32",
        "1404/12/30",  # Esfand 30 is invalid in this Jalali year.
        "1405/1/2 trailing",
    ],
)
def test_invalid_jalali_dates_are_rejected(value: str) -> None:
    with pytest.raises(ValueError):
        jalali_to_gregorian(value)


def test_normalizer_preserves_duplicates_and_quarantines_invalid_pairs() -> None:
    payload = {
        "series": [
            {
                "key": "bitcoin",
                "days": [
                    ["1405/07/29", 1200000000],
                    ["1405/07/29", 1200000000],
                    ["1405/07/28", 1100000000],
                    ["1405/07/28", 1110000000],
                    ["1404/12/30", 1000000000],
                    ["1405/07/27", 0],
                ],
            }
        ]
    }
    rows, manifest, rejected, report = summarize_and_normalize(
        payload,
        payload_sha256="a" * 64,
        retrieved_at_utc="2026-10-22T20:00:00+00:00",
    )
    assert len(rows) == 4
    assert len(manifest) == 1
    assert len(rejected) == 2
    assert {row["reason_code"] for row in rejected} == {
        "INVALID_JALALI_DATE",
        "INVALID_NONPOSITIVE_OR_NONNUMERIC_VALUE",
    }

    statuses = [row["row_quality_status"] for row in rows]
    assert statuses.count("DUPLICATE_DATE_IDENTICAL") == 2
    assert statuses.count("DUPLICATE_DATE_CONFLICT") == 2
    assert {row["observation_date"] for row in rows} == {
        "2026-10-20",
        "2026-10-21",
    }
    assert all(row["value_unit"] == "UNKNOWN_UNVERIFIED" for row in rows)
    assert all(row["value_semantics"] == "DAILY_PROVIDER_VALUE_NOT_VALIDATED_AS_CLOSE" for row in rows)
    assert all(row["source_approved"] == "false" for row in rows)
    assert all(row["eligible_for_scoring"] == "false" for row in rows)

    series = manifest[0]
    assert series["source_row_count"] == 6
    assert series["normalized_row_count"] == 4
    assert series["quarantined_row_count"] == 2
    assert series["unique_date_count"] == 2
    assert series["duplicate_date_count"] == 2
    assert series["conflicting_duplicate_date_count"] == 1
    assert series["first_date_gregorian"] == "2026-10-20"
    assert series["last_date_gregorian"] == "2026-10-21"
    assert report["raw_payload_saved"] is False
    assert report["source_approved"] is False
    assert report["investment_scoring_allowed"] is False
    assert report["backtest_approved"] is False
    assert report["outputs_are_price_feature_inputs"] is False


def test_unknown_provider_key_is_not_silently_interpreted() -> None:
    payload = {"series": [{"key": "mystery_asset", "days": [["1405/07/29", 10.5]]}]}
    rows, manifest, rejected, report = summarize_and_normalize(
        payload,
        payload_sha256="b" * 64,
        retrieved_at_utc="2026-10-22T20:00:00+00:00",
    )
    assert not rejected
    assert len(rows) == 1
    assert rows[0]["candidate_asset_family"] == "unknown_candidate"
    assert rows[0]["candidate_mapping_status"] == "UNMAPPED_KEY_REQUIRES_REVIEW"
    assert manifest[0]["value_unit"] == "UNKNOWN_UNVERIFIED"
    assert report["unknown_series_key_count"] == 1
    assert rows[0]["value"] == "10.5"


@pytest.mark.parametrize("payload", [None, [], {}, {"series": "not-an-array"}])
def test_invalid_top_level_payload_is_blocked(payload: object) -> None:
    with pytest.raises(ArchiveError):
        summarize_and_normalize(
            payload,
            payload_sha256="c" * 64,
            retrieved_at_utc="2026-10-22T20:00:00+00:00",
        )


def test_duplicate_series_keys_are_blocked() -> None:
    payload = {
        "series": [
            {"key": "dollar", "days": []},
            {"key": "dollar", "days": []},
        ]
    }
    with pytest.raises(ArchiveError, match="duplicate provider series key"):
        summarize_and_normalize(
            payload,
            payload_sha256="d" * 64,
            retrieved_at_utc="2026-10-22T20:00:00+00:00",
        )
