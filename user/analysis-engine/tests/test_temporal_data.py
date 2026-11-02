from datetime import datetime, timezone
import json

import pytest

from temporal_data import PointInTimeStore, TemporalRecord


def dt(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def record(*, retrieved: str, value: float, published: str = "2024-01-02T09:00:00Z",
           revision: str | None = None) -> TemporalRecord:
    return TemporalRecord(
        record_key="macro:us:inflation:2024-01",
        source_id="official-statistics",
        market="US",
        data_kind="macro_release",
        observed_at=dt("2024-01-01T00:00:00Z"),
        published_at=dt(published) if published else None,
        retrieved_at=dt(retrieved),
        source_revision=revision,
        payload={"value": value},
    )


def test_as_of_uses_only_versions_already_retrieved(tmp_path):
    store = PointInTimeStore(tmp_path / "pit.sqlite")
    store.append(record(retrieved="2024-01-02T09:01:00Z", value=3.1, revision="initial"))
    store.append(record(retrieved="2024-02-15T09:01:00Z", value=3.2,
                        published="2024-02-15T09:00:00Z", revision="revision-1"))

    january = store.as_of(as_of=dt("2024-01-31T23:59:00Z"))
    february = store.as_of(as_of=dt("2024-02-20T00:00:00Z"))

    assert len(january) == 1
    assert january[0]["payload"]["value"] == 3.1
    assert january[0]["source_revision"] == "initial"
    assert len(february) == 1
    assert february[0]["payload"]["value"] == 3.2
    assert february[0]["source_revision"] == "revision-1"


def test_unpublished_future_release_is_not_visible(tmp_path):
    store = PointInTimeStore(tmp_path / "pit.sqlite")
    store.append(record(retrieved="2024-01-02T09:01:00Z", value=3.1,
                        published="2024-01-02T09:00:00Z"))
    assert store.as_of(as_of=dt("2024-01-02T08:30:00Z")) == []


def test_naive_timestamps_are_rejected(tmp_path):
    store = PointInTimeStore(tmp_path / "pit.sqlite")
    with pytest.raises(ValueError, match="timezone-aware"):
        store.append(TemporalRecord(
            record_key="x", source_id="s", market="US", data_kind="price",
            observed_at=datetime(2024, 1, 1),
            retrieved_at=dt("2024-01-02T00:00:00Z"), payload={"close": 1},
        ))


def test_same_payload_retry_is_idempotent_and_revisions_are_append_only(tmp_path):
    store = PointInTimeStore(tmp_path / "pit.sqlite")
    item = record(retrieved="2024-01-02T09:01:00Z", value=3.1)
    first_id = store.append(item)
    retry_id = store.append(item)
    store.append(record(retrieved="2024-02-15T09:01:00Z", value=3.2,
                        published="2024-02-15T09:00:00Z", revision="revision-1"))

    assert first_id == retry_id
    with store._connect() as conn:
        assert conn.execute("SELECT COUNT(*) FROM temporal_records").fetchone()[0] == 2


def test_non_finite_json_payload_is_rejected(tmp_path):
    store = PointInTimeStore(tmp_path / "pit.sqlite")
    item = record(retrieved="2024-01-02T09:01:00Z", value=float("nan"))
    with pytest.raises(ValueError):
        store.append(item)



def test_historical_source_vintages_can_be_replayed_after_later_download(tmp_path):
    store = PointInTimeStore(tmp_path / "pit.sqlite")
    # Both vintages were downloaded in 2026, but the publisher says they became
    # available in January and February 2024 respectively.
    store.append(TemporalRecord(
        record_key="macro:us:inflation:2024-01",
        source_id="fred:TEST",
        market="US",
        data_kind="macro_release",
        observed_at=dt("2024-01-01T00:00:00Z"),
        published_at=dt("2024-01-10T23:59:59Z"),
        retrieved_at=dt("2026-10-16T10:00:00Z"),
        source_revision="2024-01-10",
        payload={"value": 3.1},
    ))
    store.append(TemporalRecord(
        record_key="macro:us:inflation:2024-01",
        source_id="fred:TEST",
        market="US",
        data_kind="macro_release",
        observed_at=dt("2024-01-01T00:00:00Z"),
        published_at=dt("2024-02-15T23:59:59Z"),
        retrieved_at=dt("2026-10-16T10:00:00Z"),
        source_revision="2024-02-15",
        payload={"value": 3.2},
    ))

    # Captured replay correctly has no record in 2024; source-vintage replay
    # can reconstruct what the provider says was available at each cutoff.
    assert store.as_of(as_of=dt("2024-01-31T00:00:00Z")) == []
    jan = store.as_of(as_of=dt("2024-01-31T00:00:00Z"), availability_basis="source")
    feb = store.as_of(as_of=dt("2024-02-20T00:00:00Z"), availability_basis="source")
    assert jan[0]["payload"]["value"] == 3.1
    assert feb[0]["payload"]["value"] == 3.2



def test_summary_reports_series_coverage_without_exposing_payloads(tmp_path):
    store = PointInTimeStore(tmp_path / "pit.sqlite")
    store.append(TemporalRecord(
        record_key="SPY:2024-01-01",
        source_id="global.yahoo_finance.yfinance",
        market="global_proxy",
        data_kind="adjusted_close",
        observed_at=dt("2024-01-01T00:00:00Z"),
        retrieved_at=dt("2024-01-02T00:00:00Z"),
        payload={"symbol": "SPY", "close": 100.0},
    ))
    store.append(TemporalRecord(
        record_key="SPY:2024-01-01",
        source_id="global.yahoo_finance.yfinance",
        market="global_proxy",
        data_kind="adjusted_close",
        observed_at=dt("2024-01-01T00:00:00Z"),
        retrieved_at=dt("2024-01-03T00:00:00Z"),
        payload={"symbol": "SPY", "close": 101.0},
    ))
    summary = store.summary()
    assert summary["record_versions"] == 2
    assert len(summary["series"]) == 1
    series = summary["series"][0]
    assert series["series_key"] == "SPY"
    assert series["distinct_records"] == 1
    assert series["stored_versions"] == 2
    assert series["latest_retrieved_at"] == "2024-01-03T00:00:00+00:00"
    assert "payload" not in series


def test_source_as_of_quarantines_records_without_publication_timestamp(tmp_path):
    store = PointInTimeStore(tmp_path / "pit.sqlite")
    store.append(TemporalRecord(
        record_key="event:issuer:2024-01-10",
        source_id="unverified-news-index",
        market="global",
        data_kind="candidate_event",
        observed_at=dt("2024-01-10T00:00:00Z"),
        published_at=None,
        retrieved_at=dt("2024-01-10T12:00:00Z"),
        payload={"headline": "unverified candidate"},
    ))

    cutoff = dt("2024-01-11T00:00:00Z")
    # Captured replay can reproduce what the system had ingested, but it
    # cannot establish when the publisher made this candidate available.
    assert len(store.as_of(as_of=cutoff, availability_basis="captured")) == 1
    # Source-vintage replay fails closed when publication time is unknown.
    assert store.as_of(as_of=cutoff, availability_basis="source") == []




def test_summary_keeps_distinct_macro_series_separate(tmp_path):
    store = PointInTimeStore(tmp_path / "pit.sqlite")
    for key, observed, retrieved, value in [
        ("macro:US:CPIAUCSL:2024-01-01", "2024-01-01T00:00:00Z", "2024-01-10T00:00:00Z", 3.1),
        ("macro:US:CPIAUCSL:2024-02-01", "2024-02-01T00:00:00Z", "2024-02-10T00:00:00Z", 3.2),
        ("macro:US:UNRATE:2024-01-01", "2024-01-01T00:00:00Z", "2024-01-10T00:00:00Z", 3.7),
    ]:
        store.append(TemporalRecord(
            record_key=key, source_id="fred:TEST", market="US", data_kind="macro_release",
            observed_at=dt(observed), published_at=dt(retrieved), retrieved_at=dt(retrieved),
            payload={"value": value},
        ))

    summary = store.summary()
    series = {item["series_key"]: item for item in summary["series"]}
    assert set(series) == {"CPIAUCSL", "UNRATE"}
    assert series["CPIAUCSL"]["distinct_records"] == 2
    assert series["CPIAUCSL"]["stored_versions"] == 2
    assert series["UNRATE"]["distinct_records"] == 1
    assert summary["record_versions"] == 3



def test_in_memory_store_persists_between_operations():
    store = PointInTimeStore(":memory:")
    item = record(retrieved="2024-01-02T09:01:00Z", value=3.1)
    store.append(item)

    rows = store.as_of(as_of=dt("2024-01-03T00:00:00Z"))
    assert len(rows) == 1
    assert rows[0]["payload"]["value"] == 3.1
