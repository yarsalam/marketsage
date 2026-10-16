from datetime import datetime, timezone

import pytest

from temporal_data import PointInTimeStore, TemporalRecord


def dt(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def item(*, key="series:1", market="global", kind="price", value=1,
         observed="2025-01-01T00:00:00Z", published="2025-01-02T00:00:00Z",
         retrieved="2025-01-03T00:00:00Z", source="fixture"):
    return TemporalRecord(
        record_key=key,
        source_id=source,
        market=market,
        data_kind=kind,
        observed_at=dt(observed),
        published_at=dt(published) if published else None,
        retrieved_at=dt(retrieved),
        payload={"value": value},
    )


def test_source_replay_returns_only_latest_published_revision_at_cutoff(tmp_path):
    store = PointInTimeStore(tmp_path / "pit.sqlite")
    store.append(item(value=10, published="2025-01-02T00:00:00Z",
                      retrieved="2025-02-01T00:00:00Z"))
    store.append(item(value=20, published="2025-02-10T00:00:00Z",
                      retrieved="2025-02-11T00:00:00Z"))

    early = store.as_of(as_of=dt("2025-01-31T00:00:00Z"), availability_basis="source")
    later = store.as_of(as_of=dt("2025-02-20T00:00:00Z"), availability_basis="source")
    assert [row["payload"]["value"] for row in early] == [10]
    assert [row["payload"]["value"] for row in later] == [20]


def test_as_of_filters_market_and_kind_without_leaking_other_series(tmp_path):
    store = PointInTimeStore(tmp_path / "pit.sqlite")
    store.append(item(key="spy:1", market="global_proxy", kind="adjusted_close", value=100))
    store.append(item(key="usd:1", market="iran_candidate", kind="fx_candidate", value=500000))

    rows = store.as_of(
        as_of=dt("2025-01-04T00:00:00Z"),
        market="global_proxy",
        data_kind="adjusted_close",
    )
    assert len(rows) == 1
    assert rows[0]["record_key"] == "spy:1"


def test_unknown_availability_basis_fails_closed(tmp_path):
    store = PointInTimeStore(tmp_path / "pit.sqlite")
    with pytest.raises(ValueError, match="availability_basis"):
        store.as_of(as_of=dt("2025-01-04T00:00:00Z"), availability_basis="best_guess")


def test_published_timestamp_after_capture_is_rejected(tmp_path):
    store = PointInTimeStore(tmp_path / "pit.sqlite")
    with pytest.raises(ValueError, match="later than retrieved_at"):
        store.append(item(
            published="2025-01-05T00:00:00Z",
            retrieved="2025-01-03T00:00:00Z",
        ))


def test_naive_cutoff_is_rejected_for_both_replay_modes(tmp_path):
    store = PointInTimeStore(tmp_path / "pit.sqlite")
    naive = datetime(2025, 1, 4)
    for basis in ("captured", "source"):
        with pytest.raises(ValueError, match="timezone-aware"):
            store.as_of(as_of=naive, availability_basis=basis)


def test_source_replay_never_promotes_record_with_unknown_publication_time(tmp_path):
    store = PointInTimeStore(tmp_path / "pit.sqlite")
    store.append(item(key="news:1", kind="candidate_event", published=None))
    cutoff = dt("2025-01-04T00:00:00Z")
    assert len(store.as_of(as_of=cutoff, availability_basis="captured")) == 1
    assert store.as_of(as_of=cutoff, availability_basis="source") == []



def test_source_replay_breaks_same_publication_time_ties_by_latest_capture(tmp_path):
    store = PointInTimeStore(tmp_path / "pit.sqlite")
    store.append(item(
        key="macro:US:TEST:2025-01", value=10,
        published="2025-01-02T00:00:00Z", retrieved="2025-01-03T00:00:00Z",
    ))
    store.append(item(
        key="macro:US:TEST:2025-01", value=11,
        published="2025-01-02T00:00:00Z", retrieved="2025-01-04T00:00:00Z",
    ))

    rows = store.as_of(as_of=dt("2025-01-05T00:00:00Z"), availability_basis="source")
    assert len(rows) == 1
    assert rows[0]["payload"]["value"] == 11
