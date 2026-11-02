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
    assert first.payload["normalization_status"] == "candidate_quarantined"
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
