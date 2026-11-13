from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from diagnose_runner_pre_step import inspect_diagnostics


class RunnerDiagnosticClassifierTests(unittest.TestCase):
    def test_classifies_only_sanitized_categories_and_version(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            diag = Path(temp) / "_diag"
            diag.mkdir()
            (diag / "Runner_1.log").write_text(
                "Runner.Listener version: 2.338.2\n"
                "Failed to connect: connection timed out\n"
                "Permission denied while opening a local file\n"
                "Bearer super-secret-token-value\n",
                encoding="utf-8",
            )
            result = inspect_diagnostics(temp)
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["runner_version"], "2.338.2")
        self.assertEqual(result["failure_categories"]["network_connectivity"], 1)
        self.assertEqual(result["failure_categories"]["filesystem_permission"], 1)
        serialized = json.dumps(result)
        self.assertNotIn("super-secret-token-value", serialized)
        self.assertNotIn("Runner_1.log", serialized)
        self.assertNotIn(temp, serialized)

    def test_unknown_signatures_are_not_guessed(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            diag = Path(temp) / "_diag"
            diag.mkdir()
            (diag / "Worker_1.log").write_text("opaque diagnostic text", encoding="utf-8")
            result = inspect_diagnostics(temp)
        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["reason_code"], "no_known_signature_found")
        self.assertEqual(result["failure_categories"], {})

    def test_missing_diagnostic_directory_is_insufficient_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            result = inspect_diagnostics(temp)
        self.assertEqual(result["status"], "insufficient_evidence")
        self.assertEqual(result["reason_code"], "diagnostic_directory_unavailable")
        self.assertNotIn(temp, json.dumps(result))


if __name__ == "__main__":
    unittest.main()
