from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from audit_tsetmc_daily_history import parse_date, run_audit, summarize_field


class DailyHistoryHelpersTests(unittest.TestCase):

    def test_full_audit_keeps_rows_and_flags_duplicates_without_adjusting(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for symbol, instrument in {
                "vaghdir": "26014913469567886",
                "foolad": "46348559193224090",
                "parsian": "9481703061634967",
            }.items():
                folder = root / "data/market-research/iran-equities/adjustment-evidence" / symbol / "raw/tsetmc"
                folder.mkdir(parents=True, exist_ok=True)
                records = [
                    {"dEven": 20261103, "insCode": instrument, "pClosing": 100, "qTotTran5J": 50, "zTotTran": 10, "qTotCap": 100000000000000001},
                    {"dEven": 20261102, "insCode": instrument, "pClosing": 101, "qTotTran5J": 0, "zTotTran": 0, "qTotCap": 0},
                    {"dEven": 20261102, "insCode": instrument, "pClosing": 101, "qTotTran5J": 0, "zTotTran": 0, "qTotCap": 0},
                ]
                (folder / f"{symbol}_daily_raw.json").write_text(
                    json.dumps({"closingPriceDaily": records}), encoding="utf-8"
                )

            report = run_audit(root)
            self.assertEqual(report["summary"]["total_daily_rows"], 9)
            self.assertTrue(report["summary"]["all_daily_rows_match_primary_id"])
            self.assertEqual(report["symbols"]["vaghdir"]["duplicate_date_extra_rows"], 1)
            self.assertEqual(report["symbols"]["vaghdir"]["zero_volume_rows_qTotTran5J"], 2)
            self.assertEqual(report["symbols"]["vaghdir"]["zero_trade_count_rows_zTotTran"], 2)
            self.assertEqual(len(report["symbols"]["vaghdir"]["zero_activity_sample_records_first_20"]), 2)
            self.assertEqual(
                report["symbols"]["vaghdir"]["fields"]["qTotCap"]["max"],
                "100000000000000001"
            )
    def test_parses_gregorian_tsetmc_date(self):
        self.assertEqual(parse_date(20261103).strftime("%Y-%m-%d"), "2026-11-03")

    def test_summarizes_missing_zero_and_numeric_values(self):
        summary = summarize_field(
            [{"pClosing": 100}, {"pClosing": 0}, {"pClosing": None}, {"pClosing": "bad"}],
            "pClosing"
        )
        self.assertEqual(summary["present"], 3)
        self.assertEqual(summary["missing"], 1)
        self.assertEqual(summary["zero"], 1)
        self.assertEqual(summary["invalid_numeric"], 1)
        self.assertEqual(summary["min"], "0")
        self.assertEqual(summary["max"], "100")

    def test_large_integer_values_keep_decimal_precision(self):
        summary = summarize_field(
            [{"qTotCap": 987654321012345678}, {"qTotCap": 987654321012345679}],
            "qTotCap"
        )
        self.assertEqual(summary["min"], "987654321012345678")
        self.assertEqual(summary["max"], "987654321012345679")


if __name__ == "__main__":
    unittest.main()
