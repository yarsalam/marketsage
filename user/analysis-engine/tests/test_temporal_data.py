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
