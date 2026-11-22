import hashlib
import sqlite3
from datetime import datetime, timezone

import pytest

from audit_temporal_price_basis import audit_database
from temporal_data import PointInTimeStore, TemporalRecord


def _record(store, *, key, kind, symbol, **overrides):
    payload = {
        "symbol": symbol,
        "canonical_instrument_id": overrides.pop("canonical_instrument_id", None),
        "currency": overrides.pop("currency", "USD"),
        "price_unit": overrides.pop("price_unit", "usd_per_share"),
        "price_basis": overrides.pop("price_basis", kind),
        "adjustment_policy": overrides.pop("adjustment_policy", "yfinance_auto_adjust_true_close"),
        "close": 123456.78,
    }
    payload.update(overrides)
    now = datetime(2026, 11, 9, 12, tzinfo=timezone.utc)
    return store.append(TemporalRecord(
        record_key=key,
        source_id="global.yahoo_finance.yfinance",
        market="global_proxy",
        data_kind=kind,
        observed_at=now,
        retrieved_at=now,
        payload=payload,
    ))


def test_audit_reports_only_aggregate_counts_and_does_not_mutate(tmp_path):
    database = tmp_path / "temporal.sqlite3"
    store = PointInTimeStore(database)
    _record(
        store,
        key="SPY:2026-11-08",
        kind="adjusted_close",
        symbol="SPY",
        canonical_instrument_id="global.proxy.etf.sp500",
    )
    _record(
        store,
        key="BTC-USD:2026-11-08",
        kind="adjusted_close",
        symbol="BTC-USD",
        canonical_instrument_id="global.proxy.crypto.bitcoin",
        price_unit="adjusted_close_usd_per_unit",
    )
    _record(
        store,
        key="UNKNOWN:2026-11-08",
        kind="adjusted_close",
        symbol="UNKNOWN",
    )
    store._anchor.close() if store._anchor else None

    before = hashlib.sha256(database.read_bytes()).hexdigest()
    report = audit_database(database)
    after = hashlib.sha256(database.read_bytes()).hexdigest()

    assert before == after
    assert report["status"] == "review_required"
    assert report["read_only"] is True
    assert report["mutations_performed"] == 0
    assert report["raw_values_emitted"] is False
    assert report["counts"] == {
        "audited_records": 3,
        "consistent_records": 1,
        "legacy_mismatch_records": 1,
        "unmapped_records": 1,
        "invalid_metadata_records": 0,
    }
    serialized = str(report)
    assert "123456.78" not in serialized
    assert "BTC-USD" not in serialized
    assert "SPY" not in serialized


def test_audit_handles_empty_database_without_claiming_validation(tmp_path):
    database = tmp_path / "empty.sqlite3"
    PointInTimeStore(database)
    report = audit_database(database)

    assert report["status"] == "no_records"
    assert report["counts"]["audited_records"] == 0
    assert report["mutations_performed"] == 0


def test_audit_rejects_missing_database_without_echoing_path(tmp_path):
    missing = tmp_path / "private" / "not-created.sqlite3"
    with pytest.raises(FileNotFoundError, match="database file"):
        audit_database(missing)


def test_audit_rejects_non_market_database_schema(tmp_path):
    database = tmp_path / "other.sqlite3"
    with sqlite3.connect(database) as connection:
        connection.execute("CREATE TABLE unrelated (id INTEGER PRIMARY KEY)")

    with pytest.raises(RuntimeError, match="temporal record table"):
        audit_database(database)
