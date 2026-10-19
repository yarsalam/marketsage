from __future__ import annotations

import json

import iran_live_data as live


def test_status_does_not_expose_credentials(monkeypatch, tmp_path):
    monkeypatch.setenv("IRAN_DATA_DB_PATH", str(tmp_path / "iran.sqlite3"))
    monkeypatch.setenv("TINDEX_API_BASE_URL", "https://api.example.test")
    monkeypatch.setenv("TINDEX_API_TOKEN", "secret-token")
    status = live.get_iran_data_status()
    assert status["configured"] is True
    assert status["production_approved"] is False
    assert "secret-token" not in json.dumps(status)


def test_latest_rates_are_empty_before_successful_refresh(monkeypatch, tmp_path):
    monkeypatch.setenv("IRAN_DATA_DB_PATH", str(tmp_path / "iran.sqlite3"))
    result = live.get_latest_currency_rates()
    assert result["status"] == "no_successful_refresh"
    assert result["rates"] == []
    assert result["eligible_for_scoring"] is False


def test_opportunities_fail_closed_without_approved_data(monkeypatch, tmp_path):
    monkeypatch.setenv("IRAN_DATA_DB_PATH", str(tmp_path / "iran.sqlite3"))
    result = live.get_iran_opportunities()
    assert result["status"] == "blocked_insufficient_approved_data"
    assert result["opportunities"] == []
    assert result["eligible_sources"] == []
    assert result["blocked_reasons"]


def test_refresh_persists_raw_payload_and_normalized_values(monkeypatch, tmp_path):
    monkeypatch.setenv("IRAN_DATA_DB_PATH", str(tmp_path / "iran.sqlite3"))

    class FakeClient:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return None

        def currency_rates(self):
            return {
                "success": True,
                "data": [
                    {"key": "usd", "name": "USD rate", "rate": 123456, "decimals": 0},
                    {"key": "gold", "name": "Gold quote", "rate": 123456.75, "decimals": 2},
                ],
            }

    monkeypatch.setattr(live, "TindexClient", FakeClient)
    result = live.refresh_tindex_currency_rates()
    assert result["status"] == "success"
    assert result["item_count"] == 2
    assert result["eligible_for_scoring"] is False

    latest = live.get_latest_currency_rates()
    assert latest["status"] == "data_available"
    assert [item["instrument_key"] for item in latest["rates"]] == ["gold", "usd"]
    assert all(item["unit"] is None for item in latest["rates"])
    assert all(item["eligible_for_scoring"] is False for item in latest["rates"])

    with live._connect() as db:
        raw = db.execute("SELECT payload_json FROM iran_raw_payloads").fetchone()[0]
        assert json.loads(raw)["success"] is True
        assert db.execute("SELECT COUNT(*) FROM iran_currency_observations").fetchone()[0] == 2
