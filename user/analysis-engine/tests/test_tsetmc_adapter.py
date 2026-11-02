from datetime import datetime, timezone

import pytest

import tsetmc_adapter
from source_registry import source_scoring_gate
from temporal_data import PointInTimeStore


INS_CODE = "46348559193224090"
RETRIEVED_AT = datetime(2026, 10, 16, 10, tzinfo=timezone.utc)


def sample_payload():
    return {
        "closingPriceDaily": [
            {
                "dEven": 20261015,
                "pClosing": 12345,
                "pDrCotVal": 12350,
                "priceFirst": 12000,
                "priceMax": 12400,
                "priceMin": 11900,
                "priceYesterday": 12100,
                "qTotTran5J": 100000,
                "zTotTran": 250,
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
                "zTotTran": 200,
                "qTotCap": 1000000000,
            },
        ]
    }


def sample_adjusted_chart():
    # Positional fields are checked against the raw daily-history fixture:
    # date, high, low, open, last-traded price, volume, closing price.
    return {
        "20261015": ["20261015", "12500", "9800", "11000", "9877", "100000", "9876"]
    }


def test_parser_normalizes_history_and_keeps_source_publication_unknown():
    records = tsetmc_adapter.parse_daily_history(
        sample_payload(), ins_code=INS_CODE, retrieved_at=RETRIEVED_AT
    )

    assert len(records) == 2
    first = records[0]
    assert first.source_id == "iran.tsetmc"
    assert first.market == "iran_candidate"
    assert first.data_kind == "daily_ohlcv_candidate"
    assert first.record_key == f"{INS_CODE}:2026-10-15"
    assert first.published_at is None
    assert first.retrieved_at == RETRIEVED_AT
    assert first.payload["close_candidate"] == 12345.0
    assert first.payload["price_unit"] == "rial_candidate_unverified"
    assert first.payload["normalization_status"] == "candidate_quarantined_raw_history"
    assert first.payload["eligible_for_scoring"] is False
    assert len(first.payload["source_response_sha256"]) == 64


def test_parser_rejects_empty_or_wrong_response_shape():
    with pytest.raises(tsetmc_adapter.TSETMCDataError, match="non-empty"):
        tsetmc_adapter.parse_daily_history(
            {"closingPriceDaily": []}, ins_code=INS_CODE, retrieved_at=RETRIEVED_AT
        )
    with pytest.raises(tsetmc_adapter.TSETMCDataError, match="non-empty"):
        tsetmc_adapter.parse_daily_history(
            {}, ins_code=INS_CODE, retrieved_at=RETRIEVED_AT
        )


@pytest.mark.parametrize(
    ("mutate", "message"),
    [
        (lambda row: row.update(dEven="not-a-date"), "invalid dEven"),
        (lambda row: row.update(pClosing=0), "pClosing"),
        (lambda row: row.update(pClosing=float("nan")), "pClosing"),
        (lambda row: row.update(pDrCotVal=-1), "pDrCotVal"),
        (lambda row: row.update(qTotCap=-5), "qTotCap"),
    ],
)
def test_parser_fails_closed_on_invalid_rows(mutate, message):
    payload = sample_payload()
    mutate(payload["closingPriceDaily"][0])
    with pytest.raises(tsetmc_adapter.TSETMCDataError, match=message):
        tsetmc_adapter.parse_daily_history(
            payload, ins_code=INS_CODE, retrieved_at=RETRIEVED_AT
        )


def test_parser_rejects_duplicate_dates_and_naive_retrieval_time():
    payload = sample_payload()
    payload["closingPriceDaily"][1]["dEven"] = 20261015
    with pytest.raises(tsetmc_adapter.TSETMCDataError, match="duplicate"):
        tsetmc_adapter.parse_daily_history(
            payload, ins_code=INS_CODE, retrieved_at=RETRIEVED_AT
        )

    with pytest.raises(tsetmc_adapter.TSETMCDataError, match="timezone-aware"):
        tsetmc_adapter.parse_daily_history(
            sample_payload(), ins_code=INS_CODE, retrieved_at=datetime(2026, 10, 16)
        )


def test_adjusted_chart_maps_price_fields_and_accepts_saved_json_shape():
    chart = tsetmc_adapter.parse_adjusted_chart(sample_adjusted_chart())
    assert chart["20261015"] == {
        "high_adj": 12500.0,
        "low_adj": 9800.0,
        "open_adj": 11000.0,
        "last_adj": 9877.0,
        "chart_volume": 100000.0,
        "close_adj": 9876.0,
    }


def test_adjusted_chart_parses_provider_delimited_text():
    chart = tsetmc_adapter.parse_adjusted_chart(
        "20261015,12500,9800,11000,9877,100000,9876;\n"
    )
    assert chart["20261015"]["close_adj"] == 9876.0


def test_adjusted_history_uses_provider_adjusted_close_and_keeps_raw_price():
    records = tsetmc_adapter.parse_adjusted_history(
        sample_payload(), sample_adjusted_chart(),
        ins_code=INS_CODE, retrieved_at=RETRIEVED_AT,
        daily_response_sha256="a" * 64,
        chart_response_sha256="b" * 64,
    )

    assert len(records) == 2
    first = records[0]
    assert first.data_kind == "daily_ohlcv_adjusted_candidate"
    assert first.record_key == f"{INS_CODE}:2026-10-15:adjusted"
    assert first.payload["close_candidate"] == 9876.0
    assert first.payload["raw_close_candidate"] == 12345.0
    assert first.payload["adjustment_status"] == "provider_supplied_unvalidated"
    assert first.payload["source_response_sha256"] != "a" * 64
    assert first.payload["eligible_for_scoring"] is False
    assert first.published_at is None


def test_adjusted_history_does_not_fall_back_to_raw_for_missing_chart_date():
    records = tsetmc_adapter.parse_adjusted_history(
        sample_payload(), sample_adjusted_chart(),
        ins_code=INS_CODE, retrieved_at=RETRIEVED_AT,
    )
    second = next(record for record in records if record.payload["observation_date"] == "2026-10-14")
    assert second.payload["close_candidate"] is None
    assert second.payload["raw_close_candidate"] == 12100.0
    assert second.payload["adjustment_status"] == "missing_adjusted_chart_row"
    assert second.payload["adjusted_chart_row_present"] is False


def test_adjusted_ingestion_stores_adjusted_series_and_reports_coverage(monkeypatch, tmp_path):
    monkeypatch.setattr(
        tsetmc_adapter,
        "fetch_daily_history",
        lambda ins_code, timeout=20.0: (sample_payload(), "a" * 64),
    )
    monkeypatch.setattr(
        tsetmc_adapter,
        "fetch_adjusted_chart",
        lambda ins_code, timeout=20.0: (
            tsetmc_adapter.parse_adjusted_chart(sample_adjusted_chart()), "b" * 64
        ),
    )
    store = PointInTimeStore(tmp_path / "temporal.sqlite3")
    result = tsetmc_adapter.ingest_adjusted_history(
        store, INS_CODE, retrieved_at=RETRIEVED_AT
    )

    assert result["ingested_records"] == 2
    assert result["rows_with_adjusted_close"] == 1
    assert result["rows_missing_adjusted_close"] == 1
    assert result["eligible_for_production_scoring"] is False
    captured = store.as_of(
        as_of=datetime(2026, 10, 17, tzinfo=timezone.utc),
        market="iran_candidate",
        data_kind="daily_ohlcv_adjusted_candidate",
        availability_basis="captured",
    )
    assert len(captured) == 2
    assert captured[0]["payload"]["close_candidate"] is None or captured[1]["payload"]["close_candidate"] is None


def test_ingested_records_remain_unavailable_to_source_vintage_replay(tmp_path):
    store = PointInTimeStore(tmp_path / "temporal.sqlite3")
    records = tsetmc_adapter.parse_daily_history(
        sample_payload(), ins_code=INS_CODE, retrieved_at=RETRIEVED_AT
    )
    for record in records:
        store.append(record)

    captured = store.as_of(
        as_of=datetime(2026, 10, 17, tzinfo=timezone.utc),
        market="iran_candidate",
        availability_basis="captured",
    )
    source_vintage = store.as_of(
        as_of=datetime(2026, 10, 17, tzinfo=timezone.utc),
        market="iran_candidate",
        availability_basis="source",
    )
    assert len(captured) == 2
    assert source_vintage == []


def test_candidate_adapter_does_not_enable_production_scoring():
    gate = source_scoring_gate("iran.tsetmc")
    assert gate["eligible_for_production_scoring"] is False
    assert "production_approval_missing" in gate["blocked_reasons"]
    assert "timestamp_quality_not_verified" in gate["blocked_reasons"]



def test_adjusted_chart_rejects_duplicate_dates_in_provider_text():
    duplicate = (
        "20261015,12500,9800,11000,9877,100000,9876;"
        "20261015,12600,9700,11100,9880,100100,9879;"
    )
    with pytest.raises(tsetmc_adapter.TSETMCDataError, match="duplicate date"):
        tsetmc_adapter.parse_adjusted_chart(duplicate)


@pytest.mark.parametrize(
    ("chart", "message"),
    [
        ({"20261015": ["20261015", "12500", "9800"]}, "at least seven"),
        ({"20261015": ["20261016", "12500", "9800", "11000", "9877", "100000", "9876"]}, "disagree"),
        ({"20261015": ["20261015", "12500", "9800", "11000", "9877", "100000", "0"]}, "chart close_adj"),
        ({"20261015": {"high_adj": 12500}}, "fields are incomplete"),
    ],
)
def test_adjusted_chart_rejects_incomplete_or_inconsistent_rows(chart, message):
    with pytest.raises(tsetmc_adapter.TSETMCDataError, match=message):
        tsetmc_adapter.parse_adjusted_chart(chart)


def test_adjusted_ingestion_does_not_store_partial_rows_when_chart_fetch_fails(
    monkeypatch, tmp_path
):
    monkeypatch.setattr(
        tsetmc_adapter,
        "fetch_daily_history",
        lambda ins_code, timeout=20.0: (sample_payload(), "a" * 64),
    )

    def fail_adjusted_chart(ins_code, timeout=20.0):
        raise tsetmc_adapter.TSETMCDataError("synthetic chart failure")

    monkeypatch.setattr(tsetmc_adapter, "fetch_adjusted_chart", fail_adjusted_chart)
    store = PointInTimeStore(tmp_path / "atomic-temporal.sqlite3")

    with pytest.raises(tsetmc_adapter.TSETMCDataError, match="synthetic chart failure"):
        tsetmc_adapter.ingest_adjusted_history(
            store, INS_CODE, retrieved_at=RETRIEVED_AT
        )

    captured = store.as_of(
        as_of=datetime(2026, 10, 18, tzinfo=timezone.utc),
        market="iran_candidate",
        data_kind="daily_ohlcv_adjusted_candidate",
        availability_basis="captured",
    )
    assert captured == []
