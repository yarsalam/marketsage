from __future__ import annotations

import csv
import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from scripts.diagnose_tsetmc_input_errors import (
    DiagnosticError,
    classify_error,
    summarize,
)


class TsetmcSanitizedDiagnosticsTests(unittest.TestCase):
    def _make_run(self, root: Path, run_name: str, rows: list[dict[str, str]]) -> None:
        run_dir = root / run_name
        run_dir.mkdir()
        inventory = run_dir / "input_inventory.csv"
        with inventory.open("w", encoding="utf-8", newline="") as stream:
            writer = csv.DictWriter(
                stream,
                fieldnames=["instrument_code", "symbol", "input_kind", "path", "sha256", "status", "error"],
            )
            writer.writeheader()
            writer.writerows(rows)
        digest = hashlib.sha256(inventory.read_bytes()).hexdigest()
        (run_dir / "run_manifest.json").write_text(json.dumps({
            "output_files": ["input_inventory.csv"],
            "output_hashes_sha256": {"input_inventory.csv": digest},
        }), encoding="utf-8")

    def test_error_classifier_uses_closed_safe_categories(self) -> None:
        self.assertEqual(classify_error("private.csv (UnicodeDecodeError)"), "ENCODING_ERROR")
        self.assertEqual(classify_error("private.json (JSONDecodeError)"), "MALFORMED_JSON")
        self.assertEqual(classify_error("input file not found: /private/path"), "MISSING_FILE")
        self.assertEqual(classify_error("unrecognized private exception"), "OTHER_READ_ERROR")

    def test_summary_contains_only_aggregate_counts(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._make_run(root, "run_1", [
                {
                    "instrument_code": "SECRET_CODE",
                    "symbol": "SECRET_SYMBOL",
                    "input_kind": "daily_history_path",
                    "path": "/private/raw.csv",
                    "sha256": "",
                    "status": "error",
                    "error": "private.csv (UnicodeDecodeError)",
                },
                {
                    "instrument_code": "SECRET_CODE",
                    "symbol": "SECRET_SYMBOL",
                    "input_kind": "adjusted_chart_path",
                    "path": "/private/chart.json",
                    "sha256": "",
                    "status": "error",
                    "error": "private.json (JSONDecodeError)",
                },
            ])
            result = summarize(root)
            rendered = json.dumps(result)
            self.assertEqual(result["input_error_count"], 2)
            self.assertEqual(result["error_category_counts"], {
                "ENCODING_ERROR": 1,
                "MALFORMED_JSON": 1,
            })
            for secret in ("SECRET_CODE", "SECRET_SYMBOL", "/private", "private.csv"):
                self.assertNotIn(secret, rendered)
            self.assertFalse(result["raw_rows_emitted"])
            self.assertFalse(result["paths_emitted"])

    def test_manifest_hash_mismatch_fails_closed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            self._make_run(root, "run_1", [])
            manifest = root / "run_1" / "run_manifest.json"
            data = json.loads(manifest.read_text())
            data["output_hashes_sha256"]["input_inventory.csv"] = "0" * 64
            manifest.write_text(json.dumps(data))
            with self.assertRaises(DiagnosticError) as caught:
                summarize(root)
            self.assertEqual(str(caught.exception), "inventory_hash_mismatch")

    def test_missing_run_blocks(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            with self.assertRaises(DiagnosticError) as caught:
                summarize(Path(tmp))
            self.assertEqual(str(caught.exception), "no_pipeline_runs_found")


if __name__ == "__main__":
    unittest.main()
