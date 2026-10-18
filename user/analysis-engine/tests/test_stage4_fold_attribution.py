import numpy as np
import pandas as pd
import pytest

from research.backtest import BacktestConfig
from scripts.analyze_stage4_fold import analyze_fold


def test_fold_attribution_reconciles_gross_return_and_flags_selected_asset_jump():
    dates = pd.date_range("2020-01-31", periods=40, freq="ME")
    t = np.arange(len(dates), dtype=float)
    prices = pd.DataFrame({
        "A": 100 * (1.015 ** t),
        "B": 100 * (1.008 ** t),
        "C": 100 * (1.002 ** t),
    }, index=dates)
    # Persistent level shift creates one +200% monthly return without a reverse jump.
    prices.loc[dates[25]:, "A"] *= 3

    report = analyze_fold(
        prices,
        dates[24].date().isoformat(),
        dates[29].date().isoformat(),
        BacktestConfig(
            top_n=3,
            momentum_months=3,
            volatility_months=12,
            transaction_cost_bps=10,
            slippage_bps=25,
        ),
        outlier_return_threshold=1.0,
    )

    assert report["purpose"] == "exploratory_fold_attribution_only"
    assert report["ranking_approved"] is False
    assert report["source_scoring_approved"] is False
    assert report["periods"] == 6
    assert any(
        item["symbol"] == "A" and item["monthly_return"] == pytest.approx(2.045)
        for item in report["selected_asset_return_outliers"]
    )
    for row in report["monthly"]:
        assert sum(row["equal_weight_gross_contributions"].values()) == pytest.approx(
            row["gross_return"]
        )
        assert row["net_return"] <= row["gross_return"]
    assert "not compounded" in report["contribution_note"]


def test_fold_attribution_rejects_empty_window_and_bad_threshold():
    dates = pd.date_range("2020-01-31", periods=30, freq="ME")
    prices = pd.DataFrame({"A": np.linspace(100, 130, 30)}, index=dates)
    with pytest.raises(ValueError, match="no backtest return rows"):
        analyze_fold(prices, "2010-01-31", "2010-06-30")
    with pytest.raises(ValueError, match="greater than zero"):
        analyze_fold(prices, dates[20].date().isoformat(), dates[25].date().isoformat(),
                     outlier_return_threshold=0)
