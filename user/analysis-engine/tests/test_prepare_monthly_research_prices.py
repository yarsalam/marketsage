from __future__ import annotations

import pandas as pd
import pytest

from scripts.prepare_monthly_research_prices import load_monthly_series, prepare_monthly_panel


def write_csv(path, dates, **columns):
    frame = pd.DataFrame({"Date": dates, **columns})
    frame.to_csv(path, index=False)


def test_crypto_uses_close_and_monthly_last_observation(tmp_path):
    path = tmp_path / "BTC-USD.csv"
    write_csv(
        path,
        ["2024-01-30", "2024-01-31", "2024-02-28"],
        Close=[10.0, 11.0, 12.0],
        **{"Adj Close": [100.0, 110.0, 120.0]},
    )

    monthly, meta = load_monthly_series(path, "BTC-USD")

    assert monthly.tolist() == [11.0, 12.0]
    assert meta["price_column"] == "Close"
    assert meta["monthly_observations"] == 2


def test_non_crypto_requires_and_uses_adjusted_close(tmp_path):
    path = tmp_path / "SPY.csv"
    write_csv(
        path,
        ["2024-01-30", "2024-01-31", "2024-02-29"],
        Close=[10.0, 11.0, 12.0],
        **{"Adj Close": [9.0, 10.0, 11.0]},
    )

    monthly, meta = load_monthly_series(path, "SPY")

    assert monthly.tolist() == [10.0, 11.0]
    assert meta["price_column"] == "Adj Close"


def test_does_not_forward_fill_missing_calendar_month(tmp_path):
    path = tmp_path / "SPY.csv"
    write_csv(
        path,
        ["2024-01-31", "2024-03-29"],
        **{"Adj Close": [10.0, 12.0]},
    )

    monthly, meta = load_monthly_series(path, "SPY")

    assert len(monthly) == 2
    assert meta["missing_months_inside_observed_range"] == 1
    assert pd.Timestamp("2024-02-29", tz="UTC") not in monthly.index


def test_rejects_missing_adjusted_close_instead_of_falling_back(tmp_path):
    path = tmp_path / "SPY.csv"
    write_csv(path, ["2024-01-31"], Close=[10.0])

    with pytest.raises(ValueError, match="Adj Close"):
        load_monthly_series(path, "SPY")


@pytest.mark.parametrize(
    "dates, prices, message",
    [
        (["2024-01-31", "2024-01-31"], [10.0, 11.0], "duplicate"),
        (["2024-02-29", "2024-01-31"], [10.0, 11.0], "sorted"),
        (["2024-01-31", "not-a-date"], [10.0, 11.0], "invalid date"),
        (["2024-01-31", "2024-02-29"], [10.0, float("nan")], "non-finite"),
        (["2024-01-31", "2024-02-29"], [10.0, 0.0], "non-positive"),
    ],
)
def test_rejects_invalid_daily_input(tmp_path, dates, prices, message):
    path = tmp_path / "BTC-USD.csv"
    write_csv(path, dates, Close=prices)

    with pytest.raises(ValueError, match=message):
        load_monthly_series(path, "BTC-USD")


def test_panel_uses_only_months_observed_for_all_symbols(tmp_path):
    write_csv(
        tmp_path / "BTC-USD.csv",
        ["2024-01-31", "2024-02-29", "2024-03-31"],
        Close=[10.0, 11.0, 12.0],
    )
    write_csv(
        tmp_path / "SPY.csv",
        ["2024-01-31", "2024-03-29"],
        **{"Adj Close": [20.0, 22.0]},
    )

    panel, report = prepare_monthly_panel(tmp_path, ["BTC-USD", "SPY"])

    assert len(panel) == 2
    assert panel.columns.tolist() == ["BTC-USD", "SPY"]
    assert report["monthly_rows_before_alignment"] == 3
    assert report["monthly_rows_after_alignment"] == 2
    assert report["months_excluded_for_missing_asset_observations"] == 1
    assert report["ranking_approved"] is False


def test_missing_symbol_file_fails_closed(tmp_path):
    with pytest.raises(ValueError, match="expected file not found"):
        prepare_monthly_panel(tmp_path, ["BTC-USD"])
