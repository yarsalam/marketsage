from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from scripts.run_staged_tsetmc_acceptance import (
    summarize_discovered_items,
    summarize_candidate_outputs,
    validate_pipeline_flags,
    SafetyGateError,
)


class StagedTsetmcRunnerTests(unittest.TestCase):
    def test_discovery_summary_deduplicates_shared_input_files(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            history = root / "history.json"
            chart = root / "chart.csv"
            crosswalk = root / "crosswalk.jsonl"
            history.write_bytes(b"history-data")
            chart.write_bytes(b"chart-data")
            crosswalk.write_bytes(b"identity")
            items = [
                {
                    "instrument_code": "1234567890",
                    "daily_history_path": str(history),
                    "adjusted_chart_path": str(chart),
                    "adjustment_events_path": "",
                    "share_change_events_path": "",
                    "identity_crosswalk_path": str(crosswalk),
                },
                {
                    "instrument_code": "1234567890",
                    "daily_history_path": str(history),
                    "adjusted_chart_path": str(chart),
                    "adjustment_events_path": "",
                    "share_change_events_path": "",
                    "identity_crosswalk_path": str(crosswalk),
                    "_discovery_ambiguous_history": True,
                    "_discovery_identity_conflict": True,
                },
            ]

            summary = summarize_discovered_items(items)

            self.assertEqual(summary["discovered_items"], 2)
            self.assertEqual(summary["unique_instrument_codes"], 1)
            self.assertEqual(summary["duplicate_instrument_codes"], 1)
            self.assertEqual(summary["unique_input_files"], 3)
            self.assertEqual(summary["existing_input_files"], 3)
            self.assertEqual(summary["selected_input_bytes"], len(b"history-datachart-dataidentity"))
            self.assertEqual(summary["missing_price_adjustment_event_count"], 2)
            self.assertEqual(summary["missing_share_change_event_count"], 2)
            self.assertEqual(summary["ambiguous_history_count"], 1)
            self.assertEqual(summary["identity_conflict_count"], 1)

    def test_candidate_output_summary_reports_only_aggregate_reason_codes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "quarantine.csv").write_text(
                """instrument_code,symbol,reason_code
private-code,private-symbol,RAW_HISTORY_STRUCTURAL_DEFECTS;USAGE_RIGHTS_NOT_VERIFIED
another-code,another-symbol,RAW_HISTORY_STRUCTURAL_DEFECTS
""",
                encoding="utf-8",
            )
            (root / "instrument_decisions.csv").write_text(
                """instrument_code,symbol,price_input_semantics,identity_verified
private-code,private-symbol,raw_unadjusted,true
another-code,another-symbol,unknown_unverified,false
third-code,third-symbol,untrusted-payload,
""",
                encoding="utf-8",
            )

            summary = summarize_candidate_outputs(root)

            self.assertEqual(summary["decision_rows"], 3)
            self.assertEqual(summary["quarantine_reason_code_counts"], {
                "RAW_HISTORY_STRUCTURAL_DEFECTS": 2,
                "USAGE_RIGHTS_NOT_VERIFIED": 1,
            })
            self.assertEqual(summary["price_input_semantics_counts"], {
                "other_or_unrecognized": 1,
                "raw_unadjusted": 1,
                "unknown_unverified": 1,
            })
            self.assertEqual(summary["identity_verified_true_count"], 1)
            self.assertEqual(summary["identity_verified_false_count"], 1)
            self.assertEqual(summary["identity_verified_unknown_count"], 1)
            self.assertNotIn("private-code", str(summary))
            self.assertNotIn("private-symbol", str(summary))

    def test_fail_closed_report_accepts_only_false_release_flags(self) -> None:
        report = {
            "mode": "local_offline_acceptance_pipeline",
            "source_id": "iran.tsetmc",
            "flags": {
                "raw_inputs_overwritten": False,
                "network_requests_made": False,
                "automatic_adjustment_applied": False,
                "forward_fill_applied": False,
                "production_scoring_enabled": False,
                "eligible_for_scoring": False,
                "adjusted_returns_approved": False,
                "eligible_for_backtest": False,
                "backtest_approved": False,
                "backtest_run": False,
            },
        }
        validate_pipeline_flags(report)

        report["flags"]["backtest_run"] = True
        with self.assertRaises(SafetyGateError):
            validate_pipeline_flags(report)

    def test_unknown_or_missing_fail_closed_flag_blocks(self) -> None:
        report = {
            "mode": "local_offline_acceptance_pipeline",
            "source_id": "iran.tsetmc",
            "flags": {"network_requests_made": False},
        }
        with self.assertRaises(SafetyGateError):
            validate_pipeline_flags(report)


if __name__ == "__main__":
    unittest.main()
