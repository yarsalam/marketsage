import json
from datetime import datetime, timezone

import numpy as np
import pandas as pd
import pytest
from fastapi import HTTPException

import price_service
from fastapi.testclient import TestClient
from temporal_data import PointInTimeStore

client = TestClient(price_service.app)


def provider_frame():
    dates = pd.date_range("2023-01-01", periods=300, freq="D")
    tickers = ["BTC-USD", "ETH-USD", "SOL-USD"]
    columns = pd.MultiIndex.from_product([["Close"], tickers])
    values = np.column_stack([100 + np.arange(len(dates)), 80 + np.arange(len(dates)), 50 + np.arange(len(dates))])
    return pd.DataFrame(values, index=dates, columns=columns)


def test_extract_close_preserves_missing_values_and_expected_universe():
    raw = provider_frame()
    raw.loc[raw.index[50], ("Close", "BTC-USD")] = np.nan
    result = price_service._extract_close(raw)
    assert list(result.columns) == list(price_service.TICKERS)
    assert pd.isna(result.loc[raw.index[50], "BTC-USD"])
    assert result["GLD"].isna().all()


def test_extract_close_rejects_duplicate_dates():
    raw = provider_frame()
    raw.index = list(raw.index[:-1]) + [raw.index[-2]]
    with pytest.raises(RuntimeError, match="duplicate"):
        price_service._extract_close(raw)


def test_scoring_excludes_assets_without_13_complete_months():
    dates = pd.date_range("2022-01-31", periods=18, freq="ME")
    prices = pd.DataFrame({"good": np.linspace(100, 140, 18), "gap": np.linspace(100, 120, 18)}, index=dates)
    prices.iloc[-3, prices.columns.get_loc("gap")] = np.nan
    scores = price_service.calculate_scores(prices)
    assert list(scores.index) == ["good"]


def test_scoring_fails_when_no_assets_have_complete_recent_history():
    dates = pd.date_range("2022-01-31", periods=18, freq="ME")
    prices = pd.DataFrame({"gap": np.linspace(100, 120, 18)}, index=dates)
    prices.iloc[-1, 0] = np.nan
    with pytest.raises(HTTPException) as error:
        price_service.calculate_scores(prices)
    assert error.value.status_code == 503


def test_daily_snapshot_has_checksum_and_is_immutable(tmp_path):
    dates = pd.date_range("2024-01-01", periods=4, freq="D")
    prices = pd.DataFrame({"AAA": [10.0, 11.0, 12.0, 13.0]}, index=dates)
    now = datetime(2024, 1, 5, 10, tzinfo=timezone.utc)
    metadata = price_service.write_daily_snapshot(prices, now, tmp_path)
    csv_before = (tmp_path / "prices-2024-01-05.csv").read_bytes()
    changed = prices * 2
    second = price_service.write_daily_snapshot(changed, now, tmp_path)
    assert second["sha256"] == metadata["sha256"]
    assert (tmp_path / "prices-2024-01-05.csv").read_bytes() == csv_before
    saved = json.loads((tmp_path / "prices-2024-01-05.json").read_text())
    assert saved["rows"] == 4
    assert saved["sha256"] == metadata["sha256"]


def test_daily_snapshot_appends_prices_to_temporal_store_idempotently(tmp_path):
    dates = pd.date_range("2024-01-01", periods=3, freq="D")
    prices = pd.DataFrame({"SPY": [100.0, 101.0, 102.0], "GLD": [50.0, np.nan, 52.0]}, index=dates)
    retrieved_at = datetime(2024, 1, 5, 10, tzinfo=timezone.utc)

    price_service.write_daily_snapshot(prices, retrieved_at, tmp_path)
    store = PointInTimeStore(tmp_path / "temporal.sqlite3")
    first = store.as_of(as_of=datetime(2024, 1, 6, tzinfo=timezone.utc), market="global_proxy")
    assert len(first) == 5
    spy_day_one = next(row for row in first if row["record_key"] == "SPY:2024-01-01")
    assert spy_day_one["source_id"] == "global.yahoo_finance.yfinance"
    assert spy_day_one["payload"]["close"] == 100.0
    assert spy_day_one["published_at"] is None
    assert spy_day_one["retrieved_at"] == retrieved_at.isoformat()

    # Restart/retry uses the canonical snapshot and original retrieval time.
    price_service.write_daily_snapshot(prices * 2, retrieved_at, tmp_path)
    second = store.as_of(as_of=datetime(2024, 1, 6, tzinfo=timezone.utc), market="global_proxy")
    assert len(second) == 5
    assert next(row for row in second if row["record_key"] == "SPY:2024-01-01")["payload"]["close"] == 100.0


def test_sources_endpoint_exposes_versioned_registry_and_unapproved_candidates():
    response = client.get("/sources")
    assert response.status_code == 200
    payload = response.json()
    assert payload["registry_version"]
    entries = {entry["source_id"]: entry for entry in payload["sources"]}
    assert entries["global.yahoo_finance.yfinance"]["used_by_research_engine"] is True
    assert entries["global.yahoo_finance.yfinance"]["approved_for_production"] is False
    assert entries["iran.tsetmc"]["approved_for_production"] is False
    assert entries["iran.gold_fx"]["status"] == "provider_not_selected"
    assert entries["crypto.exchange_specific"]["approved_for_production"] is False


def test_backtest_endpoint_uses_real_calculation_and_reports_benchmarks(monkeypatch):
    dates = pd.date_range("2020-01-31", periods=72, freq="ME")
    t = np.arange(len(dates), dtype=float)
    prices = pd.DataFrame({
        "SPY": 100 * (1.006 ** t) * (1 + .02 * np.sin(t)),
        "GLD": 100 * (1.003 ** t) * (1 + .01 * np.cos(t)),
        "BTC-USD": 100 * (1.012 ** t) * (1 + .04 * np.sin(t / 2)),
    }, index=dates)
    monkeypatch.setattr(price_service, "get_prices", lambda: prices)
    response = client.get("/backtest")
    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["periods"] > 36
    assert payload["holdout"]["periods"] >= 12
    assert payload["holdout"]["start"] > payload["start"]
    assert payload["holdout"]["metrics"]["historical_var_95_monthly"] >= 0
    assert "equal_weight_monthly_rebalanced" in payload["benchmarks"]
    assert "SPY_buy_and_hold" in payload["benchmarks"]
    assert "60_40_SPY_GLD_monthly_rebalanced" in payload["benchmarks"]
    assert payload["confidence_status"] == "not_calibrated"


def test_backtest_endpoint_rejects_too_short_common_history(monkeypatch):
    dates = pd.date_range("2022-01-31", periods=18, freq="ME")
    prices = pd.DataFrame({"SPY": np.linspace(100, 120, 18), "GLD": np.linspace(100, 110, 18)}, index=dates)
    monkeypatch.setattr(price_service, "get_prices", lambda: prices)
    response = client.get("/backtest")
    assert response.status_code == 503

def test_monthly_prices_reject_stale_month_end_observations():
    dates = pd.date_range("2024-01-01", "2024-04-30", freq="D")
    prices = pd.DataFrame({"SPY": 100 + np.arange(len(dates), dtype=float)}, index=dates)
    prices.loc["2024-04-16":, "SPY"] = np.nan
    monthly = price_service.completed_monthly_prices(prices)
    assert pd.isna(monthly.loc[pd.Timestamp("2024-04-30"), "SPY"])
    assert monthly.loc[pd.Timestamp("2024-03-31"), "SPY"] > 0
