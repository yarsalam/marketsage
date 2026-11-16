from __future__ import annotations

import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from infra.control_plane.preflight_cli import main


class PreflightCliTests(unittest.TestCase):
    def _root(self, root: Path) -> None:
        governance = root / "docs" / "governance"
        (governance / "work_items").mkdir(parents=True)
        work_id = "MS-20261116-CONTINUITY-001"
        (governance / "execution_policy.json").write_text(json.dumps({
            "schema_version": 1, "project": "MarketSage",
            "scope_lock": "INFRA_ONLY", "research_locked": True,
            "allowed_actions": ["infrastructure", "governance", "synthetic_test"],
            "authorized_work_ids": [work_id],
        }), encoding="utf-8")
        (governance / "work_items" / f"{work_id}.json").write_text(json.dumps({
            "work_id": work_id, "status": "IN_PROGRESS",
            "allowed_actions": ["synthetic_test"],
        }), encoding="utf-8")
        (governance / "ARTIFACT_REGISTRY.jsonl").write_text("", encoding="utf-8")
        (governance / "RUN_LEDGER.jsonl").write_text("", encoding="utf-8")

    def test_research_entrypoint_is_blocked_by_infra_only_scope(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self._root(root)
            stderr = io.StringIO()
            with patch("sys.argv", ["preflight", "--action", "research", "--root", str(root),
                                    "--code-sha", "a" * 40, "--run-id", "123"]):
                with contextlib.redirect_stderr(stderr):
                    result = main()
            self.assertEqual(result, 2)
            self.assertIn("reason=project_scope_locked", stderr.getvalue())

    def test_unlocked_policy_still_blocks_research_without_manifest_and_durable_ledger(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self._root(root)
            governance = root / "docs" / "governance"
            work_id = "MS-20261116-CONTINUITY-001"
            policy_path = governance / "execution_policy.json"
            policy = json.loads(policy_path.read_text(encoding="utf-8"))
            policy.update({
                "scope_lock": "OPEN",
                "research_locked": False,
                "allowed_actions": ["infrastructure", "governance", "synthetic_test", "research"],
            })
            policy_path.write_text(json.dumps(policy), encoding="utf-8")
            work_path = governance / "work_items" / f"{work_id}.json"
            work = json.loads(work_path.read_text(encoding="utf-8"))
            work["allowed_actions"] = ["synthetic_test", "research"]
            work_path.write_text(json.dumps(work), encoding="utf-8")

            stderr = io.StringIO()
            with patch("sys.argv", ["preflight", "--action", "research", "--root", str(root),
                                    "--code-sha", "a" * 40, "--run-id", "open-456"]):
                with contextlib.redirect_stderr(stderr):
                    result = main()
            self.assertEqual(result, 2)
            self.assertIn(
                "reason=research_cli_manifest_and_ledger_integration_missing",
                stderr.getvalue(),
            )

    def test_active_infrastructure_work_passes_without_side_effects(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self._root(root)
            stdout = io.StringIO()
            with patch("sys.argv", ["preflight", "--action", "synthetic_test", "--root", str(root),
                                    "--code-sha", "a" * 40, "--run-id", "123"]):
                with contextlib.redirect_stdout(stdout):
                    result = main()
            self.assertEqual(result, 0)
            self.assertIn("MARKETSAGE_PREFLIGHT=PASS_NO_SIDE_EFFECTS", stdout.getvalue())


if __name__ == "__main__":
    unittest.main()
