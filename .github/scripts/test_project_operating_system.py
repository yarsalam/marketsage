#!/usr/bin/env python3
"""Deterministic tests for the MarketSage operating-system validator."""
from __future__ import annotations

import copy
import json
import tempfile
import unittest
from pathlib import Path

from validate_project_operating_system import REQUIRED_RECORDS, validate


def fixture_records() -> dict[str, dict]:
    return {
        "work": {
            "allowed_statuses": sorted(["PROPOSED","READY","IN_PROGRESS","VALIDATION","ACCEPTED","BLOCKED","REWORK","REJECTED","STOPPED","ARCHIVED"]),
            "items": [{
                "id":"T-1","title":"Example","track":"product","owner":"test","status":"VALIDATION","timebox_hours":1,
                "objective":"Build one useful path","user_problem":"User cannot complete task",
                "deliverables":["working path"],"acceptance_criteria":["browser flow passes"],
                "stop_conditions":["stop after two failures"],"depends_on":[],"evidence_refs":[],
                "requires_user_flow_proof":True
            }]
        },
        "policy":{"project_decisions":["CONTINUE","PIVOT","HOLD","STOP","ARCHIVE"]},
        "gates":{"gates":[{"id":"G-1","name":"flow","required":True}]},
        "evidence":{"evidence":[]},
        "state":{"project_decision":"CONTINUE","product_release_status":"NOT_READY","first_user_value_flow":"NOT_YET_PROVEN","investment_outputs":"DISABLED_BY_POLICY","source_approval":"NONE"}
    }


class OperatingSystemValidatorTests(unittest.TestCase):
    def write_fixture(self, root: Path, records: dict) -> None:
        for key, rel in REQUIRED_RECORDS.items():
            path = root / rel
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(json.dumps(records[key]), encoding="utf-8")

    def run_fixture(self, records: dict) -> list[str]:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self.write_fixture(root, records)
            return validate(root)

    def test_valid_register_passes(self):
        self.assertEqual(self.run_fixture(fixture_records()), [])

    def test_unknown_dependency_fails(self):
        records = fixture_records()
        records["work"]["items"][0]["depends_on"] = ["MISSING"]
        self.assertTrue(any("unknown dependency" in error for error in self.run_fixture(records)))

    def test_dependency_cycle_fails(self):
        records = fixture_records()
        task = copy.deepcopy(records["work"]["items"][0])
        task.update({"id":"T-2","depends_on":["T-1"]})
        records["work"]["items"][0]["depends_on"] = ["T-2"]
        records["work"]["items"].append(task)
        self.assertTrue(any("dependency cycle" in error for error in self.run_fixture(records)))

    def test_accepted_user_flow_requires_user_flow_evidence(self):
        records = fixture_records()
        records["work"]["items"][0]["status"] = "ACCEPTED"
        self.assertTrue(any("without passing USER_FLOW evidence" in error for error in self.run_fixture(records)))

    def test_invalid_status_fails(self):
        records = fixture_records()
        records["work"]["items"][0]["status"] = "DONE"
        self.assertTrue(any("invalid status" in error for error in self.run_fixture(records)))


if __name__ == "__main__":
    unittest.main(verbosity=2)
