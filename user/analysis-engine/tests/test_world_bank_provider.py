from decimal import Decimal

import httpx
import pytest

from world_bank_provider import WorldBankClient, WorldBankError, normalize_indicator_payload


def wb_row(year, value):
    return {
        "country": {"id": "IRN", "value": "Iran, Islamic Rep."},
        "countryiso3code": "IRN",
        "date": str(year),
        "value": value,
        "unit": "",
        "indicator": {"id": "FP.CPI.TOTL.ZG", "value": "Inflation"},
        "decimal": 1,
    }


def test_normalizes_world_bank_annual_series_and_keeps_missing_values_null():
    payload = [{"page": 1}, [wb_row(2022, "42.5"), wb_row(2023, None)]]
    rows = normalize_indicator_payload(
        payload, country="IRN", indicator="FP.CPI.TOTL.ZG"
    )

    assert [row["observation_year"] for row in rows] == ["2022", "2023"]
    assert rows[0]["value"] == Decimal("42.5")
    assert rows[1]["value"] is None
    assert rows[0]["publication_timestamp"] is None
    assert all(row["eligible_for_scoring"] is False for row in rows)


def test_client_requests_no_key_json_endpoint_and_bounded_history():
    seen = {}

    def handler(request):
        seen["path"] = request.url.path
        seen["params"] = dict(request.url.params)
        return httpx.Response(200, json=[{"page": 1}, [wb_row(2024, "5.1")]])

    with WorldBankClient(base_url="https://worldbank.example.test/v2",
                         transport=httpx.MockTransport(handler)) as client:
        rows = client.indicator("irn", "FP.CPI.TOTL.ZG",
                                start_year=2024, end_year=2024, per_page=10)

    assert seen["path"] == "/v2/country/IRN/indicator/FP.CPI.TOTL.ZG"
    assert seen["params"]["format"] == "json"
    assert seen["params"]["date"] == "2024:2024"
    assert seen["params"]["per_page"] == "10"
    assert rows[0]["value"] == Decimal("5.1")


def test_invalid_envelope_and_duplicate_years_fail_closed():
    with pytest.raises(WorldBankError):
        normalize_indicator_payload({"observations": []}, country="IRN",
                                    indicator="FP.CPI.TOTL.ZG")
    with pytest.raises(WorldBankError, match="duplicate"):
        normalize_indicator_payload(
            [{"page": 1}, [wb_row(2021, "1"), wb_row(2021, "2")]],
            country="IRN", indicator="FP.CPI.TOTL.ZG",
        )


def test_invalid_indicator_parameters_are_rejected_before_network():
    with WorldBankClient(base_url="https://worldbank.example.test/v2",
                         transport=httpx.MockTransport(
                             lambda request: pytest.fail("unexpected network call"))) as client:
        with pytest.raises(ValueError):
            client.indicator("../IRN", "FP.CPI.TOTL.ZG")
        with pytest.raises(ValueError):
            client.indicator("IRN", "FP.CPI.TOTL.ZG", start_year=2030, end_year=2020)
