from __future__ import annotations

import sys

import pytest
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from build_tsetmc_adjusted_dataset import build_dataset


def test_builder_preserves_raw_prices_and_does_not_fill_missing_adjusted_dates():
    daily = [
        {
            "dEven": 20261015,
            "pClosing": 12345,
            "pDrCotVal": 12350,
            "priceFirst": 12000,
            "priceMax": 12400,
            "priceMin": 11900,
            "priceYesterday": 12100,
            "qTotTran5J": 100000,
            "qTotCap": 1234500000,
        },
        {
            "dEven": 20261014,
            "pClosing": 12100,
            "pDrCotVal": 12100,
            "priceFirst": 12000,
            "priceMax": 12200,
            "priceMin": 11900,
            "priceYesterday": 12000,
            "qTotTran5J": 90000,
            "qTotCap": 1000000000,
        },
    ]
    chart = {
        "20261015": ["20261015", "12500", "9800", "11000", "9877", "100000", "9876"]
    }

    rows, report = build_dataset(
        daily, chart, instrument_code="46348559193224090"
    )

    latest = next(row for row in rows if row["date"] == "2026-10-15")
    missing = next(row for row in rows if row["date"] == "2026-10-14")
    assert latest["close_raw"] == 12345
    assert latest["close_adj"] == 9876.0
    assert missing["close_raw"] == 12100
    assert missing["close_adj"] is None
    assert missing["adjustment_status"] == "missing_adjusted_chart_row"
    assert report["rows_with_adjusted_close"] == 1
    assert report["rows_without_adjusted_close"] == 1
    assert report["adjusted_ohlc_violation_observation_count"] == 0
    assert report["adjusted_ohlc_violation_flag_count_sample_capped"] == 0
    assert report["eligible_for_scoring"] is False


def test_builder_rejects_duplicate_daily_dates():
    row = {"dEven": 20261015, "pClosing": 100}
    try:
        build_dataset(
            [row, row],
            {"20261015": ["20261015", "120", "80", "100", "100", "10", "100"]},
            instrument_code="46348559193224090",
        )
    except ValueError as exc:
        assert "duplicate" in str(exc)
    else:
        raise AssertionError("duplicate history date should be rejected")


@pytest.mark.parametrize("instrument_code", ["", "FOLAD", "12 34"])
def test_builder_rejects_invalid_instrument_identity(instrument_code):
    with pytest.raises(ValueError, match="instrument_code must be numeric"):
        build_dataset(
            [{"dEven": 20261015, "pClosing": 100}],
            {"20261015": ["20261015", "120", "80", "100", "100", "10", "100"]},
            instrument_code=instrument_code,
        )


def test_builder_rejects_empty_raw_history():
    with pytest.raises(ValueError, match="non-empty JSON array"):
        build_dataset([], {"20261015": ["20261015", "120", "80", "100", "100", "10", "100"]},
                      instrument_code="46348559193224090")


def test_builder_rejects_invalid_adjusted_close_instead_of_falling_back_to_raw():
    daily = [{"dEven": 20261015, "pClosing": 100}]
    chart = {"20261015": ["20261015", "120", "80", "100", "100", "10", "0"]}
    with pytest.raises(ValueError, match="chart close_adj"):
        build_dataset(daily, chart, instrument_code="46348559193224090")


def test_builder_flags_adjusted_ohlc_inconsistencies_without_repairing_rows():
    daily = [{"dEven": 20261015, "pClosing": 100}]
    chart = {
        "20261015": ["20261015", "100", "90", "80", "106", "10", "105"]
    }

    rows, report = build_dataset(
        daily, chart, instrument_code="46348559193224090"
    )

    assert rows[0]["open_adj"] == 80.0
    assert rows[0]["high_adj"] == 100.0
    assert rows[0]["low_adj"] == 90.0
    assert rows[0]["last_adj"] == 106.0
    assert rows[0]["close_adj"] == 105.0
    assert report["adjusted_ohlc_violation_observation_count"] == 1
    assert report["adjusted_ohlc_violation_flag_count_sample_capped"] == 3
    assert report["adjusted_ohlc_violation_samples"] == [{
        "date": "2026-10-15",
        "flags": [
            "open_outside_low_high",
            "last_outside_low_high",
            "close_outside_low_high",
        ],
    }]
    assert report["eligible_for_scoring"] is False
