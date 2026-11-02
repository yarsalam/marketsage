from __future__ import annotations

import pandas as pd
import pytest

from research.backtest import validate_monthly_prices


def test_monthly_matrix_accepts_one_observation_per_consecutive_month():
    index = pd.to_datetime(["2024-01-30", "2024-02-28", "2024-03-28", "2024-04-30"])
    prices = pd.DataFrame({"asset": [100.0, 101.0, 102.0, 103.0]}, index=index)
    result = validate_monthly_prices(prices)
    assert len(result) == 4


def test_monthly_matrix_rejects_multiple_observations_in_same_month():
    index = pd.to_datetime(["2024-01-15", "2024-01-31", "2024-02-29", "2024-03-29"])
    prices = pd.DataFrame({"asset": [100.0, 101.0, 102.0, 103.0]}, index=index)
    with pytest.raises(ValueError, match="exactly one observation per calendar month"):
        validate_monthly_prices(prices)


def test_monthly_matrix_rejects_missing_calendar_month():
    index = pd.to_datetime(["2024-01-31", "2024-02-29", "2024-04-30", "2024-05-31"])
    prices = pd.DataFrame({"asset": [100.0, 101.0, 102.0, 103.0]}, index=index)
    with pytest.raises(ValueError, match="consecutive calendar months"):
        validate_monthly_prices(prices)
