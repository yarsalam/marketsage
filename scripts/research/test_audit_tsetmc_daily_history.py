from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from audit_tsetmc_daily_history import parse_date, run_audit, summarize_field


class DailyHistoryHelpersTests(unittest.TestCase):
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
