import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from marketsage_pipeline import (
    AdjustmentAssessment,
    AdjustmentState,
    Asset,
    BatchEngine,
    NormalizedData,
    RawPayload,
    Status,
)


class FakeAdapter:
    def __init__(self, state=AdjustmentState.UNADJUSTED_CONFIRMED,
                 events=None, coverage=True, fail_fetch=False, validation=None):
        self.state = state
        self.events = events or []
        self.coverage = coverage
        self.fail_fetch = fail_fetch
        self.validation = validation or []
        self.fetch_count = 0
        self.adjust_count = 0

    def request_fingerprint(self, asset):
        data = f"{asset.source_id}:{asset.asset_id}:{asset.source_symbol}"
        return hashlib.sha256(data.encode()).hexdigest()

    def fetch_history(self, asset):
        self.fetch_count += 1
        if self.fail_fetch:
            raise OSError("simulated source outage")
        return RawPayload(b"synthetic-raw-v1", {"fixture": True})

    def normalize(self, asset, payload):
        return NormalizedData(
            rows=[{"date": "2026-01-01", "open": 10, "high": 12,
                   "low": 9, "close": 11, "volume": 100}],
            schema={"date": "date", "close": "integer"},
        )

    def assess_adjustment(self, asset, payload, data):
        return AdjustmentAssessment(
            state=self.state,
            evidence=["synthetic fixture evidence"],
            event_coverage_complete=self.coverage,
            adjustment_type="price",
        )

    def fetch_events(self, asset):
        return list(self.events)

    def apply_adjustment(self, asset, data, events):
        self.adjust_count += 1
        return NormalizedData(
            rows=[{**data.rows[0], "close": 10.5}],
            schema=data.schema,
        )

    def validate(self, asset, data):
        return list(self.validation)


class BatchEngineTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)

    def tearDown(self):
        self.temp.cleanup()

    def asset(self, asset_id="TEST-1", source_id="fake"):
        return Asset(asset_id, "equity", source_id, "TEST")

    def test_partial_failure_does_not_stop_other_assets(self):
        bad = FakeAdapter(fail_fetch=True)
        good = FakeAdapter(
            state=AdjustmentState.VENDOR_ADJUSTED_CONFIRMED
        )
        engine = BatchEngine(self.root, {"bad": bad, "good": good}, max_workers=2)
        report = engine.run(
            [self.asset("A", "bad"), self.asset("B", "good")], "run-partial"
        )
        statuses = {item["asset_id"]: item["status"] for item in report["results"]}
        self.assertEqual(statuses["A"], Status.SOURCE_FAILED.value)
        self.assertEqual(statuses["B"], Status.ADJUSTMENT_NOT_REQUIRED.value)

    def test_raw_cache_prevents_duplicate_acquisition(self):
        adapter = FakeAdapter(
            state=AdjustmentState.VENDOR_ADJUSTED_CONFIRMED
        )
        engine = BatchEngine(self.root, {"fake": adapter})
        first = engine.run([self.asset()], "run-one")
        second = engine.run([self.asset()], "run-two")
        self.assertEqual(adapter.fetch_count, 1)
        self.assertFalse(first["results"][0]["reused_raw"])
        self.assertTrue(second["results"][0]["reused_raw"])

    def test_unknown_adjustment_goes_to_review_queue(self):
        adapter = FakeAdapter(state=AdjustmentState.UNKNOWN)
        report = BatchEngine(self.root, {"fake": adapter}).run(
            [self.asset()], "run-unknown"
        )
        item = report["results"][0]
        self.assertEqual(item["status"], Status.REVIEW_REQUIRED.value)
        self.assertEqual(adapter.adjust_count, 0)

    def test_incomplete_event_coverage_blocks_adjustment(self):
        adapter = FakeAdapter(
            state=AdjustmentState.UNADJUSTED_CONFIRMED,
            events=[{"type": "cash_dividend", "effective_date": "2026-01-01"}],
            coverage=False,
        )
        report = BatchEngine(self.root, {"fake": adapter}).run(
            [self.asset()], "run-incomplete-events"
        )
        self.assertEqual(
            report["results"][0]["status"], Status.REVIEW_REQUIRED.value
        )
        self.assertEqual(adapter.adjust_count, 0)

    def test_complete_events_are_adjusted_and_verified(self):
        adapter = FakeAdapter(
            state=AdjustmentState.UNADJUSTED_CONFIRMED,
            events=[{"type": "cash_dividend", "effective_date": "2026-01-01"}],
            coverage=True,
        )
        report = BatchEngine(self.root, {"fake": adapter}).run(
            [self.asset()], "run-adjust"
        )
        item = report["results"][0]
        self.assertEqual(item["status"], Status.ADJUSTED_VERIFIED.value)
        self.assertTrue(item["adjusted_sha256"])
        self.assertEqual(adapter.adjust_count, 1)

    def test_empty_events_only_pass_when_coverage_is_complete(self):
        adapter = FakeAdapter(
            state=AdjustmentState.UNADJUSTED_CONFIRMED,
            events=[],
            coverage=True,
        )
        report = BatchEngine(self.root, {"fake": adapter}).run(
            [self.asset()], "run-no-events"
        )
        self.assertEqual(
            report["results"][0]["status"],
            Status.ADJUSTMENT_NOT_REQUIRED.value,
        )

    def test_validation_failure_is_not_accepted(self):
        adapter = FakeAdapter(
            state=AdjustmentState.VENDOR_ADJUSTED_CONFIRMED,
            validation=["OHLC invariant failed"],
        )
        report = BatchEngine(self.root, {"fake": adapter}).run(
            [self.asset()], "run-invalid"
        )
        self.assertEqual(
            report["results"][0]["status"], Status.VALIDATION_FAILED.value
        )

    def test_raw_files_are_content_addressed_and_immutable(self):
        adapter = FakeAdapter(
            state=AdjustmentState.VENDOR_ADJUSTED_CONFIRMED
        )
        BatchEngine(self.root, {"fake": adapter}).run(
            [self.asset()], "run-immutable"
        )
        raw_files = list((self.root / "raw").rglob("*.bin"))
        self.assertEqual(len(raw_files), 1)
        self.assertEqual(raw_files[0].read_bytes(), b"synthetic-raw-v1")


if __name__ == "__main__":
    unittest.main()
