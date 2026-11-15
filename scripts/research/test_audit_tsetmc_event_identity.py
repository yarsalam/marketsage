from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from audit_tsetmc_event_identity import audit_symbol, feed_summary, norm


class FeedSummaryTests(unittest.TestCase):
    def test_exact_primary_id_is_matched(self):
        result = feed_summary([{"insCode": "111"}], "111", {"insCode2": "222"})
        self.assertEqual(result["status"], "matched_primary")
        self.assertEqual(result["matched_primary_rows"], 1)
        self.assertFalse(result["related_ids_used_as_aliases"])

    def test_unlisted_related_id_remains_unresolved(self):
        result = feed_summary([{"insCode": "333"}], "111", {"insCode2": "222"})
        self.assertEqual(result["status"], "unresolved_identifier_mismatch")
        self.assertEqual(result["unresolved_identifier_rows"], 1)
        self.assertEqual(result["related_field_match_counts_unverified"]["insCode2"], 0)

    def test_related_id_is_reported_but_not_accepted(self):
        result = feed_summary([{"insCode": "222"}], "111", {"insCode2": "222"})
        self.assertEqual(result["status"], "unresolved_identifier_mismatch")
        self.assertEqual(result["related_field_match_counts_unverified"]["insCode2"], 1)
        self.assertFalse(result["related_ids_used_as_aliases"])

    def test_python_json_preserves_large_inscode_integer(self):
        parsed = json.loads('{"insCode": 9481703061634967}')
        self.assertIsInstance(parsed["insCode"], int)
        self.assertEqual(norm(parsed["insCode"]), "9481703061634967")

    def test_float_inscode_is_rejected_as_potentially_lossy(self):
        with self.assertRaisesRegex(ValueError, "decoded as float"):
            norm(9481703061634968.0)


class InstrumentAuditTests(unittest.TestCase):
    def write_json(self, path: Path, value):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(value, ensure_ascii=False), encoding="utf-8")

    def test_audits_exact_primary_and_separates_feed_id_mismatch(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            base = root / "data/market-research/iran-equities/adjustment-evidence/vaghdir"
            identity = {
                "primary_insCode": "26014913469567886",
                "exact_ticker_record": {
                    "insCode": "26014913469567886",
                    "insCode2": "49373621277888271",
                    "insCode3": "48925462829697327",
                    "insCode4": "7173358342361500",
                    "lVal18AFC": "وغدیر"
                }
            }
            self.write_json(base / "identity.json", identity)
            self.write_json(base / "raw/tsetmc/vaghdir_instrument_search.json", {
                "instrumentSearch": [identity["exact_ticker_record"]]
            })
            self.write_json(base / "raw/tsetmc/vaghdir_price_adjust_raw.json", {
                "priceAdjust": [{"insCode": "26014913469567890", "dEven": 20260418}]
            })
            self.write_json(base / "raw/tsetmc/vaghdir_share_change_raw.json", {
                "instrumentShareChange": [{"insCode": "26014913469567886", "dEven": 20240803}]
            })

            result = audit_symbol(root, "vaghdir")
            self.assertEqual(result["price_adjust"]["status"], "unresolved_identifier_mismatch")
            self.assertEqual(result["share_change"]["status"], "matched_primary")
            self.assertEqual(result["overall_status"], "requires_identity_research")
            self.assertFalse(result["price_adjust"]["related_ids_used_as_aliases"])


if __name__ == "__main__":
    unittest.main()
