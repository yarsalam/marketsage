import pandas as pd
from fastapi.testclient import TestClient

import price_service


client = TestClient(price_service.app)


def test_health_endpoint():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_market_universe_discloses_scope():
    response = client.get("/markets")
    assert response.status_code == 200
    payload = response.json()
    assert payload["market_scope"] == "global_proxy"
    assert any("Iranian" in item for item in payload["limitations"])


def test_score_is_finite_for_constant_and_varied_series():
    dates = pd.date_range("2022-01-31", periods=18, freq="ME")
    prices = pd.DataFrame(
        {
            "UP": [100 + i * 2 for i in range(18)],
            "FLAT": [100 for _ in range(18)],
            "DOWN": [150 - i for i in range(18)],
        },
        index=dates,
    )
    scores = price_service.calculate_scores(prices)
    assert not scores.empty
    assert scores.index.is_unique
    assert scores.map(lambda value: pd.notna(value) and abs(value) < 10).all()
