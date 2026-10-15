import numpy as np
import pandas as pd
import pytest
from fastapi import HTTPException

from price_service import calculate_scores


def test_scores_are_finite_and_rank_assets():
    dates = pd.date_range("2022-01-31", periods=18, freq="ME")
    prices = pd.DataFrame(
        {
            "uptrend": np.linspace(100, 180, len(dates)),
            "flat": np.full(len(dates), 100.0),
            "downtrend": np.linspace(180, 100, len(dates)),
        },
        index=dates,
    )

    scores = calculate_scores(prices)

    assert set(scores.index) == {"uptrend", "flat", "downtrend"}
    assert scores.notna().all()
    assert np.isfinite(scores.to_numpy()).all()
    assert scores["uptrend"] > scores["downtrend"]


def test_scoring_rejects_insufficient_history():
    dates = pd.date_range("2025-01-31", periods=4, freq="ME")
    prices = pd.DataFrame({"asset": [100, 101, 102, 103]}, index=dates)

    with pytest.raises(HTTPException) as error:
        calculate_scores(prices)

    assert error.value.status_code == 503
