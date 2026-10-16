from datetime import datetime, timezone

from fred_adapter import records_from_fred_vintages
from temporal_data import PointInTimeStore


def dt(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def test_fred_vintages_preserve_observation_and_revision_dates(tmp_path):
    fetched_at = dt("2026-10-16T10:00:00Z")
    rows = [
        {"date": "2024-01-01", "realtime_start": "2024-01-10", "value": "3.1"},
        {"date": "2024-01-01", "realtime_start": "2024-02-15", "value": "3.2"},
        {"date": "2024-02-01", "realtime_start": "2024-02-15", "value": "."},
        {"date": "2024-03-01", "realtime_start": "2024-03-15", "value": "NaN"},
    ]
    records = records_from_fred_vintages("CPIAUCSL", rows, retrieved_at=fetched_at, units="index")
    assert len(records) == 2
    assert records[0].record_key == "macro:US:CPIAUCSL:2024-01-01"
    assert records[0].published_at == dt("2024-01-10T23:59:59Z")
    assert records[0].retrieved_at == fetched_at
    assert records[1].source_revision == "2024-02-15"

    store = PointInTimeStore(tmp_path / "fred.sqlite")
    for record in records:
        store.append(record)
    january = store.as_of(
        as_of=dt("2024-01-31T23:59:59Z"), availability_basis="source"
    )
    february = store.as_of(
        as_of=dt("2024-02-20T00:00:00Z"), availability_basis="source"
    )
    assert len(january) == 1
    assert january[0]["payload"]["value"] == 3.1
    assert len(february) == 1
    assert february[0]["payload"]["value"] == 3.2


def test_fred_adapter_rejects_naive_retrieval_time():
    import pytest

    with pytest.raises(ValueError, match="timezone-aware"):
        records_from_fred_vintages(
            "CPIAUCSL",
            [{"date": "2024-01-01", "realtime_start": "2024-01-10", "value": "3.1"}],
            retrieved_at=datetime(2026, 10, 16),
        )
